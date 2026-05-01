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
    # Top 参数（可选）
    request_id: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None
    region_key: str | None = None


@dataclass
class EmailConfig:
    """邮件配置"""
    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_addr: str
    to_addrs: list[str]
    use_tls: bool = True


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
    email: EmailConfig | None = None


def load_config() -> Config:
    """从环境变量加载配置"""
    # 加载 .env 文件（如果存在）
    load_dotenv()

    api_config = APIConfig(
        host=getenv("API_HOST", "10.10.160.222:30040"),
        version=getenv("API_VERSION", "2024-12-25"),
        service=getenv("API_SERVICE", "app"),
        region=getenv("API_REGION", "cn-north-1"),
        account_id=getenv("ACCOUNT_ID", "1000000000"),
        ak=getenv("API_AK", ""),
        sk=getenv("API_SK", ""),
        # Top 参数（可选）
        request_id=getenv("API_REQUEST_ID"),
        user_id=getenv("API_USER_ID"),
        tenant_id=getenv("API_TENANT_ID"),
        region_key=getenv("API_REGION_KEY"),
    )

    app_config = AppConfig(
        log_dir=Path(getenv("LOG_DIR", "logs")),
        default_page_size=int(getenv("DEFAULT_PAGE_SIZE", "10000")),
    )

    # 邮件配置（可选）
    email_config = None
    if getenv("EMAIL_ENABLED", "").lower() in ("true", "1", "yes"):
        email_config = EmailConfig(
            enabled=True,
            smtp_host=getenv("EMAIL_SMTP_HOST", ""),
            smtp_port=int(getenv("EMAIL_SMTP_PORT", "587")),
            smtp_user=getenv("EMAIL_SMTP_USER", ""),
            smtp_password=getenv("EMAIL_SMTP_PASSWORD", ""),
            from_addr=getenv("EMAIL_FROM", ""),
            to_addrs=getenv("EMAIL_TO", "").split(","),
            use_tls=getenv("EMAIL_USE_TLS", "true").lower() in ("true", "1", "yes"),
        )

    # 验证必需配置
    if not api_config.ak or not api_config.sk:
        raise ValueError("API_AK and API_SK must be set in environment variables or .env file")

    return Config(api=api_config, app=app_config, email=email_config)