# 用户组同步（sync-groups）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过 Python 规则脚本定义用户→组映射，以增量方式同步组成员（添加缺失 + 移除不匹配），支持 dry run 与互斥组。

**Architecture:** 遵循现有分层（api → core → cli）：`GroupAPI` 封装 4 个 iam 接口；`GroupSyncEngine` 负责规则加载、增量计算（纯逻辑可测）与执行；`sync-groups` Click 命令串联。规则脚本定义 `apply(user)` 与可选 `MUTEX_GROUPS`。

**Tech Stack:** Click, requests, Rich, pytest（现有依赖，无新增）

**Spec:** `docs/superpowers/specs/2026-11-09-group-sync-design.md`

---

## 文件结构

- Create: `src/inactive_user_cli/api/group.py` — 4 个组管理接口封装
- Create: `src/inactive_user_cli/core/group_sync.py` — 规则加载 + 增量计算 + 执行引擎
- Create: `src/inactive_user_cli/core/rules_example.py.example` — 规则脚本示例（不参与打包执行，供用户复制）
- Modify: `src/inactive_user_cli/cli.py` — 新增 `sync-groups` 命令
- Modify: `src/inactive_user_cli/logger.py` — 新增 `print_sync_tables` 输出方法
- Test: `tests/test_group_api.py`, `tests/test_group_sync.py`, `tests/test_cli_sync.py`

---

### Task 1: GroupAPI

**Files:**
- Create: `src/inactive_user_cli/api/group.py`
- Test: `tests/test_group_api.py`

- [ ] **Step 1: 写失败测试**

```python
"""GroupAPI 测试"""

import pytest
from unittest.mock import Mock

from inactive_user_cli.api.group import GroupAPI
from inactive_user_cli.api.client import APIClient
from inactive_user_cli.config import APIConfig


@pytest.fixture
def mock_client():
    config = APIConfig(
        host="10.10.160.222:30040/",
        version="2023-08-01",
        service="app",
        region="cn-north-1",
        account_id="1000000000",
        ak="test_ak",
        sk="test_sk",
    )
    client = APIClient(config)
    client.request = Mock()
    client.paginated_request = Mock()
    return client


@pytest.fixture
def group_api(mock_client):
    return GroupAPI(mock_client)


class TestGroupAPI:
    def test_list_groups(self, group_api, mock_client):
        """list_groups 调用 ListUserGroup 分页接口"""
        mock_client.paginated_request.return_value = (
            [{"ID": "g1", "GroupName": "教师组"}], 1,
        )
        groups, total = group_api.list_groups()
        assert groups == [{"ID": "g1", "GroupName": "教师组"}]
        assert total == 1
        args, kwargs = mock_client.paginated_request.call_args
        assert kwargs["action"] == "ListUserGroup"
        assert kwargs["service"] == "iam"
        assert kwargs["version"] == "2024-12-25"
        assert kwargs["data"]["ListOpt"]["PageNumber"] == 1

    def test_list_group_members(self, group_api, mock_client):
        """list_group_members 传 GroupID 调用 ListGroupMember"""
        mock_client.paginated_request.return_value = (
            [{"ID": "m1", "IdentityID": "u1", "Name": "20220178",
              "DisplayName": "张守栋", "Type": 2}], 1,
        )
        members, total = group_api.list_group_members("g1")
        assert members[0]["IdentityID"] == "u1"
        args, kwargs = mock_client.paginated_request.call_args
        assert kwargs["action"] == "ListGroupMember"
        assert kwargs["data"]["GroupID"] == "g1"

    def test_add_members(self, group_api, mock_client):
        """add_members 调用 CreateGroupMember"""
        mock_client.request.return_value = {"Result": {}}
        assert group_api.add_members("g1", ["u1", "u2"]) is True
        args, _ = mock_client.request.call_args
        assert args[0] == "CreateGroupMember"
        assert args[1] == {"GroupID": "g1", "UserIDs": ["u1", "u2"], "OrgIDs": []}

    def test_remove_members(self, group_api, mock_client):
        """remove_members 调用 RemoveGroupMember"""
        mock_client.request.return_value = {"Result": {}}
        assert group_api.remove_members("g1", ["u1"]) is True
        args, _ = mock_client.request.call_args
        assert args[0] == "RemoveGroupMember"
        assert args[1] == {"GroupID": "g1", "UserIDs": ["u1"], "OrgIDs": []}
```

