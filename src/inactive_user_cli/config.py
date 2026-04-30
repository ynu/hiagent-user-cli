"""配置管理模块 - 从环境变量加载配置"""

from dataclasses import dataclass
from os import getenv
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """API 配置"""
    host: str
    version: str
    service: str
    region: str
    account_id: str
    ak: str
    sk: str


@dataclass
class AppConfig:
    """应用配置"""
    log_dir: Path
    default_page_size: int


@dataclass
class Config:
    """全局配置"""
    api: APIConfig
    app: AppConfig


def load_config() -> Config:
    """从环境变量加载配置"""
    # 加载 .env 文件（如果存在）
    load_dotenv()

    api_config = APIConfig(
        host=getenv("API_HOST", "10.10.160.222:30040/"),
        version=getenv("API_VERSION", "2023-08-01"),
        service=getenv("API_SERVICE", "app"),
        region=getenv("API_REGION", "cn-north-1"),
        account_id=getenv("ACCOUNT_ID", "1000000000"),
        ak=getenv("API_AK", ""),
        sk=getenv("API_SK", ""),
    )

    app_config = AppConfig(
        log_dir=Path(getenv("LOG_DIR", "logs")),
        default_page_size=int(getenv("DEFAULT_PAGE_SIZE", "100")),
    )

    # 验证必需配置
    if not api_config.ak or not api_config.sk:
        raise ValueError("API_AK and API_SK must be set in environment variables or .env file")

    return Config(api=api_config, app=app_config)