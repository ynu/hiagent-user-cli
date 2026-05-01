"""命令行界面"""

import os
import sys

# Windows 强制 UTF-8 输出 - 必须在任何其他导入之前设置
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    # 设置标准输出/错误的编码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
from inactive_user_cli.email import send_delete_notification


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

        # 如果不是强制模式，则逐个确认
        if not force:
            # 执行删除（逐个确认）
            delete_api = DeleteUserAPI(client)
            records = []

            for i, user in enumerate(inactive_users, 1):
                user_id = user.get("ID", "")
                username = user.get("UserName", "")
                display_name = user.get("DisplayName", "") or "-"

                logger.print_info(f"[{i}/{len(inactive_users)}] 确认删除用户: {username} ({display_name}) [{user_id}]")
                confirm = click.confirm("确认删除？")
                if not confirm:
                    logger.print_info(f"跳过: {username}")
                    continue

                try:
                    delete_api.delete_by_id(user_id)
                    from datetime import datetime, timezone
                    record = DeleteRecord(
                        user_id=user_id,
                        username=username,
                        email=user.get("Email", ""),
                        status="success",
                        deleted_at=datetime.now(timezone.utc).isoformat(),
                        full_info=user,
                    )
                    logger.print_success(f"已删除: {username} ({user_id})")
                except APIError as e:
                    record = DeleteRecord(
                        user_id=user_id,
                        username=username,
                        email=user.get("Email", ""),
                        status="failed",
                        error=str(e),
                        full_info=user,
                    )
                    logger.print_error(f"删除失败: {username} ({user_id}) - {e}")

                records.append(record)

            if not records:
                logger.print_info("没有删除任何用户")
                return
        else:
            # 强制模式 - 批量确认
            confirm = click.confirm("\n确认删除以上所有用户？")
            if not confirm:
                logger.print_info("已取消删除")
                return

            # 执行批量删除
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

                    try:
                        delete_api.delete_by_id(user_id)
                        from datetime import datetime, timezone
                        record = DeleteRecord(
                            user_id=user_id,
                            username=username,
                            email=user.get("Email", ""),
                            status="success",
                            deleted_at=datetime.now(timezone.utc).isoformat(),
                            full_info=user,
                        )
                        logger.print_success(f"已删除: {username} ({user_id})")
                    except APIError as e:
                        record = DeleteRecord(
                            user_id=user_id,
                            username=username,
                            email=user.get("Email", ""),
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

        # 发送邮件通知（如果配置了）
        if config.email and config.email.enabled:
            email_records = [
                {
                    "user_id": r.user_id,
                    "username": r.username,
                    "email": r.email,
                    "status": r.status,
                    "error": r.error or "",
                }
                for r in records
            ]
            try:
                send_delete_notification(
                    config,
                    len(records),
                    success_count,
                    failure_count,
                    str(log_file),
                    email_records,
                )
                logger.print_info("已发送邮件通知")
            except Exception as e:
                logger.print_warning(f"发送邮件通知失败: {e}")

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
        click.echo(f"\n使用 'logs <filename.json>' 查看具体日志")
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
            status_icon = "[green]OK[/green]" if record["status"] == "success" else "[red]FAIL[/red]"
            click.echo(f"  {status_icon} {record['username']} ({record['user_id']})")
            if record.get("error"):
                click.echo(f"      错误: {record['error']}")


if __name__ == "__main__":
    main()