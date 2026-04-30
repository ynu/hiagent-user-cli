"""CLI 测试"""

import pytest
from click.testing import CliRunner

from inactive_user_cli.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    """CLI 测试"""

    def test_version(self, runner):
        """测试版本命令"""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help(self, runner):
        """测试帮助命令"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "delete" in result.output