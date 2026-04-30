# 检测智能体非活跃账号 CLI - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个 Python CLI 工具，用于检测并清理智能体平台中从未创建智能体的非活跃用户账号

**Architecture:** 模块化分层架构，分为 CLI 层、API 层、核心业务层、配置层和日志层。使用 Click 框架构建命令行，Rich 库实现彩色输出，volcengine 签名库处理 API 认证。

**Tech Stack:** Python 3.11+, uv, Click, requests, rich, python-dotenv, volcengine-auth

---

## 文件结构

```
inactive-user-cli/
├── src/inactive_user_cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── logger.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py      # 签名逻辑基类
│   │   ├── app.py         # ListApp 接口
│   │   ├── user.py        # ListUserForAdmin 接口
│   │   └── delete.py      # DeleteUser 接口
│   └── core/
│       ├── __init__.py
│       └── analyzer.py    # 非活跃用户分析
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_analyzer.py
│   └── test_cli.py
├── logs/
├── docs/api-reference.md
├── .env.example
├── pyproject.toml
├── README.md
├── MIT License
└── .gitignore
```

---

## Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/inactive_user_cli/__init__.py`
- Create: `src/inactive_user_cli/__main__.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "inactive-user-cli"
version = "1.0.0"
description = "CLI tool for detecting and cleaning inactive users in AI Agent platform"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Developer"}
]
dependencies = [
    "click>=8.1.0",
    "requests>=2.31.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
inactive-user = "inactive_user_cli.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 2: 创建 .env.example**

```bash
# API 配置
API_HOST=10.10.160.222:30040/
API_VERSION=2023-08-01
API_SERVICE=app
API_REGION=cn-north-1
ACCOUNT_ID=1000000000

# 认证凭据（请使用环境变量或安全 Vault）
API_AK=your_access_key_here
API_SK=your_secret_key_here

# 应用配置
LOG_DIR=logs
DEFAULT_PAGE_SIZE=100
```

- [ ] **Step 3: 创建 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env

# Logs
logs/*.json
logs/*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# uv
.uv/
```

- [ ] **Step 4: 创建 src/inactive_user_cli/__init__.py**

```python
"""Inactive User CLI - 检测并清理智能体平台非活跃用户账号"""

__version__ = "1.0.0"
```

- [ ] **Step 5: 创建 src/inactive_user_cli/__main__.py**

```python
"""包入口点，支持 python -m inactive_user_cli"""

from inactive_user_cli.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Commit**

```bash
git init 2>/dev/null || true
git add pyproject.toml .env.example .gitignore src/inactive_user_cli/
git commit -m "feat: initial project setup with pyproject.toml and basic structure"
```

---

## Task 2: 配置管理模块

**Files:**
- Create: `src/inactive_user_cli/config.py`

- [ ] **Step 1: 创建配置模块**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/inactive_user_cli/config.py
git commit -m "feat: add configuration management module"
```

---

## Task 3: 日志管理器

**Files:**
- Create: `src/inactive_user_cli/logger.py`

- [ ] **Step 1: 创建日志模块**

