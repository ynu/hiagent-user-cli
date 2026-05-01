"""包入口点，支持 python -m inactive_user_cli"""

import os
import sys

# Windows 强制 UTF-8 输出 - 必须在任何其他导入之前
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from inactive_user_cli.cli import main

if __name__ == "__main__":
    main()