- [ ] **Step 2: 运行确认失败**

Run: `uv run pytest tests/test_group_api.py -v`
Expected: FAIL — `ModuleNotFoundError: inactive_user_cli.api.group`

- [ ] **Step 3: 实现 GroupAPI**

`src/inactive_user_cli/api/group.py`:

```python
"""用户组管理接口 - ListUserGroup / ListGroupMember / CreateGroupMember / RemoveGroupMember"""

from typing import Any

from .client import APIClient


class GroupAPI:
    """用户组管理接口封装"""

    ACTION_LIST_GROUPS = "ListUserGroup"
    ACTION_LIST_MEMBERS = "ListGroupMember"
    ACTION_ADD_MEMBERS = "CreateGroupMember"
    ACTION_REMOVE_MEMBERS = "RemoveGroupMember"
    SERVICE = "iam"
    VERSION = "2024-12-25"

    def __init__(self, client: APIClient):
        self.client = client

    def list_groups(self, page_size: int = 10000) -> tuple[list[dict[str, Any]], int]:
        """获取所有用户组

        Returns:
            (groups, total): 组列表（含 ID/GroupName）和总数
        """
        data: dict[str, Any] = {"ListOpt": {"PageNumber": 1, "PageSize": page_size}}
        return self.client.paginated_request(
            action=self.ACTION_LIST_GROUPS,
            data=data,
            page_field="PageNumber",
            size_field="PageSize",
            items_field="Items",
            total_field="Total",
            page_size=page_size,
            service=self.SERVICE,
            version=self.VERSION,
        )

    def list_group_members(
        self, group_id: str, page_size: int = 10000
    ) -> tuple[list[dict[str, Any]], int]:
        """获取组成员列表

        Returns:
            (members, total): 成员列表（IdentityID 为用户 ID）和总数
        """
        data: dict[str, Any] = {"GroupID": group_id, "ListOpt": {"PageNumber": 1, "PageSize": page_size}}
        return self.client.paginated_request(
            action=self.ACTION_LIST_MEMBERS,
            data=data,
            page_field="PageNumber",
            size_field="PageSize",
            items_field="Items",
            total_field="Total",
            page_size=page_size,
            service=self.SERVICE,
            version=self.VERSION,
        )

    def add_members(self, group_id: str, user_ids: list[str]) -> bool:
        """批量添加组成员（CreateGroupMember）"""
        self.client.request(
            self.ACTION_ADD_MEMBERS,
            {"GroupID": group_id, "UserIDs": user_ids, "OrgIDs": []},
            service=self.SERVICE,
            version=self.VERSION,
        )
        return True

    def remove_members(self, group_id: str, user_ids: list[str]) -> bool:
        """批量移除组成员（RemoveGroupMember）"""
        self.client.request(
            self.ACTION_REMOVE_MEMBERS,
            {"GroupID": group_id, "UserIDs": user_ids, "OrgIDs": []},
            service=self.SERVICE,
            version=self.VERSION,
        )
        return True
```

- [ ] **Step 4: 运行确认通过**

Run: `uv run pytest tests/test_group_api.py -v`
Expected: 4 PASS

- [ ] **Step 5: 提交**

```bash
git add src/inactive_user_cli/api/group.py tests/test_group_api.py
git commit -m "feat: add GroupAPI for group member management"
```

---

### Task 2: 规则加载 + 增量计算（compute_changes）

**Files:**
- Create: `src/inactive_user_cli/core/group_sync.py`
- Test: `tests/test_group_sync.py`

- [ ] **Step 1: 写失败测试**

