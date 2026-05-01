# HiAgent User CLI

智能体平台非活跃用户检测与清理工具。

## 功能特性

- **预览分析** - 识别从未创建智能体的用户
- **批量清理** - 安全删除非活跃账号，支持逐个确认
- **操作日志** - JSON 格式完整记录删除操作
- **邮件通知** - 可选配置，删除完成后自动发送报告

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 API 凭证
```

### 3. 运行命令

```bash
uv run inactive-user --help
```

## 命令参考

### analyze - 分析非活跃用户

预览分析模式下查看所有从未创建智能体的用户。

```bash
uv run inactive-user analyze [--page-size N] [--output FILE]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |
| `--output` | path | 输出到 JSON 文件 |

**示例:**

```bash
# 分析非活跃用户
uv run inactive-user analyze

# 输出到文件
uv run inactive-user analyze --output inactive_users.json

# 大数据量场景
uv run inactive-user analyze --page-size 10000
```

### delete - 删除非活跃用户

删除操作需要确认，使用 `--force` 跳过确认直接执行。

```bash
uv run inactive-user delete [--page-size N] [--force] [--output FILE]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |
| `--force` | flag | 跳过确认，直接删除 |
| `--output` | path | 输出到 JSON 文件 |

**示例:**

```bash
# 交互模式：逐个确认删除
uv run inactive-user delete

# 批量确认模式
uv run inactive-user delete --force

# 删除后输出分析结果
uv run inactive-user delete --force --output delete_report.json
```

### list-creators - 智能体创建人列表

查看平台中创建过智能体的用户及其创建数量。

```bash
uv run inactive-user list-creators [--page-size N]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |

**示例:**

```bash
uv run inactive-user list-creators
```

### list-users - 平台用户列表

查看平台所有用户，支持关键词搜索。

```bash
uv run inactive-user list-users [--page-size N] [--query KEYWORD]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |
| `--query` | text | 搜索关键词 |

**示例:**

```bash
# 查看所有用户
uv run inactive-user list-users

# 搜索用户
uv run inactive-user list-users --query "张三"
```

### logs - 删除日志

查看历史删除操作的详细记录。

```bash
uv run inactive-user logs [FILENAME] [--dir PATH]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `FILENAME` | text | 日志文件名 |
| `--dir` | path | 日志目录路径 |

**示例:**

```bash
# 列出所有日志
uv run inactive-user logs

# 查看指定日志
uv run inactive-user logs delete_2024-01-01.json
```

## 配置说明

### 环境变量

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `API_HOST` | 10.10.160.222:30040 | 是 | API 端点地址 |
| `API_VERSION` | 2024-12-25 | 是 | API 版本号 |
| `API_REGION` | cn-north-1 | 是 | 服务区域 |
| `ACCOUNT_ID` | 1000000000 | 是 | 账号 ID |
| `API_AK` | - | 是 | 访问密钥 |
| `API_SK` | - | 是 | 密钥 |
| `LOG_DIR` | logs | 否 | 日志目录 |
| `DEFAULT_PAGE_SIZE` | 10000 | 否 | 默认分页大小 |

### Top 参数（可选）

| 变量 | 说明 |
|------|------|
| `API_REQUEST_ID` | 请求 ID |
| `API_USER_ID` | 用户 ID |
| `API_TENANT_ID` | 租户 ID |
| `API_REGION_KEY` | 区域标识 |

### 邮件通知（可选）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EMAIL_ENABLED` | false | 启用邮件通知 |
| `EMAIL_SMTP_HOST` | - | SMTP 服务器 |
| `EMAIL_SMTP_PORT` | 587 | SMTP 端口 |
| `EMAIL_SMTP_USER` | - | 发件人账号 |
| `EMAIL_SMTP_PASSWORD` | - | 发件人密码 |
| `EMAIL_FROM` | - | 发件人地址 |
| `EMAIL_TO` | - | 收件人地址（逗号分隔） |
| `EMAIL_USE_TLS` | true | 启用 TLS |

## 安全机制

- **签名认证** - 所有 API 请求使用 Volcengine Signature V4
- **确认机制** - 删除操作默认逐个确认，可选 `--force` 跳过
- **操作日志** - 所有删除操作完整记录到 JSON 文件
- **凭据保护** - API 密钥仅通过环境变量或 .env 文件加载

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI 层                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Click Commands                     │   │
│  │  list-creators  list-users  analyze  delete  logs   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        核心层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              InactiveUserAnalyzer                    │   │
│  │  计算差集：平台用户 - 智能体创建人 = 非活跃用户        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        API 层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  ListAppAPI  │  │  ListUserAPI │  │ DeleteUserAPI│     │
│  │  service=app │  │ service=iam  │  │ service=iam  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 检测逻辑

非活跃用户定义：**从未创建过任何智能体的账号**

```
非活跃用户 = 平台用户 ∩ (平台用户 - 智能体创建人集合)
```

此规则确保已创建智能体的用户即使长时间未登录也不会被误删。

## 项目结构

```
hiagent-user-cli/
├── src/inactive_user_cli/
│   ├── __init__.py          # 版本信息
│   ├── cli.py               # CLI 命令入口
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志输出
│   ├── email.py             # 邮件通知
│   └── api/
│       ├── client.py        # API 客户端
│       ├── app.py           # 智能体 API
│       ├── user.py          # 用户 API
│       ├── delete.py        # 删除 API
│       └── response.py      # 响应处理
├── tests/                   # 单元测试
├── docs/                    # 文档资料
├── .env.example             # 配置示例
└── pyproject.toml           # 项目配置
```

## License

MIT