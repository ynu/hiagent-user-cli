"""分析器测试"""

import pytest
from unittest.mock import Mock, MagicMock

from inactive_user_cli.core.analyzer import InactiveUserAnalyzer
from inactive_user_cli.api.client import APIClient
from inactive_user_cli.logger import LogManager
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
    return APIClient(config)


@pytest.fixture
def mock_logger():
    logger = Mock(spec=LogManager)
    # Mock the context manager for create_progress
    progress_mock = MagicMock()
    progress_mock.__enter__ = Mock(return_value=progress_mock)
    progress_mock.__exit__ = Mock(return_value=None)
    progress_mock.add_task = Mock(return_value="task_1")
    progress_mock.update = Mock()
    logger.create_progress = Mock(return_value=progress_mock)
    return logger


@pytest.fixture
def analyzer(mock_client, mock_logger):
    return InactiveUserAnalyzer(mock_client, mock_logger)


class TestInactiveUserAnalyzer:
    """InactiveUserAnalyzer 测试"""

    def test_init(self, analyzer, mock_client, mock_logger):
        """测试初始化"""
        assert analyzer.client == mock_client
        assert analyzer.logger == mock_logger

    def test_analyze_empty(self, analyzer, mock_client):
        """测试空数据分析"""
        # paginated_request 调用顺序: ListApp -> ListUser -> ListAllWorkspace -> ListWorkspaceMember
        mock_client.paginated_request = Mock(side_effect=[([], 0), ([], 0), ([], 0), ([], 0)])
        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 0
        assert result["active_users"] == 0
        assert result["inactive_count"] == 0
        assert result["inactive_users"] == []

    def test_analyze_all_active(self, analyzer, mock_client):
        """测试所有用户都是活跃用户"""
        apps = [
            {"CreateUserID": "user_001"},
            {"CreateUserID": "user_002"},
        ]
        users = [
            {"ID": "user_001", "Name": "User 1"},
            {"ID": "user_002", "Name": "User 2"},
        ]

        # paginated_request 调用顺序: ListApp -> ListUser -> ListAllWorkspace -> ListWorkspaceMember
        mock_client.paginated_request = Mock(side_effect=[(apps, 2), (users, 2), ([], 0), ([], 0)])
        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 2
        assert result["active_users"] == 2
        assert result["inactive_count"] == 0
        assert result["inactive_users"] == []

    def test_analyze_mixed(self, analyzer, mock_client):
        """测试混合用户（活跃和非活跃）"""
        apps = [
            {"CreateUserID": "user_001"},
        ]
        users = [
            {"ID": "user_001", "Name": "Active User"},
            {"ID": "user_002", "Name": "Inactive User"},
            {"ID": "user_003", "Name": "Another Inactive"},
        ]

        # paginated_request 调用顺序: ListApp -> ListUser -> ListAllWorkspace -> ListWorkspaceMember
        mock_client.paginated_request = Mock(side_effect=[(apps, 1), (users, 3), ([], 0), ([], 0)])
        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 3
        assert result["active_users"] == 1
        assert result["inactive_count"] == 2
        assert len(result["inactive_users"]) == 2

        inactive_ids = {u["ID"] for u in result["inactive_users"]}
        assert "user_002" in inactive_ids
        assert "user_003" in inactive_ids
        assert "user_001" not in inactive_ids

    def test_analyze_exclude_workspace_admins(self, analyzer, mock_client):
        """测试排除空间管理员"""
        apps = [
            {"CreateUserID": "user_001"},
        ]
        users = [
            {"ID": "user_001", "UserName": "Active User", "DisplayName": ""},
            {"ID": "user_002", "UserName": "Inactive User", "DisplayName": ""},
            {"ID": "user_003", "UserName": "Workspace Admin", "DisplayName": ""},  # 空间管理员
            {"ID": "user_004", "UserName": "Another Inactive", "DisplayName": ""},
        ]
        # 工作空间列表（1个团队工作空间）
        workspaces = [
            {"ID": "ws_001", "IsPersonal": False},
        ]
        # 工作空间成员（包含 WorkspaceAdmin）
        members = [
            {"Name": "Workspace Admin", "Role": "WorkspaceAdmin"},
            {"Name": "Regular Member", "Role": "WorkspaceMember"},
        ]

        # paginated_request 调用顺序: ListApp -> ListUser -> ListAllWorkspace -> ListWorkspaceMember
        mock_client.paginated_request = Mock(side_effect=[
            (apps, 1),        # ListApp
            (users, 4),       # ListUser
            (workspaces, 1),  # ListAllWorkspace
            (members, 2),     # ListWorkspaceMember
        ])
        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 4
        assert result["active_users"] == 1
        assert result["inactive_count"] == 2  # user_002 和 user_004（排除 user_003 空间管理员）
        assert len(result["inactive_users"]) == 2

        inactive_ids = {u["ID"] for u in result["inactive_users"]}
        assert "user_002" in inactive_ids
        assert "user_004" in inactive_ids
        assert "user_003" not in inactive_ids  # 空间管理员被排除