"""ListApp 接口 - 获取智能体列表及创建人信息"""

from typing import Any

from .client import APIClient


# ListApp 默认时间范围（覆盖所有数据）
DEFAULT_START_TIME = "2020-01-01T00:00:00.00Z"
DEFAULT_END_TIME = "2100-01-01T00:00:00.00Z"


class ListAppAPI:
    """ListApp 接口封装"""

    ACTION = "ListApp"
    # ListApp 使用 app service
    SERVICE = "app"

    def __init__(self, client: APIClient):
        self.client = client

    def list_apps(
        self,
        keyword: str | None = None,
        app_type: int | None = None,
        status: int | None = None,
        workspace_id: str | None = None,
        page_size: int = 10000,
        start_time: str | None = DEFAULT_START_TIME,
        end_time: str | None = DEFAULT_END_TIME,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取智能体列表

        Args:
            keyword: 搜索关键词
            app_type: 智能体类型
            status: 智能体状态
            workspace_id: 工作空间ID
            page_size: 每页大小（默认 10000）
            start_time: 创建时间起始（默认 2020-01-01）
            end_time: 创建时间结束（默认 2100-01-01）

        Returns:
            (apps, total): 智能体列表和总数
        """
        # 构造 Filter（必须包含时间范围）
        data: dict[str, Any] = {
            "Filter": {
                "StartTime": start_time,
                "EndTime": end_time,
            }
        }

        # 添加可选过滤条件
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
            service=self.SERVICE,
        )

    def get_creators(self, page_size: int = 10000) -> set[str]:
        """
        获取所有智能体创建人的 ID 集合

        Returns:
            创建人 ID 集合
        """
        apps, _ = self.list_apps(page_size=page_size)
        creators = {app.get("CreateUser", "") for app in apps if app.get("CreateUser")}
        return creators