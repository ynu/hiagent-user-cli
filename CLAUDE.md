# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

HiAgent User CLI - 智能体平台非活跃用户检测与清理工具，用于识别并删除从未创建智能体的非活跃账号。

## 常用命令

```bash
# 安装依赖
uv sync

# 运行命令
uv run inactive-user --help
uv run inactive-user analyze [--include-visitor]
uv run inactive-user delete [--include-visitor] --force
uv run inactive-user list-creators
uv run inactive-user list-users
uv run inactive-user logs

# 运行测试
uv run pytest
uv run pytest tests/test_cli.py::test_analyze  # 单个测试
```

## 配置

从 `.env` 文件加载配置（复制 `.env.example`），必需的环境变量：
- `API_HOST` - API 端点地址
- `API_VERSION` - API 版本号
- `API_REGION` - 服务区域
- `ACCOUNT_ID` - 账号 ID
- `API_AK` / `API_SK` - 访问密钥

## 架构

```
cli.py (Click 命令层)
    └── InactiveUserAnalyzer (核心分析逻辑)
            ├── ListAppAPI (获取智能体创建人)
            ├── ListUserAPI (获取平台用户)
            └── DeleteUserAPI (删除用户)

APIClient (API 客户端基类)
    └── 封装火山引擎 Signature V4 签名逻辑
    └── 提供分页请求支持
```

**核心逻辑**：非活跃用户 = 平台用户 - 智能体创建人集合（即从未创建过任何智能体的用户）

## 技术栈

- **CLI**: Click
- **API**: requests + volcengine SDK
- **输出**: Rich (彩色终端表格)
- **配置**: python-dotenv
- **测试**: pytest

## Windows 兼容性

`cli.py` 强制设置 UTF-8 编码以支持中文输出。