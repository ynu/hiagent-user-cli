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

    def test_execute_displays_final_changes(self, runner, rules_file, tmp_path):
        """执行后显示实际执行的变更（非 DRY RUN 预览）"""
        dry = fake_engine_data()
        final = dict(fake_engine_data(), dry_run=False, applied=True, success=1, failure=0, errors=[])
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   side_effect=[dry, final]), \
             patch("inactive_user_cli.logger.LogManager.save_sync_log",
                   return_value=tmp_path / "log.json"):
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file, "--force"],
            )
        assert result.exit_code == 0
        # 预览 + 执行各打印一次变更表；DRY RUN 标记只出现在预览
        assert result.output.count("同步变更预览") == 2
        assert result.output.count("DRY RUN") == 1
        # 摘要按批次计数描述
        assert "批操作" in result.output

    def test_no_changes_skips_confirm(self, runner, rules_file):
        """无变更时跳过确认，不执行"""
        dry = dict(fake_engine_data(), changes={})
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   return_value=dry) as mock_run:
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file],
            )
        assert result.exit_code == 0
        assert mock_run.call_count == 1

    def test_execute_warns_on_divergence(self, runner, rules_file):
        """执行集与预览不一致时输出警告"""
        dry = fake_engine_data()
        final = dict(fake_engine_data(),
                     changes={"教师组": {"group_id": "g_t", "add": ["u1", "u9"], "remove": []}},
                     dry_run=False, applied=True, success=1, failure=0, errors=[])
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   side_effect=[dry, final]), \
             patch("inactive_user_cli.logger.LogManager.save_sync_log",
                   return_value=None):
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file, "--force"],
            )
        assert result.exit_code == 0
        assert "已变化" in result.output

    def test_no_divergence_no_warning(self, runner, rules_file):
        """执行集与预览一致时不输出警告"""
        dry = fake_engine_data()
        final = dict(fake_engine_data(), dry_run=False, applied=True, success=1, failure=0, errors=[])
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   side_effect=[dry, final]), \
             patch("inactive_user_cli.logger.LogManager.save_sync_log",
                   return_value=None):
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file, "--force"],
            )
        assert result.exit_code == 0
        assert "已变化" not in result.output

    def test_execute_api_error(self, runner, rules_file):
        """执行阶段 API 错误 → 退出码 1"""
        from inactive_user_cli.api.client import APIError
        dry = fake_engine_data()
        with patch("inactive_user_cli.core.group_sync.GroupSyncEngine.run",
                   side_effect=[dry, APIError("boom")]):
            result = runner.invoke(
                main, ["sync-groups", "--rules", rules_file, "--force"],
            )
        assert result.exit_code == 1

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


SYNC_LOG = """{
    "version": "1.0.0",
    "timestamp": "2026-01-01T00:00:00+00:00",
    "operation": "sync_groups",
    "total_count": 1,
    "success_count": 1,
    "failure_count": 0,
    "changes": {"教师组": {"group_id": "g_t", "add": ["u1"], "remove": []}}
}"""


class TestLogsCommand:
    def test_logs_lists_sync_logs(self, runner, tmp_path):
        """logs 列出 sync_*.json 日志"""
        (tmp_path / "sync_20260101_000000.json").write_text(SYNC_LOG, encoding="utf-8")
        result = runner.invoke(main, ["logs", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "sync_20260101_000000.json" in result.output
        assert "同步日志" in result.output

    def test_logs_views_sync_log(self, runner, tmp_path):
        """查看 sync 日志：显示同步日志头与分组变更摘要"""
        (tmp_path / "sync_20260101_000000.json").write_text(SYNC_LOG, encoding="utf-8")
        result = runner.invoke(
            main, ["logs", "sync_20260101_000000.json", "--dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "同步日志" in result.output
        assert "教师组" in result.output