```python
"""GroupSyncEngine 测试"""

import textwrap

import pytest

from inactive_user_cli.core.group_sync import load_rules, compute_changes


RULES_OK = textwrap.dedent("""
    import re
    MUTEX_GROUPS = [["学生组", "教师组"]]
    def apply(user):
        if re.fullmatch(r"\\d{8}", user.get("UserName", "")):
            return "教师组"
        return "学生组"
""")

RULES_NO_APPLY = "x = 1\n"
RULES_SYNTAX_ERROR = "def apply(:\n"


@pytest.fixture
def rules_file(tmp_path):
    path = tmp_path / "rules.py"
    path.write_text(RULES_OK, encoding="utf-8")
    return path


class TestLoadRules:
    def test_load_ok(self, rules_file):
        rules = load_rules(rules_file)
        assert rules["MUTEX_GROUPS"] == [["学生组", "教师组"]]
        assert callable(rules["apply"])

    def test_missing_apply(self, tmp_path):
        path = tmp_path / "bad.py"
        path.write_text(RULES_NO_APPLY, encoding="utf-8")
        with pytest.raises(ValueError, match="apply"):
            load_rules(path)

    def test_syntax_error(self, tmp_path):
        path = tmp_path / "bad.py"
        path.write_text(RULES_SYNTAX_ERROR, encoding="utf-8")
        with pytest.raises(ValueError, match="加载规则脚本失败"):
            load_rules(path)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(ValueError, match="不存在"):
            load_rules(tmp_path / "nope.py")


class TestComputeChanges:
    """compute_changes(users, groups, group_members, rules) -> changes"""

    @pytest.fixture
    def groups(self):
        return [
            {"ID": "g_t", "GroupName": "教师组"},
            {"ID": "g_s", "GroupName": "学生组"},
            {"ID": "g_v", "GroupName": "访客组"},  # 规则未声明
        ]

    @pytest.fixture
    def users(self):
        return [
            {"ID": "u1", "UserName": "20220178", "DisplayName": "张老师"},
            {"ID": "u2", "UserName": "20220179", "DisplayName": "李老师"},
            {"ID": "u3", "UserName": "s001", "DisplayName": "王同学"},
            {"ID": "u4", "UserName": "s002", "DisplayName": "赵同学"},
        ]

    def test_incremental_add_only(self, groups, users, rules_file):
        """已在组内的用户不会被重复添加（纯增量）"""
        rules = load_rules(rules_file)
        members = {
            "g_t": [{"IdentityID": "u1"}],   # u1 已在教师组
            "g_s": [],                        # 学生组为空
        }
        changes = compute_changes(users, groups, members, rules)
        assert changes == {
            "教师组": {"group_id": "g_t", "add": ["u2"], "remove": []},
            "学生组": {"group_id": "g_s", "add": ["u3", "u4"], "remove": []},
        }

    def test_remove_non_matching(self, groups, users, rules_file):
        """组内不再匹配的用户被移除"""
        rules = load_rules(rules_file)
        members = {
            "g_t": [{"IdentityID": "u1"}],
            "g_s": [{"IdentityID": "u1"}],   # u1 在学生组但规则目标是教师组 → 移除
        }
        changes = compute_changes(users, groups, members, rules)
        assert changes["学生组"]["remove"] == ["u1"]
        assert changes["学生组"]["add"] == ["u3", "u4"]
        assert changes["教师组"]["add"] == []

    def test_undeclared_group_untouched(self, groups, users, rules_file):
        """规则未声明的组不出现在变更中"""
        rules = load_rules(rules_file)
        members = {
            "g_v": [{"IdentityID": "u1"}],
            "g_s": [],
        }
        changes = compute_changes(users, groups, members, rules)
        assert "访客组" not in changes

    def test_mutex_priority(self, groups, users, rules_file):
        """用户同时命中互斥两个组时，按 MUTEX_GROUPS 声明顺序保留第一个"""
        # 学生组排第一 → 规则返回两个组时保留学生组
        rules_text = RULES_OK.replace('return "教师组"', 'return ["教师组", "学生组"]')
        path = rules_file
        path.write_text(rules_text, encoding="utf-8")
        rules = load_rules(rules_file)
        members = {"g_t": [], "g_s": []}
        changes = compute_changes(users, groups, members, rules)
        # u1 返回 [教师组, 学生组]，互斥集合 [学生组, 教师组]，按集合声明顺序保留学生组
        assert "u1" in changes["学生组"]["add"]
        assert "u1" not in changes["教师组"]["add"]

    def test_unknown_group_in_rules(self, groups, rules_file):
        """规则引用不存在的组 → 报错"""
        rules = load_rules(rules_file)
        with pytest.raises(ValueError, match="教师组"):
            compute_changes([], [{"ID": "g_s", "GroupName": "学生组"}], {}, rules)

    def test_returned_group_not_defined(self, groups, users, rules_file):
        """apply 返回了规则文件未引用……不适用：返回组名必须在平台组列表中"""
        rules = load_rules(rules_file)
        users2 = [{"ID": "u9", "UserName": "xyz", "DisplayName": "???"}]
        # xyz 匹配 fallback "学生组"，存在 → 正常
        changes = compute_changes(users2, groups, {}, rules)
        assert changes["学生组"]["add"] == ["u9"]
```

