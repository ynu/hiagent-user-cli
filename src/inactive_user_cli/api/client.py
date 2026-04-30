"""API 客户端基类 - 封装火山引擎签名逻辑"""

import json
from collections import OrderedDict
from typing import Any

import requests

from volcengine.auth.SignerV4 import SignerV4
from volcengine.auth.SignParam import SignParam
from volcengine.Credentials import Credentials

from inactive_user_cli.config import APIConfig


class APIError(Exception):
    """API 错误"""
    pass


class APIClient:
    """API 客户端基类"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.signer = SignerV4()
        self.base_url = f"http://{config.host}"

    def _build_sign_param(self, action: str) -> SignParam:
        """构建签名参数"""
        param = SignParam()
        param.method = "POST"
        param.host = self.config.host

        query = OrderedDict()
        query["Action"] = action
        query["Version"] = self.config.version
        query["X-Account-Id"] = self.config.account_id
        param.query = query

        header = OrderedDict()
        header["Host"] = self.config.host
        header["Content-Type"] = "application/json"
        param.header_list = header
        param.headers = header

        credentials = Credentials(
            self.config.ak,
            self.config.sk,
            self.config.service,
            self.config.region,
        )
        self.signer.sign(param, credentials)

        return param

    def _build_url(self, action: str) -> str:
        """构建请求 URL"""
        return f"{self.base_url}?Action={action}&Version={self.config.version}&X-Account-Id={self.config.account_id}"

    def request(self, action: str, data: dict[str, Any]) -> dict[str, Any]:
        """发送 API 请求"""
        param = self._build_sign_param(action)
        url = self._build_url(action)

        response = requests.post(
            url,
            headers=param.headers,
            data=json.dumps(data),
            timeout=30,
        )

        if response.status_code != 200:
            raise APIError(f"HTTP {response.status_code}: {response.text}")

        result = response.json()
        if result.get("ResponseMetadata", {}).get("Error"):
            error = result["ResponseMetadata"]["Error"]
            raise APIError(f"API Error: {error.get('Message', 'Unknown error')}")

        return result

    def paginated_request(
        self,
        action: str,
        data: dict[str, Any],
        page_field: str = "PageNumber",
        size_field: str = "PageSize",
        items_field: str = "Items",
        total_field: str = "Total",
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """分页请求，遍历所有数据"""
        all_items: list[dict[str, Any]] = []
        page = 1

        # 设置初始分页参数
        if "ListOpt" not in data:
            data["ListOpt"] = {}
        data["ListOpt"][size_field] = page_size

        while True:
            data["ListOpt"][page_field] = page
            result = self.request(action, data)

            # 提取数据
            resp_data = result.get("Response", result)
            items = resp_data.get(items_field, [])
            all_items.extend(items)

            total = resp_data.get(total_field, 0)
            if page * page_size >= total:
                break

            page += 1

        return all_items, len(all_items)