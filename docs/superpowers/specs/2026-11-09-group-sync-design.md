# 用户组管理功能设计（sync-groups）

日期：2026-11-09
状态：已确认

## 目标

为 hiagent-user-cli 增加"定期整理用户组"能力：通过规则脚本定义用户 → 组的映射，
以**增量**方式同步组成员（只添加未加入的、只移除不再匹配的），支持 dry run 和互斥组。

## 用户决策记录

- 同步语义：**添加 + 移除**（整理 = 补齐缺失 + 清理不匹配）
- DSL 格式：**Python 脚本**
- 匹配字段：任意用户字段（UserName / DisplayName / Email / Source / RoleName 等）
- 互斥冲突：**优先级制**（按规则声明顺序取第一个匹配，不报错）
- 移除范围：**仅规则声明的组**（未声明组如访客组、管理员组完全不碰）

## 架构

遵循现有分层（api → core → cli）：

```
api/group.py            GroupAPI（新）
    ├── list_groups()            → ListUserGroup，分页
    ├── list_group_members(id)   → ListGroupMember，分页
    ├── add_members(id, ids)     → CreateGroupMember
    └── remove_members(id, ids)  → RemoveGroupMember

core/group_sync.py      GroupSyncEngine（新）
    ├── load_rules(path)         → 动态加载规则脚本
    ├── compute_changes()        → 计算增量（纯逻辑，易测试）
    └── run(dry_run)             → 执行/预览

cli.py                  sync-groups 命令（新）
```

全部走 iam service / Version=2024-12-25，复用 `APIClient.request` / `paginated_request`。

## 规则脚本协议（Python DSL）

```python
# rules.py 示例
import re

# 可选：互斥组声明 —— 同一集合内用户只能属于一个组
MUTEX_GROUPS = [
    ["学生组", "教师组"],
]

def apply(user: dict) -> str | list[str] | None:
    """返回目标组名（或组名列表），不匹配返回 None。"""
    if re.fullmatch(r"\d{8}", user.get("UserName", "")):
        return "教师组"
    return "学生组"
```

约定：

- 脚本必须定义 `apply(user) -> str | list[str] | None`；缺失或加载失败 → 报错退出
- `MUTEX_GROUPS` 可选；每个集合内的组互斥
- 脚本只写匹配逻辑；增量过滤、互斥仲裁、dry run 全由引擎负责

## 核心算法

1. `ListUserForAdmin` 拉全部用户
2. `ListUserGroup` 拉所有组，按名称解析规则引用的组为 ID；引用不存在的组 → 报错退出
3. 对**规则声明的组**逐个 `ListGroupMember` 拉现有成员（分页）→ 现有成员集合
4. 对每个用户求目标组：返回列表时视为多组归属；互斥集合内按**规则引用顺序**
   （即用户返回组名与集合内组名的匹配顺序）取第一个有效归属，其余丢弃
5. 计算（全部只针对规则声明的组）：
   - **待添加** = 期望成员 − 现有成员（天然过滤已加入用户 → 纯增量）
   - **待移除** = 现有成员 − 期望成员
6. dry run：打印每组的添加/移除表 + 统计，不调写接口
7. 执行：按组批量 `CreateGroupMember` / `RemoveGroupMember`（UserIDs 列表）
8. 结果保存 JSON 日志（`logs` 命令可查看）

## 互斥仲裁细节

- 仅 `MUTEX_GROUPS` 声明的集合生效；未声明组可自由共存
- 用户目标组与互斥集合的交集多于一个时，按**组名在集合中的声明顺序**保留第一个
- 被丢弃的组按普通"不在期望集合"处理 → 若已在其中则会被移除（保证二选一）

## 错误处理与安全

- 非强制模式：显示变更表后 `click.confirm` 确认；dry run 隐含跳过确认
- 单组 API 失败：记录失败继续处理其他组，最后汇总成功/失败数
- `--force` 跳过确认（与现有 delete 命令一致）

## CLI

```bash
uv run inactive-user sync-groups --rules rules.py [--dry-run] [--force]
```

## 测试

- 单测 `compute_changes`（假 client / 注入数据）：增量过滤、互斥优先级、仅处理声明组、
  添加与移除集合计算
- 单测规则加载：合法脚本、缺 apply、语法错误、MUTEX_GROUPS 缺省
- CLI 测试：dry run 不产生写调用（mock 断言）
