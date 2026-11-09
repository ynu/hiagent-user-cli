"""sync-groups 命令测试"""

import textwrap

import pytest
from unittest.mock import patch

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
        # run 被调用过（预览），取消后未再次执行
        assert mock_run.call_count == 1
        assert mock_run.call_args.kwargs.get("dry_run") is True

    def test_execute_with_force(self, runner, rules_file, tmp_path):
        """--force 跳过确认直接执行"""
        dry = fake_engine_data()
        final = dict(fake_engine_data(), dry_run=False, applied=True, success=1, failure=0, errors=[])
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   side_effect=[dry, final]) as mock_run, \
             patch("inactive_user_cli.logger.LogManager.save_sync_log",
                   return_value=tmp_path / "log.json"):
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file, "--force"],
            )
        assert result.exit_code == 0
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[-1].kwargs.get("dry_run") is False

    def test_missing_rules_file(self, runner, tmp_path):
        """规则文件不存在 → 报错退出"""
        result = runner.invoke(
            main, ["sync-groups", "--rules", str(tmp_path / "nope.py"), "--dry-run"],
        )
        assert result.exit_code != 0

    def test_invalid_rules(self, runner, tmp_path):
        """规则脚本缺 apply → 报错退出"""
        bad = tmp_path / "bad.py"
        bad.write_text("x = 1\n", encoding="utf-8")
        result = runner.invoke(
            main, ["sync-groups", "--rules", str(bad), "--dry-run"],
        )
        assert result.exit_code == 1
