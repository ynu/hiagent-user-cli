"""DeleteUser 接口 - 删除用户"""

from .client import APIClient, APIError


class DeleteUserAPI:
    """DeleteUser 接口封装"""

    ACTION = "DeleteUser"
    # DeleteUser 使用 iam service
    SERVICE = "iam"

    def __init__(self, client: APIClient):
        self.client = client

    def delete_by_id(self, user_id: str) -> bool:
        """
        通过用户 ID 删除用户

        Args:
            user_id: 用户 ID

        Returns:
            是否删除成功
        """
        self.client.request(self.ACTION, {"ID": user_id}, service=self.SERVICE)
        return True

    def delete_by_name(self, username: str) -> bool:
        """
        通过用户名删除用户

        Args:
            username: 用户名

        Returns:
            是否删除成功
        """
        self.client.request(self.ACTION, {"Name": username}, service=self.SERVICE)
        return True