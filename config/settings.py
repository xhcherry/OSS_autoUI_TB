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


def _platform_flag(name, default=False):
    """解析外部（测试平台 / CI）注入的子进程环境变量布尔开关
    （1/true/yes/on，不区分大小写）。本地直接 pytest 运行时不存在该变量，
    保持默认关闭。
    """
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # 框架无头静默运行公共参数
    # （-s 输出步骤日志，便于 CI/服务器查看执行过程；runner.py 覆盖调试 addopts 时使用）
    HEADLESS_ADDOPTS = "-s -v --tb=short --strict-markers --import-mode=importlib"

    # 主平台登录（必填）
    BASE_URL = os.getenv("BASE_URL", "")
    USERNAME = os.getenv("USERNAME", "")
    PASSWORD = os.getenv("PASSWORD", "")

    # 模块专用账号池
    # 每个模块可配单个或多个账号，并发时按 worker_id 轮询分配。
    # 方式1（池子，推荐）：MODULE_A_ACCOUNTS=user1:pass1,user2:pass2
    # 方式2（单账号兼容）：MODULE_A_USERNAME / MODULE_A_PASSWORD
    # 优先级：池子 > 单账号 > 基础账号
    # 每新增 XXX_ACCOUNTS，conftest 会自动注册同名 pytest marker "xxx"。
    MODULE_A_ACCOUNTS = _parse_account_pool(
        os.getenv("MODULE_A_ACCOUNTS", ""),
        os.getenv("MODULE_A_USERNAME", USERNAME),
        os.getenv("MODULE_A_PASSWORD", PASSWORD),
    )
    MODULE_B_ACCOUNTS = _parse_account_pool(
        os.getenv("MODULE_B_ACCOUNTS", ""),
        os.getenv("MODULE_B_USERNAME", USERNAME),
        os.getenv("MODULE_B_PASSWORD", PASSWORD),
    )
    MODULE_C_ACCOUNTS = _parse_account_pool(
        os.getenv("MODULE_C_ACCOUNTS", ""),
        os.getenv("MODULE_C_USERNAME", USERNAME),
        os.getenv("MODULE_C_PASSWORD", PASSWORD),
    )

    # 企业微信机器人通知
    WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL", "")
    # 推送开关：runner.py 触发时置 True；外部平台也可通过
    # 子进程环境变量 WECOM_NOTIFY=1 注入，本地直跑默认不推送
    WECOM_NOTIFY = _platform_flag("WECOM_NOTIFY", False)

    # 管理后台平台（数据验证用，可选）
    ADMIN_BASE_URL = os.getenv("ADMIN_BASE_URL", "")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    # 子系统平台（可选，复用主平台 BASE_URL 登录后跳转）
    SUB_USERNAME = os.getenv("SUB_USERNAME", "")
    SUB_PASSWORD = os.getenv("SUB_PASSWORD", "")

    # 数据库（数据验证用，可选）
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
