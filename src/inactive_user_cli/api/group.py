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
