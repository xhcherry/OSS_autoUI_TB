import os

from dotenv import load_dotenv

load_dotenv()


def _parse_account_pool(raw, fallback_user, fallback_pass):
    """解析账号池字符串 'user1:pass1,user2:pass2'；为空时回退到单账号"""
    if raw:
        pool = []
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" in pair:
                u, p = pair.split(":", 1)
                pool.append({"username": u.strip(), "password": p.strip()})
        if pool:
            return pool
    return [{"username": fallback_user, "password": fallback_pass}]


class Config:
    # OSS登录
    BASE_URL = os.getenv("BASE_URL", "")
    USERNAME = os.getenv("OSS_USERNAME", "")
    PASSWORD = os.getenv("OSS_PASSWORD", "")

    # ── 模块专用账号池 ────────────────────────────────────────────
    # 每个模块可配单个或多个账号，并发时按 worker_id 轮询分配。
    # 方式1（池子，推荐）：OSS_SALES_ACCOUNTS=user1:pass1,user2:pass2
    # 方式2（单账号兼容）：OSS_SALES_USERNAME / OSS_SALES_PASSWORD
    # 优先级：池子 > 单账号 > 基础账号
    SALES_ACCOUNTS = _parse_account_pool(
        os.getenv("OSS_SALES_ACCOUNTS", ""),
        os.getenv("OSS_SALES_USERNAME", USERNAME),
        os.getenv("OSS_SALES_PASSWORD", PASSWORD),
    )
    ACADEMIC_ACCOUNTS = _parse_account_pool(
        os.getenv("OSS_ACADEMIC_ACCOUNTS", ""),
        os.getenv("OSS_ACADEMIC_USERNAME", USERNAME),
        os.getenv("OSS_ACADEMIC_PASSWORD", PASSWORD),
    )
    RESOURCE_ACCOUNTS = _parse_account_pool(
        os.getenv("OSS_RESOURCE_ACCOUNTS", ""),
        os.getenv("OSS_RESOURCE_USERNAME", USERNAME),
        os.getenv("OSS_RESOURCE_PASSWORD", PASSWORD),
    )

    # vs2数据库
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
