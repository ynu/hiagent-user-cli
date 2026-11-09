"""用户组同步引擎 - 规则加载、增量计算、执行"""

import importlib.util
from pathlib import Path
from typing import Any, Callable

from ..api.client import APIClient, APIError
from ..api.group import GroupAPI
from ..api.user import ListUserAPI


class RulesError(ValueError):
    """规则脚本错误"""


def load_rules(path: str | Path) -> dict[str, Any]:
    """加载规则脚本

    脚本必须定义 apply(user) -> str | list[str] | None；
    可选定义 MUTEX_GROUPS: list[list[str]]。

    Returns:
        {"apply": callable, "MUTEX_GROUPS": list[list[str]]}
    """
    path = Path(path)
    if not path.exists():
        raise RulesError(f"规则脚本不存在: {path}")

    try:
        spec = importlib.util.spec_from_file_location("hiagent_sync_rules", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        raise RulesError(f"加载规则脚本失败: {path} - {e}") from e

    apply_fn = getattr(module, "apply", None)
    if not callable(apply_fn):
        raise RulesError(f"规则脚本缺少 apply(user) 函数: {path}")

    mutex_groups = getattr(module, "MUTEX_GROUPS", []) or []
    if not isinstance(mutex_groups, list) or not all(
        isinstance(mset, list) and all(isinstance(g, str) for g in mset)
        for mset in mutex_groups
    ):
        raise RulesError("MUTEX_GROUPS 必须是 [[组名, ...], ...] 形式")

    return {
        "apply": apply_fn,
        "MUTEX_GROUPS": list(mutex_groups),
    }


def resolve_mutex(target_groups: list[str], mutex_groups: list[list[str]]) -> list[str]:
    """互斥仲裁：用户目标组与互斥集合交集多于一个时，按集合声明顺序保留第一个"""
    resolved = list(target_groups)
    for mutex_set in mutex_groups:
        hits = [g for g in mutex_set if g in resolved]
        if len(hits) > 1:
            keep = hits[0]
            resolved = [g for g in resolved if g not in mutex_set or g == keep]
    return resolved


def compute_changes(
    users: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    group_members: dict[str, list[dict[str, Any]]],
    rules: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """计算组变更（纯函数）

    Args:
        users: 平台全部用户（含 ID 字段）
        groups: 平台全部组（含 ID/GroupName）
        group_members: {组 ID: 成员列表}，仅规则引用的组
        rules: load_rules() 结果

    Returns:
        {组名: {"group_id": 组ID, "add": [用户ID...], "remove": [用户ID...]}}
        仅包含有变更的组。
    """
    apply_fn: Callable = rules["apply"]
    mutex_groups = rules["MUTEX_GROUPS"]

    name_to_id = {g.get("GroupName", ""): g.get("ID", "") for g in groups}

    # 规则引用的组 = 互斥声明中出现的组 + apply 实际返回的组
    referenced = {g for mset in mutex_groups for g in mset}

    # 目标组: {用户 ID: [组名...]}
    desired: dict[str, list[str]] = {}
    returned_groups: set[str] = set()

    for user in users:
        user_id = user.get("ID", "")
        if not user_id:
            continue
        try:
            result = apply_fn(user)
        except Exception as e:
            raise RulesError(f"apply() 处理用户 {user.get('UserName', user_id)} 失败: {e}") from e

        if result is None:
            target = []
        elif isinstance(result, str):
            target = [result]
        elif isinstance(result, list):
            target = [g for g in result if isinstance(g, str)]
        else:
            target = []

        target = resolve_mutex(target, mutex_groups)
        returned_groups.update(target)
        desired[user_id] = target

    referenced.update(returned_groups)

    # 校验引用的组都存在
    missing = [g for g in referenced if g not in name_to_id]
    if missing:
        raise RulesError(f"规则引用的组在平台中不存在: {', '.join(missing)}")

    # 现有成员: {组 ID: {用户 ID...}}
    current: dict[str, set[str]] = {
        gid: {m.get("IdentityID", "") for m in group_members.get(gid, []) if m.get("IdentityID")}
        for gid in {name_to_id[g] for g in referenced}
    }

    changes: dict[str, dict[str, Any]] = {}
    for group_name in sorted(referenced):
        gid = name_to_id[group_name]
        existing = current[gid]
        wanted = {uid for uid, names in desired.items() if group_name in names}
        add = sorted(wanted - existing)
        remove = sorted(existing - wanted)
        if add or remove:
            changes[group_name] = {"group_id": gid, "add": add, "remove": remove}

    return changes


class GroupSyncEngine:
    """用户组同步引擎：拉取数据 → 计算变更 → 执行/预览"""

    def __init__(self, client: APIClient, rules_path: str | Path, page_size: int = 10000):
        self.client = client
        self.rules_path = Path(rules_path)
        self.page_size = page_size
        self.rules = load_rules(self.rules_path)

    def fetch_changes(self) -> dict[str, dict[str, Any]]:
        """拉取平台数据并计算变更

        注意：规则脚本 apply 必须是确定性纯函数（两次计算需一致）。
        """
        group_api = GroupAPI(self.client)
        user_api = ListUserAPI(self.client)

        groups, _ = group_api.list_groups(page_size=self.page_size)
        users, _ = user_api.list_users(include_visitor=True, page_size=self.page_size)

        # 空用户列表多半是 API 异常：desired 全空会把引用组的成员全部判为待移除，
        # 为防止误删全部组成员，此处直接中止
        if not users:
            raise RulesError(
                "未获取到任何平台用户（可能是 API 异常），为防止误删全部组成员，已中止同步。"
            )

        name_to_id = {g.get("GroupName", ""): g.get("ID", "") for g in groups}

        # 先用空成员算一遍拿到 apply 实际返回的组集合（compute_changes 是纯函数，代价低），
        # 据此决定要拉哪些组的成员
        changes = compute_changes(users, groups, {}, self.rules)

        referenced = set(changes.keys()) | {g for mset in self.rules["MUTEX_GROUPS"] for g in mset}
        group_members: dict[str, list[dict[str, Any]]] = {}
        for name in referenced:
            gid = name_to_id.get(name)
            if not gid:
                continue
            members, _ = group_api.list_group_members(gid, page_size=self.page_size)
            group_members[gid] = members

        # 用真实成员重算（现有成员数据到位后增量才准确）
        return compute_changes(users, groups, group_members, self.rules)

    def run(self, dry_run: bool = False) -> dict[str, Any]:
        """执行同步；dry_run=True 时只返回变更不调用写接口

        注意：success/failure 按写操作批次计数（一次批量添加计 1）。

        Returns:
            {"changes": 变更表, "dry_run": bool, "applied": bool,
             "success": int, "failure": int, "errors": [str...]}
        """
        changes = self.fetch_changes()

        if dry_run:
            return {"changes": changes, "dry_run": True, "applied": False,
                    "success": 0, "failure": 0, "errors": []}

        group_api = GroupAPI(self.client)

        success = 0
        failure = 0
        errors: list[str] = []

        for group_name, change in changes.items():
            gid = change["group_id"]
            if change["add"]:
                try:
                    group_api.add_members(gid, change["add"])
                    success += 1
                except APIError as e:
                    failure += 1
                    errors.append(f"添加到 {group_name} 失败: {e}")
            if change["remove"]:
                try:
                    group_api.remove_members(gid, change["remove"])
                    success += 1
                except APIError as e:
                    failure += 1
                    errors.append(f"从 {group_name} 移除失败: {e}")

        return {"changes": changes, "dry_run": False, "applied": True,
                "success": success, "failure": failure, "errors": errors}