```python
"""日志管理器 - Rich 彩色输出 + JSON 文件持久化"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()


@dataclass
class DeleteRecord:
    """删除记录"""
    user_id: str
    username: str
    email: str
    status: str
    deleted_at: str | None = None
    error: str | None = None
    full_info: dict[str, Any] | None = None


@dataclass
class DeleteLog:
    """删除日志"""
    version: str = "1.0.0"
    timestamp: str = ""
    operation: str = "delete_users"
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    records: list[dict[str, Any]] | None = None


class LogManager:
    """日志管理器"""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def print_info(self, message: str):
        """打印信息日志"""
        console.print(f"[blue]ℹ[/blue] {message}")

    def print_success(self, message: str):
        """打印成功日志"""
        console.print(f"[green]✓[/green] {message}")

    def print_warning(self, message: str):
        """打印警告日志"""
        console.print(f"[yellow]⚠[/yellow] {message}")

    def print_error(self, message: str):
        """打印错误日志"""
        console.print(f"[red]✗[/red] {message}")

    def print_header(self, message: str):
        """打印标题"""
        console.print(f"\n[bold cyan]{message}[/bold cyan]\n")

    def print_stats(self, total_users: int, active_users: int, inactive_users: int):
        """打印统计信息"""
        inactive_rate = (inactive_users / total_users * 100) if total_users > 0 else 0
        table = Table(title="非活跃用户分析报告", show_header=True, header_style="bold magenta")
        table.add_column("指标", style="cyan")
        table.add_column("数值", justify="right", style="white")

        table.add_row("总用户数", f"{total_users:,}")
        table.add_row("有智能体用户数", f"{active_users:,}")
        table.add_row("非活跃用户数", f"[yellow]{inactive_users:,}[/yellow]")
        table.add_row("非活跃占比", f"[yellow]{inactive_rate:.1f}%[/yellow]")

        console.print(table)

    def print_users_table(self, users: list[dict[str, Any]]):
        """打印用户表格"""
        if not users:
            console.print("[dim]无用户[/dim]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=12)
        table.add_column("用户名", style="green")
        table.add_column("邮箱", style="blue")
        table.add_column("显示名", style="white")
        table.add_column("角色", style="yellow")

        for user in users:
            table.add_row(
                user.get("ID", ""),
                user.get("UserName", ""),
                user.get("Email", "") or "-",
                user.get("DisplayName", "") or "-",
                user.get("RoleName", "") or "-",
            )

        console.print(table)

    def print_creators_table(self, creators: list[dict[str, Any]]):
        """打印创建人表格"""
        if not creators:
            console.print("[dim]无创建人[/dim]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("创建人ID", style="dim", width=12)
        table.add_column("智能体数量", justify="right", style="green")

        # 按创建人ID分组统计
        creator_stats: dict[str, int] = {}
        for creator in creators:
            uid = creator.get("CreateUser", "")
            if uid:
                creator_stats[uid] = creator_stats.get(uid, 0) + 1

        for uid, count in sorted(creator_stats.items()):
            table.add_row(uid, str(count))

        console.print(table)

    def create_progress(self) -> Progress:
        """创建进度条"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )

    def save_delete_log(self, records: list[DeleteRecord]) -> Path:
        """保存删除日志到 JSON 文件"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"delete_{timestamp}.json"

        success_count = sum(1 for r in records if r.status == "success")
        failure_count = len(records) - success_count

        log = DeleteLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_count=len(records),
            success_count=success_count,
            failure_count=failure_count,
            records=[asdict(r) for r in records],
        )

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(asdict(log), f, ensure_ascii=False, indent=2)

        return log_file

    def print_delete_summary(self, log_file: Path, success: int, failed: int):
        """打印删除摘要"""
        table = Table(title="删除结果摘要", show_header=False)
        table.add_column("指标", style="cyan")
        table.add_column("数值", justify="right", style="white")

        table.add_row("成功", f"[green]{success}[/green]")
        table.add_row("失败", f"[red]{failed}[/red]" if failed > 0 else str(failed))
        table.add_row("日志文件", f"[dim]{log_file}[/dim]")

        console.print(table)
```

- [ ] **Step 2: Commit**

```bash
git add src/inactive_user_cli/logger.py
git commit -m "feat: add log manager with rich colored output and JSON persistence"
```

---

## Task 4: API 客户端基类

**Files:**
- Create: `src/inactive_user_cli/api/__init__.py`
- Create: `src/inactive_user_cli/api/client.py`

- [ ] **Step 1: 创建 API 模块初始化文件**

```python
"""API 模块 - 封装火山引擎 API 调用"""

from .client import APIClient
from .app import ListAppAPI
from .user import ListUserAPI
from .delete import DeleteUserAPI

__all__ = ["APIClient", "ListAppAPI", "ListUserAPI", "DeleteUserAPI"]
```

- [ ] **Step 2: 创建 API 客户端基类**

```python
"""API 客户端基类 - 封装火山引擎签名逻辑"""

import json
from collections import OrderedDict
from typing import Any

import requests

from volcengine.auth.SignerV4 import SignerV4
from volcengine.auth.SignParam import SignParam
from volcengine.Credentials import Credentials

from inactive_user_cli.config import APIConfig


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


class APIError(Exception):
    """API 错误"""
    pass
```

- [ ] **Step 3: Commit**

```bash
git add src/inactive_user_cli/api/
git commit -m "feat: add API client base class with volcengine signature"
```

---

## Task 5: ListApp 接口封装

**Files:**
- Create: `src/inactive_user_cli/api/app.py`

- [ ] **Step 1: 创建 ListApp API 封装**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/inactive_user_cli/api/app.py
git commit -m "feat: add ListApp API wrapper"
```

---

## Task 6: ListUserForAdmin 接口封装

**Files:**
- Create: `src/inactive_user_cli/api/user.py`

- [ ] **Step 1: 创建 ListUserForAdmin API 封装**

```python
"""ListUserForAdmin 接口 - 获取平台用户列表"""

from typing import Any

from .client import APIClient


