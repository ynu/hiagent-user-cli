"""用户组同步引擎 - 规则加载、增量计算、执行"""

import importlib.util
from pathlib import Path
from typing import Any, Callable


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