- [ ] **Step 2: 运行确认失败**

Run: `uv run pytest tests/test_group_sync.py -v`
Expected: FAIL — `ModuleNotFoundError: inactive_user_cli.core.group_sync`

- [ ] **Step 3: 实现 load_rules + compute_changes**

在 `src/inactive_user_cli/core/group_sync.py` 写入（Task 3 会补 `run`）：

```python
"""用户组同步引擎 - 规则加载、增量计算、执行"""

import importlib.util
import sys
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

    return {
        "apply": apply_fn,
        "MUTEX_GROUPS": list(getattr(module, "MUTEX_GROUPS", []) or []),
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
    referenced.add("__probe__")

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
    referenced.discard("__probe__")

    # 校验引用的组都存在
    missing = [g for g in referenced if g not in name_to_id]
    if missing:
        raise RulesError(f"规则引用的组在平台中不存在: {', '.join(missing)}")

    # 现有成员: {组 ID: {用户 ID...}}
    current: dict[str, set[str]] = {
        gid: {m.get("IdentityID", "") for m in group_members.get(gid, [])}
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
```

- [ ] **Step 4: 运行确认通过**

Run: `uv run pytest tests/test_group_sync.py -v`
Expected: 11 PASS

- [ ] **Step 5: 提交**

```bash
git add src/inactive_user_cli/core/group_sync.py tests/test_group_sync.py
git commit -m "feat: add rule loading and incremental change computation"
```

---

### Task 3: GroupSyncEngine（数据拉取 + 执行 + dry run）

**Files:**
- Modify: `src/inactive_user_cli/core/group_sync.py`
- Test: `tests/test_group_sync.py`（追加）

- [ ] **Step 1: 追加失败测试**

在 `tests/test_group_sync.py` 末尾追加：

