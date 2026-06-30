"""devflow_diag — báo 'code nào đang CHẠY' để biết có cần reload không.

Chốt chặn cho friction "lỡ sửa code mà server còn chạy bản cũ": chụp fingerprint
code LÚC IMPORT (= bản đang nạp) rồi so với fingerprint ĐĨA lúc gọi. Khác nhau ⇒
đĩa đã đổi ⇒ server đang chạy bản cũ ⇒ cần Reconnect/restart.

KHÔNG trả secret — chỉ fingerprint + cờ cấu hình (bool) + thống kê.
"""
import hashlib
import os
import sys
import time

import config
from http_common import build_tool_safe

_safe = build_tool_safe("devflow")
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # devflow-mcp/
_START = time.time()
_SKIP_DIRS = {".venv", "__pycache__", ".git", "tests", ".pytest_cache", "guides", "plans"}


def _iter_py(root: str):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def _fingerprint(root: str):
    """sha256 (12 hex) trên nội dung mọi .py + số file + mtime mới nhất."""
    h = hashlib.sha256()
    newest = 0.0
    count = 0
    for p in sorted(_iter_py(root)):
        try:
            st = os.stat(p)
            with open(p, "rb") as fh:
                h.update(os.path.relpath(p, root).encode())
                h.update(fh.read())
            newest = max(newest, st.st_mtime)
            count += 1
        except OSError:
            continue
    return h.hexdigest()[:12], count, newest


# Chụp NGAY LÚC IMPORT = vân tay của đúng bản code đang được process này nạp.
_LOADED_FP, _LOADED_FILES, _LOADED_MTIME = _fingerprint(_PKG_ROOT)


def _ts(epoch: float):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch)) if epoch else None


@_safe
def devflow_diag() -> dict:
    """Chẩn đoán server đang chạy: code có bị cũ so với đĩa không (KHÔNG lộ secret).

    `stale=true` ⇒ đã sửa code sau khi server khởi động → /mcp → devflow → Reconnect
    (hoặc restart Claude) để nạp bản mới. Gọi lại sau reload: fingerprint phải khớp.
    """
    disk_fp, nfiles, newest = _fingerprint(_PKG_ROOT)
    stale = disk_fp != _LOADED_FP
    return {
        "pid": os.getpid(),
        "started_at": _ts(_START),
        "uptime_sec": round(time.time() - _START),
        "python": sys.version.split()[0],
        "transport": os.getenv("DEVFLOW_TRANSPORT", "stdio").lower(),
        "loaded_fingerprint": _LOADED_FP,  # bản đang chạy nạp lúc khởi động
        "disk_fingerprint": disk_fp,       # bản đang nằm trên đĩa lúc này
        "stale": stale,
        "reload_hint": (
            "Code trên đĩa KHÁC bản đang chạy → /mcp → devflow → Reconnect để nạp bản mới"
            if stale else "đang chạy code mới nhất ✓"
        ),
        "py_files": nfiles,
        "newest_mtime": _ts(newest),
        "services": {  # chỉ bool — có cấu hình hay không, TUYỆT ĐỐI không kèm giá trị
            "gitlab": config.gitlab_client is not None,
            "notion": config.notion_client is not None,
            "figma": config.figma_client is not None,
            "jira_write": config.JIRA_ENABLE_WRITE,
        },
    }


TOOLS = [devflow_diag]


def register(mcp) -> None:
    for fn in TOOLS:
        mcp.tool()(fn)
