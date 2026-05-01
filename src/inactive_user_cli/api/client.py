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

    # 默认 service（ListApp 使用 app）
    DEFAULT_SERVICE = "app"
    # ListApp 专用版本
    APP_VERSION = "2023-08-01"
    # ListUser/DeleteUser 版本
    IAM_VERSION = "2024-12-25"

    def __init__(self, config: APIConfig):
        self.config = config
        self.signer = SignerV4()
        self.base_url = f"http://{config.host}"

    def _build_sign_param(self, action: str, service: str | None = None, version: str | None = None) -> SignParam:
        """构建签名参数

        Args:
            action: API Action
            service: 服务名称（可选，默认使用 DEFAULT_SERVICE）
            version: API 版本（可选，默认使用配置版本）
        """
        param = SignParam()
        param.method = "POST"
        param.host = self.config.host

        # 使用指定的 version 或配置的 version
        actual_version = version or self.config.version

        query = OrderedDict()
        query["Action"] = action
        query["Version"] = actual_version
        query["X-Account-Id"] = self.config.account_id
        param.query = query

        header = OrderedDict()
        header["Host"] = self.config.host
        header["Content-Type"] = "application/json"
        param.header_list = header
        param.headers = header

        # 使用指定的 service 或默认 service
        actual_service = service or self.DEFAULT_SERVICE
        credentials = Credentials(
            self.config.ak,
            self.config.sk,
            actual_service,
            self.config.region,
        )
        self.signer.sign(param, credentials)

        return param

    def _build_url(self, action: str, version: str | None = None) -> str:
        """构建请求 URL

        Args:
            action: API Action
            version: API 版本（可选）
        """
        actual_version = version or self.config.version
        return f"{self.base_url}?Action={action}&Version={actual_version}&X-Account-Id={self.config.account_id}"

    def request(self, action: str, data: dict[str, Any], service: str | None = None, version: str | None = None) -> dict[str, Any]:
        """发送 API 请求

        Args:
            action: API Action
            data: 请求数据
            service: 服务名称（可选，默认使用 DEFAULT_SERVICE）
            version: API 版本（可选）
        """
        # 序列化 body 用于签名
        body_json = json.dumps(data)

        # 构建签名参数并设置 body
        param = self._build_sign_param(action, service, version)
        param.body = body_json

        # 重新签名（包含 body）
        actual_service = service or self.DEFAULT_SERVICE
        credentials = Credentials(
            self.config.ak,
            self.config.sk,
            actual_service,
            self.config.region,
        )
        self.signer.sign(param, credentials)

        url = self._build_url(action, version)

        response = requests.post(
            url,
            headers=param.headers,
            data=body_json,
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
        page_size: int = 10000,
        service: str | None = None,
        version: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """分页请求，遍历所有数据

        Args:
            action: API Action
            data: 请求数据
            page_field: 页数字段名
            size_field: 每页大小字段名
            items_field: 数据项字段名
            total_field: 总数字段名
            page_size: 每页大小（默认 10000）
            service: 服务名称（可选，默认使用 DEFAULT_SERVICE）
            version: API 版本（可选）
        """
        all_items: list[dict[str, Any]] = []
        page = 1

        # 设置初始分页参数
        if "ListOpt" not in data:
            data["ListOpt"] = {}
        data["ListOpt"][size_field] = page_size

        while True:
            data["ListOpt"][page_field] = page
            result = self.request(action, data, service, version)

            # 提取数据 - 兼容 Result 和 Response
            resp_data = result.get("Result", result.get("Response", result))
            items = resp_data.get(items_field, [])
            all_items.extend(items)

            total = resp_data.get(total_field, 0)
            if page * page_size >= total:
                break

            page += 1

        return all_items, len(all_items)