```python
from inactive_user_cli.core.group_sync import GroupSyncEngine


@pytest.fixture
def mock_client2():
    from unittest.mock import Mock
    from inactive_user_cli.api.client import APIClient
    from inactive_user_cli.config import APIConfig
    config = APIConfig(
        host="10.10.160.222:30040/",
        version="2023-08-01",
        service="app",
        region="cn-north-1",
        account_id="1000000000",
        ak="test_ak",
        sk="test_sk",
    )
    client = APIClient(config)
    client.request = Mock()
    client.paginated_request = Mock()
    return client


class TestGroupSyncEngine:
    def test_fetch_and_compute(self, mock_client2, rules_file):
        """fetch_changes 拉取用户/组/成员并计算变更"""
        engine = GroupSyncEngine(mock_client2, rules_file)

        def paginated_side_effect(action, data, **kwargs):
            if action == "ListUserForAdmin":
                return (
                    [{"ID": "u1", "UserName": "20220178", "DisplayName": "张老师"},
                     {"ID": "u2", "UserName": "s001", "DisplayName": "王同学"}], 2,
                )
            if action == "ListUserGroup":
                return ([{"ID": "g_t", "GroupName": "教师组"},
                         {"ID": "g_s", "GroupName": "学生组"}], 2,)
            if action == "ListGroupMember":
                gid = data["GroupID"]
                return ([{"IdentityID": "u1"}] if gid == "g_t" else ([{"IdentityID": "u2"}]), 1,)

        mock_client2.paginated_request.side_effect = paginated_side_effect
        changes = engine.fetch_changes()
        # u1 → 教师组（已在内，无操作）；u2 → 学生组（已在）；教师组现有 u1 匹配、学生组现有 u2 匹配
        assert changes == {}

    def test_fetch_changes_unknown_group(self, mock_client2, rules_file):
        """规则引用不存在的组 → RulesError"""
        engine = GroupSyncEngine(mock_client2, rules_file)

        def paginated_side_effect(action, data, **kwargs):
            if action == "ListUserForAdmin":
                return ([], 0)
            return ([{"ID": "g_s", "GroupName": "学生组"}], 1)

        mock_client2.paginated_request.side_effect = paginated_side_effect
        with pytest.raises(Exception, match="不存在"):
            engine.fetch_changes()

    def test_dry_run_no_write_calls(self, mock_client2, rules_file):
        """dry_run=True 不调用 CreateGroupMember/RemoveGroupMember"""
        engine = GroupSyncEngine(mock_client2, rules_file)

        def paginated_side_effect(action, data, **kwargs):
            if action == "ListUserForAdmin":
                return (
                    [{"ID": "u2", "UserName": "20220179", "DisplayName": "李老师"}], 1,
                )
            if action == "ListUserGroup":
                return ([{"ID": "g_t", "GroupName": "教师组"},
                         {"ID": "g_s", "GroupName": "学生组"}], 2,)
            if action == "ListGroupMember":
                return ([{"IdentityID": "u1"}] if data["GroupID"] == "g_t" else [], 1 if data["GroupID"] == "g_t" else 0,)

        mock_client2.paginated_request.side_effect = paginated_side_effect
        mock_client2.request = Mock()

        result = engine.run(dry_run=True)
        # u2 应加入教师组 → 但 dry run 不应有任何写请求
        mock_client2.request.assert_not_called()
        assert result["dry_run"] is True
        assert result["applied"] is False
        assert result["changes"]["教师组"]["add"] == ["u2"]

    def test_execute_add_and_remove(self, mock_client2, rules_file):
        """执行模式调用 add/remove 并返回结果"""
        engine = GroupSyncEngine(mock_client2, rules_file)

        def paginated_side_effect(action, data, **kwargs):
            if action == "ListUserForAdmin":
                return (
                    [{"ID": "u2", "UserName": "20220179", "DisplayName": "李老师"},
                     {"ID": "u1", "UserName": "s001", "DisplayName": "王同学"}], 2,
                )
            if action == "ListUserGroup":
                return ([{"ID": "g_t", "GroupName": "教师组"},
                         {"ID": "g_s", "GroupName": "学生组"}], 2,)
            if action == "ListGroupMember":
                if data["GroupID"] == "g_t":
                    return ([{"IdentityID": "u1"}], 1)  # u1 在教师组但规则判定为学生组
                return ([], 0)

        mock_client2.paginated_request.side_effect = paginated_side_effect
        mock_client2.request = Mock()

        result = engine.run(dry_run=False)
        mock_client2.request.assert_called()
        calls = {args[0] for args, _ in mock_client2.request.call_args_list}
        assert calls == {"CreateGroupMember", "RemoveGroupMember"}
        assert result["applied"] is True
        # 教师组: add u2, remove u1；学生组: add u1
        assert result["changes"]["教师组"]["add"] == ["u2"]
        assert result["changes"]["教师组"]["remove"] == ["u1"]
        assert result["changes"]["学生组"]["add"] == ["u1"]
```

- [ ] **Step 2: 运行确认失败**

Run: `uv run pytest tests/test_group_sync.py -v -k Engine`
Expected: FAIL — `ImportError: cannot import name 'GroupSyncEngine'`

- [ ] **Step 3: 实现 GroupSyncEngine**

在 `src/inactive_user_cli/core/group_sync.py` 末尾追加：

