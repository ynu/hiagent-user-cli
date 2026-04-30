"""ListApp 接口 - 获取智能体列表及创建人信息"""

from typing import Any

from .client import APIClient


class ListAppAPI:
    """ListApp 接口封装"""

    ACTION = "ListApp"

    def __init__(self, client: APIClient):
        self.client = client

    def list_apps(
        self,
        keyword: str | None = None,
        app_type: int | None = None,
        status: int | None = None,
        workspace_id: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取智能体列表

        Returns:
            (apps, total): 智能体列表和总数
        """
        data: dict[str, Any] = {}

        if keyword or app_type is not None or status is not None or workspace_id:
            data["Filter"] = {}
            if keyword:
                data["Filter"]["Keyword"] = keyword
            if app_type is not None:
                data["Filter"]["AppType"] = app_type
            if status is not None:
                data["Filter"]["Status"] = status
            if workspace_id:
                data["Filter"]["WorkspaceID"] = workspace_id

        return self.client.paginated_request(
            action=self.ACTION,
            data=data,
            page_field="PageNumber",
            size_field="PageSize",
            items_field="Items",
            total_field="Total",
            page_size=page_size,
        )

    def get_creators(self, page_size: int = 100) -> set[str]:
        """
        获取所有智能体创建人的 ID 集合

        Returns:
            创建人 ID 集合
        """
        apps, _ = self.list_apps(page_size=page_size)
        creators = {app.get("CreateUser", "") for app in apps if app.get("CreateUser")}
        return creators