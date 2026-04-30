"""API 客户端测试"""

import pytest
from unittest.mock import Mock, patch

from inactive_user_cli.api.client import APIClient, APIError
from inactive_user_cli.config import APIConfig


@pytest.fixture
def api_config():
    return APIConfig(
        host="10.10.160.222:30040/",
        version="2023-08-01",
        service="app",
        region="cn-north-1",
        account_id="1000000000",
        ak="test_ak",
        sk="test_sk",
    )


@pytest.fixture
def api_client(api_config):
    return APIClient(api_config)


class TestAPIClient:
    """APIClient 测试"""

    def test_init(self, api_client, api_config):
        """测试初始化"""
        assert api_client.config == api_config
        assert api_client.base_url == "http://10.10.160.222:30040/"

    def test_build_url(self, api_client):
        """测试 URL 构建"""
        url = api_client._build_url("ListApp")
        assert "Action=ListApp" in url
        assert "Version=2023-08-01" in url
        assert "X-Account-Id=1000000000" in url

    @patch("inactive_user_cli.api.client.requests.post")
    def test_request_success(self, mock_post, api_client):
        """测试成功请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ResponseMetadata": {},
            "Response": {"Items": [], "Total": 0}
        }
        mock_post.return_value = mock_response

        result = api_client.request("ListApp", {})
        assert "Response" in result

    @patch("inactive_user_cli.api.client.requests.post")
    def test_request_http_error(self, mock_post, api_client):
        """测试 HTTP 错误"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            api_client.request("ListApp", {})
        assert "HTTP 500" in str(exc_info.value)

    @patch("inactive_user_cli.api.client.requests.post")
    def test_request_api_error(self, mock_post, api_client):
        """测试 API 错误"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ResponseMetadata": {
                "Error": {"Message": "Invalid parameters"}
            }
        }
        mock_post.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            api_client.request("ListApp", {})
        assert "Invalid parameters" in str(exc_info.value)