```python
from ..api.client import APIClient, APIError


class GroupSyncEngine:
    """用户组同步引擎：拉取数据 → 计算变更 → 执行/预览"""

    def __init__(self, client: APIClient, rules_path: str | Path, page_size: int = 10000):
        self.client = client
        self.rules_path = Path(rules_path)
        self.page_size = page_size
        self.rules = load_rules(self.rules_path)

    def fetch_changes(self) -> dict[str, dict[str, Any]]:
        """拉取平台数据并计算变更"""
        from ..api.group import GroupAPI
        from ..api.user import ListUserAPI

        group_api = GroupAPI(self.client)
        user_api = ListUserAPI(self.client)

        groups, _ = group_api.list_groups(page_size=self.page_size)
        users, _ = user_api.list_users(include_visitor=True, page_size=self.page_size)

        name_to_id = {g.get("GroupName", ""): g.get("ID", "") for g in groups}
        referenced = {g for mset in self.rules["MUTEX_GROUPS"] for g in mset}

        # 先跑一遍 compute_changes 拿到引用集合，再拉这些组的成员
        try:
            changes = compute_changes(users, groups, {}, self.rules)
        except RulesError:
            raise

        group_members: dict[str, list[dict[str, Any]]] = {}
        all_names = set(changes.keys()) | referenced
        for name in all_names:
            gid = name_to_id.get(name)
            if not gid:
                continue
            members, _ = group_api.list_group_members(gid, page_size=self.page_size)
            group_members[gid] = members

        # 用真实成员重算（现有成员数据到位后增量才准确）
        return compute_changes(users, groups, group_members, self.rules)

    def run(self, dry_run: bool = False) -> dict[str, Any]:
        """执行同步；dry_run=True 时只返回变更不调用写接口

        Returns:
            {"changes": 变更表, "dry_run": bool, "applied": bool,
             "success": int, "failure": int, "errors": [str...]}
        """
        changes = self.fetch_changes()

        if dry_run:
            return {"changes": changes, "dry_run": True, "applied": False,
                    "success": 0, "failure": 0, "errors": []}

        from ..api.group import GroupAPI
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
```

- [ ] **Step 4: 运行确认通过**

Run: `uv run pytest tests/test_group_sync.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add src/inactive_user_cli/core/group_sync.py tests/test_group_sync.py
git commit -m "feat: add GroupSyncEngine with dry run support"
```

---

### Task 4: CLI sync-groups 命令 + Rich 输出

**Files:**
- Modify: `src/inactive_user_cli/cli.py`
- Modify: `src/inactive_user_cli/logger.py`
- Create: `src/inactive_user_cli/core/rules_example.py.example`
- Test: `tests/test_cli_sync.py`

- [ ] **Step 1: 在 logger.py 追加输出方法（无独立测试，随 CLI 测试覆盖）**

在 `LogManager` 类内追加：

```python
    def print_sync_changes(self, changes: dict[str, dict], dry_run: bool):
        """打印同步变更表"""
        from rich.table import Table

        mode = "[yellow]DRY RUN[/yellow] - " if dry_run else ""
        if not changes:
            console.print(f"\n{mode}[green]所有组已同步，无需变更[/green]")
            return

        console.print(f"\n{mode}[bold]同步变更预览:[/bold]\n")
        for group_name, change in changes.items():
            table = Table(title=f"组: {group_name}", show_header=True, header_style="bold magenta")
            table.add_column("操作", style="cyan")
            table.add_column("用户 ID", style="white")
            for uid in change["add"]:
                table.add_row("[green]添加[/green]", uid)
            for uid in change["remove"]:
                table.add_row("[red]移除[/red]", uid)
            console.print(table)

        add_total = sum(len(c["add"]) for c in changes.values())
        remove_total = sum(len(c["remove"]) for c in changes.values())
        console.print(f"\n合计: [green]添加 {add_total}[/green] / [red]移除 {remove_total}[/red]")

    def print_sync_summary(self, result: dict):
        """打印执行结果摘要"""
        if result["dry_run"]:
            return
        if result["failure"]:
            console.print(f"\n[red]执行完成: 成功 {result['success']} 项，失败 {result['failure']} 项[/red]")
            for err in result["errors"]:
                console.print(f"  [red]✗[/red] {err}")
        else:
            console.print(f"\n[green]✓ 同步完成: 共执行 {result['success']} 项操作[/green]")
```

- [ ] **Step 2: 写 CLI 失败测试**

`tests/test_cli_sync.py`:

