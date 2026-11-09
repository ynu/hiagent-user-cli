"""GroupAPI 测试"""

import pytest
from unittest.mock import Mock

from inactive_user_cli.api.group import GroupAPI


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
