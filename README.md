# HiAgent User CLI

智能体平台非活跃用户检测与清理工具。

## 功能特性

- **预览分析** - 识别从未创建智能体的用户，排除空间管理员
- **批量清理** - 安全删除非活跃账号，支持逐个确认
- **操作日志** - JSON 格式完整记录删除操作
- **邮件通知** - 可选配置，删除完成后自动发送报告
- **空间管理** - 显示团队空间管理员和工作空间信息

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

### analyze - 分析用户

分析平台用户，访客单独统计，非访客区分活跃/非活跃，同时排除空间管理员。

**分析报告包含：**
- 用户统计（总用户数、活跃/非活跃用户数、访客数）
- 非活跃用户列表
- 团队空间管理员列表
- 团队工作空间列表

```bash
uv run inactive-user analyze [--page-size N] [--output FILE]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |
| `--output` | path | 输出到 JSON 文件 |

**示例:**

```bash
uv run inactive-user analyze
uv run inactive-user analyze --output report.json
```

**输出示例:**

```
用户分析报告
┏━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ 指标           ┃ 数值  ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ 总用户数       │  261  │
│ 普通用户数     │  258  │
│   - 活跃用户   │  100  │
│   - 非活跃用户 │  158  │
│   - 非活跃占比 │ 61.2% │
│ 访客用户数     │    3  │
│ 团队空间管理员数│   17  │
└────────────────┴───────┘

普通非活跃用户列表:
[用户表格...]

团队空间管理员列表:
[管理员表格...]

团队工作空间列表:
[工作空间表格...]
```

### delete - 删除用户

- `--only-visitor`: 删除所有访客用户（不区分活跃状态）
- 默认：删除普通用户（非访客）中的非活跃用户

```bash
uv run inactive-user delete [--page-size N] [--only-visitor] [--force] [--output FILE]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |
| `--only-visitor` | flag | 删除所有访客用户 |
| `--force` | flag | 跳过确认，直接删除 |
| `--output` | path | 输出到 JSON 文件 |

**示例:**

```bash
# 交互模式：逐个确认删除非活跃用户
uv run inactive-user delete

# 删除所有访客用户（不区分活跃状态）
uv run inactive-user delete --only-visitor --force

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

查看平台所有用户（默认包含访客），支持关键词搜索。

```bash
uv run inactive-user list-users [--page-size N] [--query KEYWORD] [--include-visitor]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--page-size` | integer | 每页数量，默认 100 |
| `--query` | text | 搜索关键词 |
| `--include-visitor` | flag | 包含访客用户（默认开启） |

**示例:**

```bash
uv run inactive-user list-users
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
│  │  计算差集：平台用户 - 智能体创建人 - 空间管理员        │   │
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
│  ┌──────────────────────────────┐                         │
│  │   ListWorkspaceAPI (空间管理) │                         │
│  │   service=iam                │                         │
│  └──────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 检测逻辑

非活跃用户定义：**从未创建过任何智能体的账号，且不是团队空间管理员**

```
非活跃用户 = 平台用户 ∩ (平台用户 - 智能体创建人集合 - 空间管理员集合)
```

此规则确保：
1. 已创建智能体的用户即使长时间未登录也不会被误删
2. 团队空间管理员即使未创建智能体也不会被误删（需要参与工作空间管理）

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
│       └── workspace.py     # 工作空间 API
├── tests/                   # 单元测试
├── docs/                    # 文档资料
├── .env.example             # 配置示例
└── pyproject.toml           # 项目配置
```

## License

MIT