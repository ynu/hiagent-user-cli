"""日志管理器 - Rich 彩色输出 + JSON 文件持久化"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


# 禁用 Rich 的 legacy_windows 模式以支持 UTF-8
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

console = Console(legacy_windows=False, force_terminal=True)


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
        table.add_column("创建人ID", style="dim", width=15)
        table.add_column("创建人名称", style="green")
        table.add_column("智能体数量", justify="right", style="yellow")

        # 按创建人ID分组统计，保留 CreateUserName
        creator_stats: dict[str, tuple[int, str]] = {}  # {uid: (count, name)}
        for creator in creators:
            uid = creator.get("CreateUserID", "")
            name = creator.get("CreateUserName", "")
            if uid:
                if uid in creator_stats:
                    creator_stats[uid] = (creator_stats[uid][0] + 1, creator_stats[uid][1])
                else:
                    creator_stats[uid] = (1, name)

        for uid, (count, name) in sorted(creator_stats.items()):
            table.add_row(uid, name or "-", str(count))

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