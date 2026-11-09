# 用户组同步规则脚本示例
# 复制为 rules.py 后修改，运行:
#   uv run inactive-user sync-groups --rules rules.py --dry-run
#
# 必须定义: apply(user) -> 组名(str) / 组名列表(list[str]) / None
# 可选定义: MUTEX_GROUPS - 互斥组集合，同一集合内用户只能属于一个组，
#           同时命中多个时按声明顺序保留第一个

import re

MUTEX_GROUPS = [
    ["学生组", "教师组"],
]


def apply(user):
    """根据用户属性决定目标组，不匹配返回 None"""
    # 用户名是 8 位数字 → 教师组
    if re.fullmatch(r"\d{8}", user.get("UserName", "")):
        return "教师组"
    # 邮箱包含 @stu. → 学生组
    # email = user.get("Email", "") or ""
    # if "@stu." in email:
    #     return "学生组"
    # 不匹配任何组
    return "学生组"
