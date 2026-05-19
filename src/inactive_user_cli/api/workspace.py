"""ListAllWorkspace 和 ListWorkspaceMember 接口"""

from dataclasses import dataclass
from typing import Any

from .client import APIClient


@dataclass
class WorkspaceMember:
    """工作空间成员信息"""
    member_id: str
    member_name: str
    member_display_name: str
    role: str


@dataclass
class WorkspaceInfo:
    """工作空间信息"""
    workspace_id: str
    workspace_name: str
    admins: list[WorkspaceMember]
    other_members: list[WorkspaceMember]


class ListWorkspaceAPI:
    """ListWorkspace 接口封装"""

    ACTION_LIST_ALL = "ListAllWorkspace"
    ACTION_LIST_MEMBERS = "ListWorkspaceMember"
    SERVICE = "iam"
    VERSION = "2024-12-25"

    def __init__(self, client: APIClient):
        self.client = client

    def list_all_workspaces(self, page_size: int = 10000) -> tuple[list[dict[str, Any]], int]:
        """
        获取所有工作空间

        Args:
            page_size: 每页大小（默认 10000）

        Returns:
            (workspaces, total): 工作空间列表和总数
        """
        data: dict[str, Any] = {
            "ListOpt": {
                "Sort": [{"SortField": "created_time", "SortOrder": "desc"}],
                "PageNumber": 1,
                "PageSize": page_size,
            },
            "Filter": {},
        }

        return self.client.paginated_request(
            action=self.ACTION_LIST_ALL,
            data=data,
            page_field="PageNumber",
            size_field="PageSize",
            items_field="Items",
            total_field="Total",
            page_size=page_size,
            service=self.SERVICE,
            version=self.VERSION,
        )

    def list_workspace_members(
        self,
        workspace_id: str,
        page_size: int = 10000,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取工作空间成员列表

        Args:
            workspace_id: 工作空间ID
            page_size: 每页大小（默认 10000）

        Returns:
            (members, total): 成员列表和总数
        """
        data: dict[str, Any] = {
            "ListOpt": {
                "PageNumber": 1,
                "PageSize": page_size,
            },
            "Filter": {},
            "WorkspaceID": workspace_id,
        }

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

    def get_workspace_admins(self, page_size: int = 10000) -> tuple[set[str], list[WorkspaceInfo]]:
        """
        获取所有工作空间信息

        Returns:
            (admin_names, workspaces):
            - admin_names: 空间管理员 Name 集合（用于排除）
            - workspaces: 工作空间信息列表（含管理员和其他成员）
        """
        workspaces, _ = self.list_all_workspaces(page_size=page_size)

        # 仅获取团队工作空间（IsPersonal: false）
        team_workspaces = [ws for ws in workspaces if not ws.get("IsPersonal", True)]

        admin_names: set[str] = set()
        workspaces_info: list[WorkspaceInfo] = []

        for ws in team_workspaces:
            workspace_id = ws.get("ID", "")
            workspace_name = ws.get("Name", "")
            admins: list[WorkspaceMember] = []
            other_members: list[WorkspaceMember] = []

            if workspace_id:
                members, _ = self.list_workspace_members(workspace_id, page_size=page_size)
                for member in members:
                    member_id = member.get("ID", "")
                    name = member.get("Name", "")
                    display_name = member.get("DisplayName", "") or name
                    role = member.get("Role", "")

                    ws_member = WorkspaceMember(
                        member_id=member_id,
                        member_name=name,
                        member_display_name=display_name,
                        role=role,
                    )

                    if role == "WorkspaceAdmin":
                        if name:
                            admin_names.add(name)
                            admins.append(ws_member)
                    elif role == "WorkspaceMember" or role == "WorkspaceVisitor":
                        other_members.append(ws_member)

            workspaces_info.append(WorkspaceInfo(
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                admins=admins,
                other_members=other_members,
            ))

        return admin_names, workspaces_info