class ListUserAPI:
    """ListUserForAdmin 接口封装"""

    ACTION = "ListUserForAdmin"

    def __init__(self, client: APIClient):
        self.client = client

    def list_users(
        self,
        query: str | None = None,
        status: int | None = None,
        role_name: str | None = None,
        org_id: str | None = None,
        include_visitor: bool = True,
        source: str | None = None,
        contact_search: str | None = None,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取用户列表

        Returns:
            (users, total): 用户列表和总数
        """
        data: dict[str, Any] = {
            "IncludeVisitor": include_visitor,
        }

        if query:
            data["Query"] = query
        if status is not None:
            data["Status"] = status
        if role_name:
            data["RoleName"] = role_name
        if org_id:
            data["OrgID"] = org_id
        if source:
            data["Source"] = source
        if contact_search:
            data["ContactSearch"] = contact_search

        return self.client.paginated_request(
            action=self.ACTION,
            data=data,
            page_field="PageNumber",
            size_field="PageSize",
            items_field="Items",
            total_field="Total",
            page_size=page_size,
        )
```

- [ ] **Step 2: Commit**

```bash
git add src/inactive_user_cli/api/user.py
git commit -m "feat: add ListUserForAdmin API wrapper"
```

---

## Task 7: DeleteUser 接口封装

**Files:**
- Create: `src/inactive_user_cli/api/delete.py`

- [ ] **Step 1: 创建 DeleteUser API 封装**

```python
"""DeleteUser 接口 - 删除用户"""

from typing import Any

from .client import APIClient, APIError


class DeleteUserAPI:
    """DeleteUser 接口封装"""

    ACTION = "DeleteUser"

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
        try:
            self.client.request(self.ACTION, {"ID": user_id})
            return True
        except APIError as e:
            raise APIError(f"Failed to delete user {user_id}: {e}")

    def delete_by_name(self, username: str) -> bool:
        """
        通过用户名删除用户

        Args:
            username: 用户名

        Returns:
            是否删除成功
        """
        try:
            self.client.request(self.ACTION, {"Name": username})
            return True
        except APIError as e:
            raise APIError(f"Failed to delete user {username}: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add src/inactive_user_cli/api/delete.py
git commit -m "feat: add DeleteUser API wrapper"
```

---

## Task 8: 核心分析器

**Files:**
- Create: `src/inactive_user_cli/core/__init__.py`
- Create: `src/inactive_user_cli/core/analyzer.py`

- [ ] **Step 1: 创建核心模块初始化文件**

```python
"""核心业务模块"""

from .analyzer import InactiveUserAnalyzer

__all__ = ["InactiveUserAnalyzer"]
```

- [ ] **Step 2: 创建分析器**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/inactive_user_cli/core/
git commit -m "feat: add inactive user analyzer"
```

---

## Task 9: CLI 命令行

**Files:**
- Create: `src/inactive_user_cli/cli.py`

- [ ] **Step 1: 创建 CLI 模块**

```python
"""命令行界面"""

import sys
from pathlib import Path
from typing import Optional

import click

from inactive_user_cli import __version__
from inactive_user_cli.config import load_config, Config
from inactive_user_cli.logger import LogManager, DeleteRecord
from inactive_user_cli.api.client import APIClient, APIError
from inactive_user_cli.api.app import ListAppAPI
from inactive_user_cli.api.user import ListUserAPI
from inactive_user_cli.api.delete import DeleteUserAPI
from inactive_user_cli.core.analyzer import InactiveUserAnalyzer


def get_config() -> tuple[Config, LogManager, APIClient]:
    """获取配置并初始化组件"""
    try:
        config = load_config()
    except ValueError as e:
        click.echo(f"[red]配置错误: {e}[/red]", err=True)
        sys.exit(1)

    logger = LogManager(config.app.log_dir)
    client = APIClient(config.api)

    return config, logger, client


@click.group()
@click.version_option(version=__version__)
def main():
    """检测智能体非活跃账号 CLI 工具

    用于检测并清理智能体平台中从未创建智能体的非活跃用户账号。
    """
    pass


@main.command("list-creators")
@click.option("--page-size", default=100, help="每页数量")
def list_creators(page_size: int):
    """查看智能体创建人列表"""
    config, logger, client = get_config()
    logger.print_header("智能体创建人列表")

    try:
        list_app = ListAppAPI(client)
        apps, total = list_app.list_apps(page_size=page_size)

        logger.print_info(f"共获取 {total} 个智能体")
        logger.print_creators_table(apps)

    except APIError as e:
        logger.print_error(f"API 请求失败: {e}")
        sys.exit(1)


@main.command("list-users")
@click.option("--page-size", default=100, help="每页数量")
@click.option("--query", default=None, help="搜索关键词")
def list_users(page_size: int, query: Optional[str]):
    """查看平台用户列表"""
    config, logger, client = get_config()
    logger.print_header("平台用户列表")

    try:
        list_user = ListUserAPI(client)
        users, total = list_user.list_users(query=query, page_size=page_size)

        logger.print_info(f"共获取 {total} 个用户")
        logger.print_users_table(users)

    except APIError as e:
        logger.print_error(f"API 请求失败: {e}")
        sys.exit(1)


@main.command("analyze")
@click.option("--page-size", default=100, help="每页数量")
@click.option("--output", type=click.Path(), default=None, help="输出到文件")
def analyze(page_size: int, output: Optional[str]):
    """分析并列出非活跃用户（预览模式）"""
    config, logger, client = get_config()
    logger.print_header("非活跃用户分析")

    try:
        analyzer = InactiveUserAnalyzer(client, logger)
        result = analyzer.analyze(page_size=page_size)

        logger.print_stats(
            total_users=result["total_users"],
            active_users=result["active_users"],
            inactive_users=result["inactive_count"],
        )

        if result["inactive_users"]:
            logger.print_info(f"非活跃用户列表:")
            logger.print_users_table(result["inactive_users"])

            # 输出到文件
            if output:
                import json
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "summary": {
                            "total_users": result["total_users"],
                            "active_users": result["active_users"],
                            "inactive_count": result["inactive_count"],
                        },
                        "inactive_users": result["inactive_users"],
                    }, f, ensure_ascii=False, indent=2)
                logger.print_success(f"已保存到 {output_path}")

    except APIError as e:
        logger.print_error(f"API 请求失败: {e}")
        sys.exit(1)


@main.command("delete")
@click.option("--page-size", default=100, help="每页数量")
@click.option("--force", is_flag=True, help="跳过确认直接删除")
@click.option("--output", type=click.Path(), default=None, help="输出到文件")
def delete(page_size: int, force: bool, output: Optional[str]):
    """删除非活跃用户（需确认）"""
    config, logger, client = get_config()
    logger.print_header("删除非活跃用户")

    try:
        # 分析非活跃用户
        analyzer = InactiveUserAnalyzer(client, logger)
        result = analyzer.analyze(page_size=page_size)
        inactive_users = result["inactive_users"]

        if not inactive_users:
            logger.print_info("没有发现非活跃用户")
            return

        # 显示将要删除的用户
        logger.print_warning(f"即将删除 {len(inactive_users)} 个非活跃用户:")
        logger.print_users_table(inactive_users)

        # 确认删除
        if not force:
            confirm = click.confirm("\n确认删除以上用户？")
            if not confirm:
                logger.print_info("已取消删除")
                return

        # 执行删除
        delete_api = DeleteUserAPI(client)
        records = []

        with logger.create_progress() as progress:
            task = progress.add_task(
                f"[red]删除用户...[/red]",
                total=len(inactive_users),
            )

            for user in inactive_users:
                user_id = user.get("ID", "")
                username = user.get("UserName", "")
                email = user.get("Email", "")

                try:
                    delete_api.delete_by_id(user_id)
                    from datetime import datetime, timezone
                    record = DeleteRecord(
                        user_id=user_id,
                        username=username,
                        email=email,
                        status="success",
                        deleted_at=datetime.now(timezone.utc).isoformat(),
                        full_info=user,
                    )
                    logger.print_success(f"已删除: {username} ({user_id})")
                except APIError as e:
                    record = DeleteRecord(
                        user_id=user_id,
                        username=username,
                        email=email,
                        status="failed",
                        error=str(e),
                        full_info=user,
                    )
                    logger.print_error(f"删除失败: {username} ({user_id}) - {e}")

                records.append(record)
                progress.advance(task)

        # 保存日志
        log_file = logger.save_delete_log(records)
        success_count = sum(1 for r in records if r.status == "success")
        failure_count = len(records) - success_count

        logger.print_delete_summary(log_file, success_count, failure_count)

    except APIError as e:
        logger.print_error(f"API 请求失败: {e}")
        sys.exit(1)


@main.command("logs")
@click.argument("filename", required=False)
@click.option("--dir", "log_dir", type=click.Path(exists=True), default=None, help="日志目录")
def logs(filename: Optional[str], log_dir: Optional[str]):
    """查看删除日志"""
    if log_dir:
        log_path = Path(log_dir)
    else:
        _, logger_instance, _ = get_config()
        log_path = logger_instance.log_dir

    if filename:
        log_file = log_path / filename
        if not log_file.exists():
            click.echo(f"[red]日志文件不存在: {log_file}[/red]", err=True)
            sys.exit(1)
    else:
        # 列出所有日志文件
        log_files = sorted(log_path.glob("delete_*.json"), reverse=True)
        if not log_files:
            click.echo("[yellow]没有找到删除日志[/yellow]")
            return

        click.echo("[cyan]删除日志列表:[/cyan]\n")
        for f in log_files:
            click.echo(f"  {f.name}")
        click.echo(f"\n使用 'logs ' 查看具体日志")
        return

    # 读取并显示日志
    import json
    with open(log_file, encoding="utf-8") as f:
        data = json.load(f)

    click.echo(f"\n[bold]删除日志: {log_file.name}[/bold]\n")
    click.echo(f"时间: {data.get('timestamp', 'N/A')}")
    click.echo(f"操作: {data.get('operation', 'N/A')}")
    click.echo(f"总数: {data.get('total_count', 0)}")
    click.echo(f"成功: [green]{data.get('success_count', 0)}[/green]")
    click.echo(f"失败: [red]{data.get('failure_count', 0)}[/red]\n")

    if data.get("records"):
        click.echo("[cyan]详细记录:[/cyan]")
        for record in data["records"]:
            status_icon = "[green]✓[/green]" if record["status"] == "success" else "[red]✗[/red]"
            click.echo(f"  {status_icon} {record['username']} ({record['user_id']})")
            if record.get("error"):
                click.echo(f"      错误: {record['error']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add src/inactive_user_cli/cli.py
git commit -m "feat: add CLI commands (list-creators, list-users, analyze, delete, logs)"
```

---

## Task 10: 文档和许可证

**Files:**
- Create: `docs/api-reference.md`
- Create: `README.md`
- Create: `MIT License`

- [ ] **Step 1: 创建 API 参考文档**

```markdown
# API 参考文档

本文档描述了检测智能体非活跃账号 CLI 工具所使用的后端 API 接口。

## 接口概述

| 接口 | Action | 用途 |
|------|--------|------|
| ListApp | `ListApp` | 获取智能体列表（含创建人） |
| ListUserForAdmin | `ListUserForAdmin` | 获取平台用户列表 |
| DeleteUser | `DeleteUser` | 删除指定用户 |

## 通用说明

### 认证方式
所有接口使用火山引擎签名 v4 进行认证。

### 请求格式
- Method: POST
- Content-Type: application/json
- URL 参数: Action, Version, X-Account-Id

### 分页
ListApp 和 ListUserForAdmin 接口支持分页，通过 ListOpt 参数控制：
- PageNumber: 页码（从 1 开始）
- PageSize: 每页条数

---

## ListApp - 获取智能体列表

### 请求
```json
{
  "ListOpt": {
    "PageNumber": 1,
    "PageSize": 100
  },
  "Filter": {
    "Keyword": "可选，搜索关键词",
    "AppType": 0,
    "Status": 1,
    "WorkspaceID": "可选，工作空间ID"
  }
}
```

### 响应
```json
{
  "Response": {
    "Items": [
      {
        "AppID": "智能体ID",
        "Name": "智能体名称",
        "Description": "描述",
        "Icon": "图标URL",
        "AppType": 0,
        "Status": 1,
        "CreateTime": "2024-01-01T00:00:00Z",
        "CreateUser": "创建人ID",
        "WorkspaceID": "工作空间ID",
        "IsFavorite": false,
        "PublishStatus": 1
      }
    ],
    "Total": 100
  }
}
```

### AppType 枚举值
| 值 | 说明 |
|----|------|
| 0 | Single - 单Agent模式 |
| 1 | Multi - 多Agent模式 |
| 2 | ChatFlow - 对话流模式 |
| 3 | Workflow - 流程编排模式 |

---

## ListUserForAdmin - 获取用户列表

### 请求
```json
{
  "Query": "可选，搜索关键词",
  "Status": 1,
  "RoleName": "可选，角色名",
  "OrgID": "可选，组织ID",
  "IncludeVisitor": true,
  "Source": "可选，用户来源",
  "ContactSearch": "可选，手机号/邮箱搜索",
  "ListOpt": {
    "PageNumber": 1,
    "PageSize": 100
  }
}
```

### 响应
```json
{
  "Response": {
    "Items": [
      {
        "ID": "用户ID",
        "UserName": "用户名",
        "DisplayName": "显示名",
        "Email": "邮箱",
        "Mobile": "手机号",
        "Source": "用户来源",
        "Status": 1,
        "RoleName": "角色名",
        "TenantID": "租户ID",
        "TenantName": "租户名称",
        "Orgs": [
          {"OrgID": "组织ID", "RoleName": "组织角色"}
        ],
        "UserGroups": [
          {"UserGroupID": "用户组ID", "UserGroupName": "用户组名"}
        ],
        "HasPassword": true,
        "Creator": "创建人",
        "CreatedTime": "2024-01-01T00:00:00Z",
        "UpdatedTime": "2024-01-01T00:00:00Z"
      }
    ],
    "Total": 1000
  }
}
```

---

## DeleteUser - 删除用户

### 请求方式 1: 通过 ID 删除
```json
{
  "ID": "用户ID"
}
```

### 请求方式 2: 通过用户名删除
```json
{
  "Name": "用户名"
}
```

### 响应
无返回内容（成功时返回空响应）

### 错误码
| 错误码 | 说明 |
|--------|------|
| 1001 | 用户不存在 |
| 1002 | 无权限删除 |
| 1003 | 用户受保护无法删除 |

---

## 签名机制

### Python 示例
```python
from volcengine.auth.SignerV4 import SignerV4
from volcengine.auth.SignParam import SignParam
from volcengine.Credentials import Credentials
from collections import OrderedDict
import requests
import json

# 配置
ak = "your_access_key"
sk = "your_secret_key"
region = "cn-north-1"
service = "app"
host = "10.10.160.222:30040/"
action = "ListApp"
version = "2023-08-01"
account_id = "1000000000"

# 签名
signer = SignerV4()
param = SignParam()
param.method = "POST"
param.host = host

query = OrderedDict()
query["Action"] = action
query["Version"] = version
query["X-Account-Id"] = account_id
param.query = query

header = OrderedDict()
header["Host"] = host
header["Content-Type"] = "application/json"
param.header_list = header
param.headers = header

credentials = Credentials(ak, sk, service, region)
signer.sign(param, credentials)

# 发送请求
url = f"http://{host}?Action={action}&Version={version}&X-Account-Id={account_id}"
data = {"ListOpt": {"PageNumber": 1, "PageSize": 100}}
response = requests.post(url, headers=param.headers, data=json.dumps(data))
```
```

- [ ] **Step 2: 创建 README.md**

```markdown
# Inactive User CLI

检测并清理智能体平台中从未创建智能体的非活跃用户账号的 CLI 工具。

## 功能特性

- **查看智能体创建人** - 获取平台上所有智能体的创建人列表
- **查看平台用户** - 获取所有平台用户信息
- **分析非活跃用户** - 智能识别从未创建智能体的用户
- **批量删除** - 安全删除非活跃用户（先预览后确认）
- **日志记录** - JSON 格式删除日志，支持追溯

## 技术方案

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI 入口 (Click)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      配置层 (python-dotenv)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      API 层 (火山引擎 SDK)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  ListApp    │  │ ListUser    │  │  DeleteUser │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   核心分析器 (InactiveUserAnalyzer)           │
│         对比创建人列表与用户列表 → 筛选非活跃用户              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     日志层 (Rich + JSON)                      │
└─────────────────────────────────────────────────────────────┘
```

### 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| Python 版本 | 3.11+ | 现代 Python 特性支持 |
| 包管理 | uv | 高性能 Python 包管理 |
| CLI 框架 | Click | 事实标准的 Python CLI 框架 |
| HTTP 客户端 | requests | 兼容火山引擎签名逻辑 |
| 终端输出 | Rich | 彩色终端和表格展示 |
| 配置管理 | python-dotenv | 环境变量加载 |
| API 认证 | volcengine-auth | 火山引擎签名 v4 |

### 非活跃用户判定逻辑

```
1. 调用 ListApp 接口，获取所有智能体及其创建人 (CreateUser)
2. 提取所有唯一的创建人 ID，组成「活跃用户」集合
3. 调用 ListUserForAdmin 接口，获取所有平台用户
4. 过滤：用户 ID 不在「活跃用户」集合中 → 非活跃用户
5. 对比结果展示，确认后调用 DeleteUser 删除
```

### API 调用流程

```python
# 1. 获取智能体创建人
apps = list_app_api.list_apps()
creators = {app["CreateUser"] for app in apps}

# 2. 获取平台用户
users = list_user_api.list_users()

# 3. 筛选非活跃用户
inactive_users = [u for u in users if u["ID"] not in creators]

# 4. 确认后删除
for user in inactive_users:
    delete_user_api.delete_by_id(user["ID"])
```

## 安装

### 环境要求

- Python 3.11+
- uv 包管理器

### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd inactive-user-cli

# 使用 uv 安装依赖
uv sync

# 安装为全局命令
uv pip install -e .
```

或者使用 pipx：

```bash
uv pip install -e .
```

## 配置

### 环境变量

复制 `.env.example` 为 `.env`，配置以下变量：

```bash
# API 配置
API_HOST=10.10.160.222:30040/
API_VERSION=2023-08-01
API_SERVICE=app
API_REGION=cn-north-1
ACCOUNT_ID=1000000000

# 认证凭据（必需）
API_AK=your_access_key_here
API_SK=your_secret_key_here

# 应用配置
LOG_DIR=logs
DEFAULT_PAGE_SIZE=100
```

### 安全性建议

- 不要将 `.env` 文件提交到版本控制系统
- 生产环境建议使用环境变量而非 `.env` 文件
- API AK/SK 建议定期轮换

## 使用

### 查看智能体创建人

```bash
inactive-user list-creators
```

输出示例：
```
╭──────────────────────────────────────────────────────────────╮
│                    智能体创建人列表                           │
╰──────────────────────────────────────────────────────────────╯

ℹ 获取到 150 个智能体

┌────────────┬──────────────┐
│ 创建人ID   │ 智能体数量   │
├────────────┼──────────────┤
│ uid_001    │ 5            │
│ uid_002    │ 3            │
│ uid_003    │ 2            │
└────────────┴──────────────┘
```

### 查看平台用户

```bash
inactive-user list-users
```

### 分析非活跃用户

```bash
# 默认分析
inactive-user analyze

# 输出到文件
inactive-user analyze --output inactive_users.json
```

输出示例：
```
╭──────────────────────────────────────────────────────────╮
│                    非活跃用户分析报告                      │
├──────────────────┬───────────────────────────────────────┤
│ 总用户数          │ 1,234                                  │
│ 有智能体用户数    │ 456                                    │
│ 非活跃用户数      │ 778                                    │
│ 非活跃占比        │ 63.0%                                  │
╰──────────────────┴───────────────────────────────────────╯

ℹ 非活跃用户列表:
┌────────────┬────────────┬───────────────────┬─────────────┐
│ ID         │ 用户名     │ 邮箱              │ 角色        │
├────────────┼────────────┼───────────────────┼─────────────┤
│ uid_1001   │ test_user  │ test@example.com  │ Member      │
│ uid_1002   │ demo_user  │ demo@example.com  │ Visitor     │
└────────────┴────────────┴───────────────────┴─────────────┘
```

### 删除非活跃用户

```bash
# 交互式确认删除
inactive-user delete

# 跳过确认直接删除（慎用）
inactive-user delete --force
```

删除流程：
1. 显示分析结果和非活跃用户列表
2. 提示确认删除
3. 逐个删除用户
4. 生成删除日志

### 查看删除日志

```bash
# 列出所有日志
inactive-user logs

# 查看指定日志
inactive-user logs delete_20260430_153000.json
```

## 日志格式

删除日志保存在 `logs/` 目录，格式如下：

```json
{
  "version": "1.0.0",
  "timestamp": "2026-04-30T15:30:00+08:00",
  "operation": "delete_users",
  "total_count": 10,
  "success_count": 9,
  "failure_count": 1,
  "records": [
    {
      "user_id": "uid_001",
      "username": "test_user",
      "email": "test@example.com",
      "status": "success",
      "deleted_at": "2026-04-30T15:30:05+08:00",
      "full_info": {
        "ID": "uid_001",
        "UserName": "test_user",
        "DisplayName": "Test User",
        "Email": "test@example.com",
        "RoleName": "Member",
        "TenantID": "tenant_001",
        "TenantName": "Default Tenant"
      }
    }
  ]
}
```

## 开发

### 运行测试

```bash
uv run pytest
```

### 代码格式化

```bash
uv run ruff format .
```

### 类型检查

```bash
uv run mypy src/
```

## 项目结构

```
inactive-user-cli/
├── src/inactive_user_cli/
│   ├── __init__.py           # 包初始化
│   ├── __main__.py           # 包入口
│   ├── cli.py                # CLI 命令定义
│   ├── config.py             # 配置管理
│   ├── logger.py             # 日志管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py         # API 客户端基类
│   │   ├── app.py            # ListApp 接口
│   │   ├── user.py           # ListUserForAdmin 接口
│   │   └── delete.py         # DeleteUser 接口
│   └── core/
│       ├── __init__.py
│       └── analyzer.py       # 非活跃用户分析
├── tests/
├── docs/
│   └── api-reference.md
├── logs/                     # 删除日志目录
├── .env.example
├── pyproject.toml
├── README.md
├── MIT License
└── .gitignore
```

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT License - 详见 [MIT License](MIT License)
```

- [ ] **Step 3: 创建 MIT License**

```markdown
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Commit**

```bash
git add docs/api-reference.md README.md "MIT License"
git commit -m "docs: add API reference, README and MIT License"
```

---

## Task 11: 测试文件

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_api_client.py`
- Create: `tests/test_analyzer.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 创建测试初始化文件**

```python
"""测试包"""
```

- [ ] **Step 2: 创建 API 客户端测试**

```python
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
```

- [ ] **Step 3: 创建分析器测试**

```python
"""分析器测试"""

import pytest
from unittest.mock import Mock, MagicMock

from inactive_user_cli.core.analyzer import InactiveUserAnalyzer
from inactive_user_cli.api.client import APIClient
from inactive_user_cli.logger import LogManager
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
    return APIClient(config)


@pytest.fixture
def mock_logger():
    return Mock(spec=LogManager)


@pytest.fixture
def analyzer(mock_client, mock_logger):
    return InactiveUserAnalyzer(mock_client, mock_logger)


class TestInactiveUserAnalyzer:
    """InactiveUserAnalyzer 测试"""

    def test_init(self, analyzer, mock_client, mock_logger):
        """测试初始化"""
        assert analyzer.client == mock_client
        assert analyzer.logger == mock_logger

    def test_analyze_empty(self, analyzer, mock_client):
        """测试空数据分析"""
        # Mock 分页请求
        mock_client.paginated_request = Mock(return_value=([], 0))

        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 0
        assert result["active_users"] == 0
        assert result["inactive_count"] == 0
        assert result["inactive_users"] == []

    def test_analyze_all_active(self, analyzer, mock_client):
        """测试所有用户都是活跃用户"""
        apps = [
            {"CreateUser": "user_001"},
            {"CreateUser": "user_002"},
        ]
        users = [
            {"ID": "user_001", "UserName": "User 1"},
            {"ID": "user_002", "UserName": "User 2"},
        ]

        mock_client.paginated_request = Mock(side_effect=[(apps, 2), (users, 2)])
        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 2
        assert result["active_users"] == 2
        assert result["inactive_count"] == 0
        assert result["inactive_users"] == []

    def test_analyze_mixed(self, analyzer, mock_client):
        """测试混合用户（活跃和非活跃）"""
        apps = [
            {"CreateUser": "user_001"},
        ]
        users = [
            {"ID": "user_001", "UserName": "Active User"},
            {"ID": "user_002", "UserName": "Inactive User"},
            {"ID": "user_003", "UserName": "Another Inactive"},
        ]

        mock_client.paginated_request = Mock(side_effect=[(apps, 1), (users, 3)])
        result = analyzer.analyze(page_size=100)

        assert result["total_users"] == 3
        assert result["active_users"] == 1
        assert result["inactive_count"] == 2
        assert len(result["inactive_users"]) == 2

        inactive_ids = {u["ID"] for u in result["inactive_users"]}
        assert "user_002" in inactive_ids
        assert "user_003" in inactive_ids
        assert "user_001" not in inactive_ids
```

- [ ] **Step 4: 创建 CLI 测试**

```python
"""CLI 测试"""

import pytest
from click.testing import CliRunner

from inactive_user_cli.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    """CLI 测试"""

    def test_version(self, runner):
        """测试版本命令"""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "inactive-user-cli" in result.output.lower()

    def test_help(self, runner):
        """测试帮助命令"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "list-creators" in result.output
        assert "list-users" in result.output
        assert "analyze" in result.output
        assert "delete" in result.output

    def test_list_creators_command_exists(self, runner):
        """测试 list-creators 命令存在"""
        result = runner.invoke(main, ["list-creators", "--help"])
        assert result.exit_code == 0

    def test_list_users_command_exists(self, runner):
        """测试 list-users 命令存在"""
        result = runner.invoke(main, ["list-users", "--help"])
        assert result.exit_code == 0

    def test_analyze_command_exists(self, runner):
        """测试 analyze 命令存在"""
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0

    def test_delete_command_exists(self, runner):
        """测试 delete 命令存在"""
        result = runner.invoke(main, ["delete", "--help"])
        assert result.exit_code == 0

    def test_logs_command_exists(self, runner):
        """测试 logs 命令存在"""
        result = runner.invoke(main, ["logs", "--help"])
        assert result.exit_code == 0
```

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: add unit tests for API client, analyzer and CLI"
```

---

## 验收检查清单

- [ ] Task 1: 项目初始化完成 (pyproject.toml, .env.example, .gitignore)
- [ ] Task 2: 配置管理模块完成
- [ ] Task 3: 日志管理器完成 (Rich 彩色输出 + JSON)
- [ ] Task 4: API 客户端基类完成 (火山引擎签名)
- [ ] Task 5: ListApp 接口封装完成
- [ ] Task 6: ListUserForAdmin 接口封装完成
- [ ] Task 7: DeleteUser 接口封装完成
- [ ] Task 8: 核心分析器完成
- [ ] Task 9: CLI 命令完成
- [ ] Task 10: 文档和许可证完成
- [ ] Task 11: 测试文件完成
- [ ] README 中技术实现方案完整

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-inactive-user-cli-plan.md`**

## 执行选择

**1. Subagent-Driven (推荐)** - 每个 Task 由独立 subagent 执行，任务间有检查点

**2. Inline Execution** - 当前会话内批量执行，阶段性检查

选择哪种方式？