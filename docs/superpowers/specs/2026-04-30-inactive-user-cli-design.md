# 检测智能体非活跃账号 CLI 工具 - 设计规格

**版本**: 1.0.0
**日期**: 2026-04-30
**状态**: 草稿

---

## 一、项目概述

### 1.1 目标
开发一个基于 Python uv 的 CLI 工具，用于检测并清理智能体平台中从未创建智能体的非活跃用户账号。

### 1.2 核心功能
1. **查看智能体创建人信息** - 调用 `ListApp` 接口获取所有智能体及其创建人
2. **获取平台用户列表** - 调用 `ListUserForAdmin` 接口获取所有平台用户
3. **计算非活跃用户** - 对比筛选出未创建任何智能体的用户
4. **删除非活跃用户** - 调用 `DeleteUser` 接口批量删除非活跃用户
5. **日志管理** - 彩色终端输出 + JSON 格式删除日志持久化

### 1.3 非活跃用户判定标准
- **核心条件**: 用户 ID 不在任何智能体（ListApp）的创建人列表中
- 不检查工作流/插件/知识库等资源，仅以智能体创建记录为依据

---

## 二、技术架构

### 2.1 技术栈
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| Python 版本 | 3.11+ | 需要类型提示支持 |
| 包管理 | uv | 现代 Python 包管理器 |
| CLI 框架 | Click | 命令行应用事实标准 |
| HTTP 客户端 | requests | 与现有签名代码兼容 |
| 配置管理 | python-dotenv | 环境变量加载 |
| 日志输出 | rich | 彩色终端输出 |

### 2.2 项目结构
```
inactive-user-cli/
├── src/
│   └── inactive_user_cli/
│       ├── __init__.py
│       ├── __main__.py       # 包入口点
│       ├── cli.py            # Click 命令定义
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py     # API 客户端基类（签名逻辑）
│       │   ├── app.py        # ListApp 接口
│       │   ├── user.py       # ListUserForAdmin 接口
│       │   └── delete.py     # DeleteUser 接口
│       ├── core/
│       │   ├── __init__.py
│       │   └── analyzer.py   # 非活跃用户分析逻辑
│       ├── config.py         # 配置加载
│       └── logger.py         # 日志管理器
├── tests/
│   └── ...
├── logs/                     # 删除日志输出目录
├── docs/
│   └── api-reference.md      # 接口参考文档
├── .env.example
├── pyproject.toml
├── README.md
├── MIT License
└── .gitignore
```

### 2.3 组件关系图
```
┌─────────────────────────────────────────────────────────────┐
│                         CLI 入口                              │
│                      (cli.py / Click)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     配置加载 (config.py)                       │
│              .env → 环境变量 → API Credentials                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      API 客户端层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  ListApp    │  │ ListUser    │  │  DeleteUser │          │
│  │  (app.py)   │  │  (user.py)  │  │ (delete.py) │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│                   client.py (签名逻辑)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   核心分析器 (analyzer.py)                     │
│         对比创建人列表与用户列表 → 筛选非活跃用户               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     日志管理器 (logger.py)                     │
│            Rich 彩色输出 + JSON 文件持久化                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、API 接口设计

### 3.1 通用签名机制
所有接口调用使用火山引擎签名 v4：
- Header 中添加 `X-Account-Id`
- 请求体为 JSON 格式
- 签名参数：AK、SK、Region、Service

### 3.2 接口列表

| 接口 | Action | 用途 |
|------|--------|------|
| ListApp | `ListApp` | 获取智能体列表（含创建人） |
| ListUserForAdmin | `ListUserForAdmin` | 获取平台用户列表 |
| DeleteUser | `DeleteUser` | 删除指定用户 |

### 3.3 分页处理
- ListApp / ListUserForAdmin 均支持分页
- 工具自动遍历所有页面
- 默认每页 100 条，可配置

---

## 四、CLI 命令设计

### 4.1 命令列表
```bash
# 查看智能体创建人列表
inactive-user list-creators

# 查看平台用户列表
inactive-user list-users

# 分析并列出非活跃用户（预览模式）
inactive-user analyze

# 删除非活跃用户（需确认）
inactive-user delete

# 查看删除日志
inactive-user logs [filename]
```

### 4.2 analyze 命令
```bash
inactive-user analyze [OPTIONS]

选项:
  --output FILE    输出到文件（JSON 格式）
  --dry-run        仅显示统计信息，不执行分析