```python
"""sync-groups 命令测试"""

import textwrap

import pytest
from unittest.mock import Mock, patch

from click.testing import CliRunner

from inactive_user_cli.cli import main

RULES = textwrap.dedent("""
    MUTEX_GROUPS = [["学生组", "教师组"]]
    def apply(user):
        return "教师组" if user.get("UserName", "").startswith("2022") else None
""")


@pytest.fixture
def rules_file(tmp_path):
    path = tmp_path / "rules.py"
    path.write_text(RULES, encoding="utf-8")
    return str(path)


@pytest.fixture
def runner():
    return CliRunner()


def fake_engine_data():
    """mock GroupSyncEngine.run 返回的 dry run 结果"""
    return {
        "changes": {"教师组": {"group_id": "g_t", "add": ["u1"], "remove": []}},
        "dry_run": True, "applied": False,
        "success": 0, "failure": 0, "errors": [],
    }


class TestSyncGroupsCommand:
    def test_dry_run_no_confirm(self, runner, rules_file):
        """--dry-run 直接输出预览，不请求确认"""
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   return_value=fake_engine_data()):
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file, "--dry-run"],
            )
        assert result.exit_code == 0
        assert "教师组" in result.output

    def test_execute_requires_confirm(self, runner, rules_file):
        """执行模式需要确认，取消则不执行"""
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   return_value=fake_engine_data()) as mock_run:
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file],
                input="n\n",
            )
        assert result.exit_code == 0
        # run 在确认前调用过（获取预览），但只有 dry_run 调用；确认取消后不重复执行
        assert mock_run.call_count == 1
        assert mock_run.call_args.kwargs.get("dry_run") is True

    def test_missing_rules_file(self, runner, tmp_path):
        """规则文件不存在 → 报错退出"""
        result = runner.invoke(
            main, ["sync-groups", "--rules", str(tmp_path / "nope.py"), "--dry-run"],
        )
        assert result.exit_code == 1

    def test_invalid_rules(self, runner, tmp_path):
        """规则脚本缺 apply → 报错退出"""
        bad = tmp_path / "bad.py"
        bad.write_text("x = 1\n", encoding="utf-8")
        result = runner.invoke(
            main, ["sync-groups", "--rules", str(bad), "--dry-run"],
        )
        assert result.exit_code == 1
```

- [ ] **Step 3: 运行确认失败**

Run: `uv run pytest tests/test_cli_sync.py -v`
Expected: FAIL — sync-groups 命令不存在（exit code 2, "No such command"）

- [ ] **Step 4: 实现 sync-groups 命令**

在 `cli.py` 导入区追加：

```python
from inactive_user_cli.core.group_sync import GroupSyncEngine, RulesError
```

在 `logs` 命令之前追加命令：

```python
@main.command("sync-groups")
@click.option("--rules", "rules_path", required=True, type=click.Path(exists=True), help="规则脚本路径")
@click.option("--dry-run", is_flag=True, help="仅预览变更，不执行")
@click.option("--force", is_flag=True, help="跳过确认直接执行")
def sync_groups(rules_path: str, dry_run: bool, force: bool):
    """根据规则脚本增量同步用户组成员（添加缺失 + 移除不匹配）"""
    config, logger, client = get_config()
    logger.print_header("用户组同步")

    try:
        engine = GroupSyncEngine(client, rules_path)
    except RulesError as e:
        logger.print_error(f"规则错误: {e}")
        sys.exit(1)

    try:
        # 先预览（dry run 计算）
        result = engine.run(dry_run=True)
        logger.print_sync_changes(result["changes"], dry_run=True)

        if dry_run:
            return

        if not result["changes"]:
            logger.print_info("所有组已同步，无需变更")
            return

        if not force:
            if not click.confirm("\n确认执行以上变更？"):
                logger.print_info("已取消")
                return

        final_result = engine.run(dry_run=False)
        logger.print_sync_changes(final_result["changes"], dry_run=False)
        logger.print_sync_summary(final_result)

        # 保存日志
        log_file = logger.save_sync_log(final_result)
        logger.print_info(f"日志已保存: {log_file}")

    except RulesError as e:
        logger.print_error(f"规则错误: {e}")
        sys.exit(1)
    except APIError as e:
        logger.print_error(f"API 请求失败: {e}")
        sys.exit(1)
```

注意：这里调了两次 `engine.run`（第一次 dry_run=True 用于预览，第二次真实执行时重新拉取计算，避免预览与执行之间数据变化导致不一致的旧状态写入）。`test_execute_requires_confirm` 断言 mock 下两次调用均为 dry_run=True/False —— mock 返回值固定，取消时 call_count==1。若 mock 使第二次调用也返回 dry_run 数据，测试中 `input="n\n"` 取消后 run 只被调一次，逻辑自洽。

