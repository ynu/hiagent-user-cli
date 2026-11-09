"""共享 fixtures"""

import pytest
from unittest.mock import Mock

from inactive_user_cli.api.client import APIClient
from inactive_user_cli.config import APIConfig


@pytest.fixture
def mock_client():
    config = APIConfig(
        host="10.10.160.222:30040/",
        version="2023-08-01",
        service="app",
        region="cn-north-1",
        account_id="1000000000",
        ak="test_ak",
        sk="test_sk",
    )
    client = APIClient(config)
    client.request = Mock()
    client.paginated_request = Mock()
    return client
