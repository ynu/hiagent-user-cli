"""非活跃用户分析器"""

from typing import Any

from inactive_user_cli.api.client import APIClient
from inactive_user_cli.api.app import ListAppAPI
from inactive_user_cli.api.user import ListUserAPI
from inactive_user_cli.logger import LogManager


class InactiveUserAnalyzer:
    """非活跃用户分析器"""

    def __init__(self, client: APIClient, logger: LogManager):
        self.client = client
        self.logger = logger
        self.list_app = ListAppAPI(client)
        self.list_user = ListUserAPI(client)

    def analyze(self, page_size: int = 100) -> dict[str, Any]:
        """
        分析非活跃用户

        Returns:
            包含分析结果的字典
        """
        with self.logger.create_progress() as progress:
            # 步骤1: 获取智能体创建人
            task1 = progress.add_task("[cyan]获取智能体创建人...", total=None)
            creators = self.list_app.get_creators(page_size=page_size)
            progress.update(task1, completed=True, description=f"[green]获取到 {len(creators)} 个创建人")

            # 步骤2: 获取平台用户
            task2 = progress.add_task("[cyan]获取平台用户...", total=None)
            users, total_users = self.list_user.list_users(page_size=page_size)
            progress.update(task2, completed=True, description=f"[green]获取到 {total_users} 个用户")

        # 步骤3: 计算非活跃用户
        inactive_users = []
        active_count = 0

        for user in users:
            user_id = user.get("ID", "")
            if user_id not in creators:
                inactive_users.append(user)
            else:
                active_count += 1

        return {
            "total_users": total_users,
            "active_users": active_count,
            "inactive_users": inactive_users,
            "inactive_count": len(inactive_users),
            "creators": creators,
        }

    def get_creators(self, page_size: int = 100) -> list[dict[str, Any]]:
        """获取所有创建人及其创建的智能体"""
        apps, _ = self.list_app.list_apps(page_size=page_size)
        return apps

    def get_users(self, page_size: int = 100) -> list[dict[str, Any]]:
        """获取所有用户"""
        users, _ = self.list_user.list_users(page_size=page_size)
        return users