```

**输出示例**:
```
╭──────────────────────────────────────────────────────────╮
│                    非活跃用户分析报告                      │
├──────────────────┬───────────────────────────────────────┤
│ 总用户数          │ 1,234                                  │
│ 有智能体用户数    │ 456                                    │
│ 非活跃用户数      │ 778                                    │
│ 非活跃占比        │ 63.0%                                  │
╰──────────────────┴───────────────────────────────────────╯

非活跃用户列表:
┌─────────────────────────────────────────────────────────────┐
│ ID        │ 用户名      │ 邮箱                  │ 角色       │
├───────────┼─────────────┼───────────────────────┼───────────┤
│ uid_001   │ test_user   │ test@example.com      │ Member    │
│ uid_002   │ demo_user   │ demo@example.com      │ Visitor   │
└───────────┴─────────────┴───────────────────────┴───────────┘
```

### 4.3 delete 命令
```bash
inactive-user delete [OPTIONS]

选项:
  --user-id TEXT    指定用户 ID（可多次使用）
  --username TEXT   指定用户名（可多次使用）
  --file FILE       从 JSON 文件导入用户列表
  --force           跳过确认直接删除
```

**交互流程**:
1. 显示即将删除的用户列表
2. 提示确认 (`Are you sure you want to delete 10 users? [y/N]`)
3. 确认后执行删除
4. 显示删除结果摘要

---

## 五、日志管理

### 5.1 终端彩色输出
使用 `rich` 库实现：
- 进度条显示 API 分页请求进度
- 表格展示用户列表
- 彩色状态指示（成功=绿色，失败=红色，警告=黄色）

### 5.2 JSON 日志持久化
日志文件保存到 `logs/` 目录，文件名格式：
```
logs/delete_YYYYMMDD_HHMMSS.json
```

**日志结构**:
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
        "user_id": "uid_001",
        "tenant_id": "...",
        "display_name": "...",
        "role_name": "Member",
        "orgs": [...],
        "user_groups": [...]
      }
    },
    {
      "user_id": "uid_002",
      "username": "failed_user",
      "email": "failed@example.com",
      "status": "failed",
      "error": "User is protected",
      "full_info": {...}
    }
  ]
}
```

---

## 六、配置管理

### 6.1 环境变量 (.env)
```bash
# API 配置
API_HOST=10.10.160.222:30040/
API_VERSION=2023-08-01
API_SERVICE=app
API_REGION=cn-north-1
ACCOUNT_ID=1000000000

# 认证凭据（建议使用环境变量而非文件）
API_AK=your_access_key_here
API_SK=your_secret_key_here

# 应用配置
LOG_DIR=logs
DEFAULT_PAGE_SIZE=100
```

### 6.2 .env.example 模板
复制为 `.env` 后填入实际值。

---

## 七、数据流

### 7.1 analyze 流程
```
1. 加载配置 (.env)
         ↓
2. 调用 ListApp (分页获取所有智能体)
         ↓
3. 提取所有唯一的创建人 ID 集合
         ↓
4. 调用 ListUserForAdmin (分页获取所有用户)
         ↓
5. 过滤: user_id NOT IN 创建人集合
         ↓
6. 输出非活跃用户列表 (Rich 表格)
```

### 7.2 delete 流程
```
1. 确认待删除用户列表
         ↓
2. 用户输入 'y' 确认
         ↓
3. 遍历用户列表，逐个调用 DeleteUser
         ↓
4. 记录每个删除操作的结果
         ↓
5. 生成 JSON 日志文件
         ↓
6. 显示删除摘要 (成功数/失败数)
```

---

## 八、错误处理

| 场景 | 处理方式 |
|------|---------|
| API 请求失败 | 重试 3 次，间隔 1s，超时后退出 |
| 签名失败 | 输出错误信息，退出 |
| 用户不存在 | 跳过，记录到失败日志 |
| 无权限删除 | 记录错误，继续下一个 |
| 网络超时 | 重试机制 |

---

## 九、验收标准

- [ ] `list-creators` 命令可正确显示智能体创建人列表
- [ ] `list-users` 命令可正确显示平台用户列表
- [ ] `analyze` 命令正确识别非活跃用户（无智能体创建记录）
- [ ] `delete` 命令可成功删除用户并记录日志
- [ ] 终端输出使用 Rich 彩色显示
- [ ] 删除日志以 JSON 格式保存到 `logs/` 目录
- [ ] 所有敏感配置通过环境变量管理（不硬编码）
- [ ] 代码可通过 `uv build` 打包分发

---

## 十、后续扩展（可选）

- [ ] 支持导出非活跃用户为 CSV
- [ ] 支持增量扫描（记录上次扫描时间）
- [ ] 支持 Webhook 通知删除结果
- [ ] 支持配置文件（YAML）管理多环境