- [ ] **Step 5: 在 logger.py 追加 save_sync_log**

在 `LogManager` 类内追加（复用 `save_delete_log` 的文件命名风格，先查看该方法确认命名规则后照抄格式）：

```python
    def save_sync_log(self, result: dict) -> Path:
        """保存同步日志"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"sync_{timestamp}.json"
        data = {
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": "sync_groups",
            "dry_run": result["dry_run"],
            "applied": result["applied"],
            "changes": result["changes"],
            "success_count": result["success"],
            "failure_count": result["failure"],
            "errors": result["errors"],
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return log_file
```

实现前先 Read `src/inactive_user_cli/logger.py` 中 `save_delete_log` 的实际实现，若其命名/结构不同则按其风格调整 `save_sync_log`。

- [ ] **Step 6: 运行确认通过**

Run: `uv run pytest tests/test_cli_sync.py tests/test_group_sync.py -v`
Expected: 全部 PASS

- [ ] **Step 7: 全量回归**

Run: `uv run pytest`
Expected: 全部 PASS（含原有测试）

- [ ] **Step 8: 提交**

```bash
git add src/inactive_user_cli/cli.py src/inactive_user_cli/logger.py tests/test_cli_sync.py
git commit -m "feat: add sync-groups command with dry run support"
```

---

### Task 5: 规则示例文件 + README 更新

**Files:**
- Create: `src/inactive_user_cli/core/rules_example.py.example`
- Modify: `README.md`

- [ ] **Step 1: 创建示例规则文件**

`src/inactive_user_cli/core/rules_example.py.example`:

```python
# 用户组同步规则脚本示例
# 复制为 rules.py 后修改，运行:
#   uv run inactive-user sync-groups --rules rules.py --dry-run
#
# 必须定义: apply(user) -> 组名(str) / 组名列表(list[str]) / None
# 可选定义: MUTEX_GROUPS - 互斥组集合，同一集合内用户只能属于一个组，
#           同时命中多个时按声明顺序保留第一个

import re

MUTEX_GROUPS = [
    ["学生组", "教师组"],
]


def apply(user):
    """根据用户属性决定目标组，不匹配返回 None"""
    # 用户名是 8 位数字 → 教师组
    if re.fullmatch(r"\d{8}", user.get("UserName", "")):
        return "教师组"
    # 邮箱包含 @stu. → 学生组
    email = user.get("Email", "") or ""
    if "@stu." in email:
        return "学生组"
    # 不匹配任何组
    return None
```

- [ ] **Step 2: 更新 README.md**

在 README 的命令列表部分（先 Read README 找到现有命令表所在位置）追加：

```markdown
## 用户组同步

根据规则脚本增量同步用户组成员（添加缺失成员 + 移除不匹配成员）。

```bash
# 预览变更（不执行）
uv run inactive-user sync-groups --rules rules.py --dry-run

# 执行（需确认）
uv run inactive-user sync-groups --rules rules.py

# 跳过确认
uv run inactive-user sync-groups --rules rules.py --force
```

规则脚本示例见 `src/inactive_user_cli/core/rules_example.py.example`。
```

- [ ] **Step 3: 全量回归**

Run: `uv run pytest`
Expected: 全部 PASS

- [ ] **Step 4: 提交**

```bash
git add src/inactive_user_cli/core/rules_example.py.example README.md
git commit -m "docs: add group sync rules example and README section"
```

---

## Self-Review 结果

- **Spec 覆盖：** 4 个 API 接口（Task 1）、规则加载/互斥/增量（Task 2）、dry run/执行（Task 3）、CLI/日志（Task 4）、示例与文档（Task 5）——全部覆盖
- **占位符：** 无 TBD/TODO；logger 的 save_delete_log 风格差异已用显式检查步骤处理
- **类型一致性：** `compute_changes` 返回 `{组名: {"group_id", "add", "remove"}}` 在 Task 2/3/4 一致；`RulesError` 在 Task 2 定义、Task 4 CLI 使用
