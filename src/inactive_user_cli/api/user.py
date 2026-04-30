"""ListUserForAdmin 接口 - 获取平台用户列表"""

from typing import Any

from .client import APIClient


class ListUserAPI:
    """ListUserForAdmin 接口封装"""

    ACTION = "ListUserForAdmin"

    def __init__(self, client: APIClient):
        self.client = client

    def list_users(
        self,
        query: str | None = None,
        status: int | None = None,
        role_name: str | None = None,
        org_id: str | None = None,
        include_visitor: bool = True,
        source: str | None = None,
        contact_search: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取用户列表

        Returns:
            (users, total): 用户列表和总数
        """
        data: dict[str, Any] = {
            "IncludeVisitor": include_visitor,
        }

        if query:
            data["Query"] = query
        if status is not None:
            data["Status"] = status
        if role_name:
            data["RoleName"] = role_name
        if org_id:
            data["OrgID"] = org_id
        if source:
            data["Source"] = source
        if contact_search:
            data["ContactSearch"] = contact_search

        return self.client.paginated_request(
            action=self.ACTION,
            data=data,
            page_field="PageNumber",
            size_field="PageSize",
            items_field="Items",
            total_field="Total",
            page_size=page_size,
        )