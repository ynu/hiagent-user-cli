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

    def test_bad_mutex_shape(self, tmp_path):
        path = tmp_path / "bad.py"
        path.write_text('MUTEX_GROUPS = "学生组"\ndef apply(user):\n    return None\n', encoding="utf-8")
        with pytest.raises(ValueError, match="MUTEX_GROUPS"):
            load_rules(path)


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
        # u2 也是教师（8 位工号）且不在教师组 → 需要添加
        assert changes["教师组"]["add"] == ["u2"]

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
        # 所有人都被仲裁到学生组 → 教师组没有任何变更，不出现
        assert "教师组" not in changes

    def test_unknown_group_in_rules(self, groups, rules_file):
        """规则引用不存在的组 → 报错"""
        rules = load_rules(rules_file)
        with pytest.raises(ValueError, match="教师组"):
            compute_changes([], [{"ID": "g_s", "GroupName": "学生组"}], {}, rules)

    def test_apply_raises(self, groups, rules_file):
        """apply 抛异常 → 包装为 RulesError 并带用户信息"""
        rules = load_rules(rules_file)
        # 覆盖 rules["apply"] 为抛异常的函数
        def bad_apply(user):
            raise RuntimeError("boom")
        rules["apply"] = bad_apply
        with pytest.raises(ValueError, match="boom"):
            compute_changes([{"ID": "u1", "UserName": "20220178"}], groups, {}, rules)

    def test_fallback_group_exists(self, groups, users, rules_file):
        """apply 返回的组名必须在平台组列表中；xyz 匹配 fallback "学生组"，存在 → 正常"""
        rules = load_rules(rules_file)
        users2 = [{"ID": "u9", "UserName": "xyz", "DisplayName": "???"}]
        changes = compute_changes(users2, groups, {}, rules)
        assert changes["学生组"]["add"] == ["u9"]


from unittest.mock import Mock

from inactive_user_cli.core.group_sync import GroupSyncEngine


@pytest.fixture
def mock_client2():
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
