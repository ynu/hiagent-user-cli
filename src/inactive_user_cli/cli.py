"""CLI 入口模块"""

import click
from inactive_user_cli import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Inactive User CLI - 检测并清理智能体平台非活跃用户账号"""
    pass


if __name__ == "__main__":
    main()