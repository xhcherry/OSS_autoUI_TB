import tempfile
import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser

from config.settings import Config
from pages.admin.login_page import AdminLoginPage
from pages.primary.login_page import LoginPage
from utils.allure_helper import attach_screenshot, generate_allure_report_dir
from utils.db_client import DBClient
from utils.wecom_notifier import WeComNotifier, build_test_report_markdown


# ── marker
def _build_account_registry():
    registry = {}
    for attr in dir(Config):
        if attr.endswith("_ACCOUNTS") and not attr.startswith("_"):
            marker_name = attr.removesuffix("_ACCOUNTS").lower()
            registry[marker_name] = getattr(Config, attr)
    return registry


MODULE_ACCOUNTS = _build_account_registry()


def _resolve_account(request, worker_id):
    """
    根据 pytest marker 返回对应板块的账号池，再按 worker_id 轮询分配。
    - 有 marker → 使用该模块的账号池
    - 无 marker → 使用默认账号
    - 多 worker 并发时自动轮询（gw0→pool[0], gw1→pool[1], ...）
    """
    pool = None
    for marker_name, account_pool in MODULE_ACCOUNTS.items():
        if request.node.get_closest_marker(marker_name):
            pool = account_pool
            break
    if pool is None:
        pool = [{"username": Config.USERNAME, "password": Config.PASSWORD}]

    if worker_id == "master":
        return pool[0]
    worker_index = int(worker_id[2:])
    return pool[worker_index % len(pool)]


def pytest_configure(config):
    for marker_name in MODULE_ACCOUNTS:
        config.addinivalue_line("markers", f"{marker_name}: {marker_name}板块用例")

    # 子系统账号不走 ACCOUNTS 池，手动注册
    config.addinivalue_line("markers", "sub: 子系统板块用例")

    for level in ("p0", "p1", "p2", "p3"):
        config.addinivalue_line("markers", f"{level}: 优先级{level.upper()}")

    if getattr(config.option, "allure_report_dir", None) or hasattr(config, "workerinput"):
        return
    config.option.allure_report_dir = generate_allure_report_dir()


# storageState 登录态缓存
# 缓存内容：{username: state_file_path}
_auth_state_cache: dict[str, str] = {}


def _safe_attach(page, name="截图"):
    """安全截图，页面已关闭则跳过"""
    try:
        attach_screenshot(page, name)
    except Exception:
        pass


def _ensure_auth_state(browser: Browser, account: dict):
    """
    为该账号准备好已登录的页面。
    - 首次调用：执行完整登录，保存 storage_state，返回已登录的 (context, page)
    - 已有缓存：返回 (None, None)，fixture 自己从文件创建新 context
    """
    cache_key = account["username"]

    if cache_key in _auth_state_cache:
        return None, None

    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto(Config.BASE_URL)

    login_page = LoginPage(page)
    login_page.login(account["username"], account["password"])
    # 此时 page 已在首页，无需再次 goto

    state_path = _save_storage_state(context, cache_key)
    _auth_state_cache[cache_key] = state_path

    return context, page


def _save_storage_state(context: Browser, cache_key: str) -> str:
    """将 storage_state 落盘并返回路径"""
    state_dir = Path(tempfile.gettempdir()) / "autoui_auth"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"state_{cache_key}.json"
    context.storage_state(path=str(state_path))
    return str(state_path)


def _new_context_from_cache(browser: Browser, cache_key: str):
    """从缓存文件创建已登录的新 context"""
    context = browser.new_context(storage_state=_auth_state_cache[cache_key])
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto(Config.BASE_URL)
    return context, page


@pytest.fixture(scope="function")
def logged_in_page(browser: Browser, request, worker_id):
    """主平台-已登录页面（首次登录直接复用 live page，后续用例从缓存创建独立 context）"""
    account = _resolve_account(request, worker_id)
    cache_key = account["username"]

    context, page = _ensure_auth_state(browser, account)
    if context is None:
        context, page = _new_context_from_cache(browser, cache_key)
    yield page
    _safe_attach(page, "最终截图")
    context.close()


@pytest.fixture(scope="module")
def shared_page(browser: Browser, request, worker_id):
    """主平台-已登录页面（首次登录直接复用 live page，后续模块从缓存创建独立 context）"""
    account = _resolve_account(request, worker_id)
    cache_key = account["username"]

    context, page = _ensure_auth_state(browser, account)
    if context is None:
        context, page = _new_context_from_cache(browser, cache_key)
    yield page
    context.close()


# ── 管理后台 fixtures ─────────────────────────────────────────
# 管理后台是独立系统，使用独立的登录态缓存

_ADMIN_AUTH_CACHE_KEY = "admin_user"


def _ensure_admin_auth_state(browser: Browser):
    """为管理后台账号准备登录态缓存（与主平台独立）"""
    if _ADMIN_AUTH_CACHE_KEY in _auth_state_cache:
        return None, None

    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)

    admin_login = AdminLoginPage(page)
    admin_login.login()

    state_path = _save_storage_state(context, "admin")
    _auth_state_cache[_ADMIN_AUTH_CACHE_KEY] = state_path

    return context, page


def _new_admin_context_from_cache(browser: Browser):
    """从缓存创建已登录的管理后台 context"""
    context = browser.new_context(storage_state=_auth_state_cache[_ADMIN_AUTH_CACHE_KEY])
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto(Config.ADMIN_BASE_URL)
    return context, page


@pytest.fixture(scope="function")
def admin_logged_in_page(browser: Browser):
    """管理后台-已登录页面（function 级别，用例间隔离）"""
    context, page = _ensure_admin_auth_state(browser)
    if context is None:
        context, page = _new_admin_context_from_cache(browser)
    yield page
    _safe_attach(page, "管理后台最终截图")
    context.close()


@pytest.fixture(scope="module")
def admin_shared_page(browser: Browser):
    """管理后台-已登录页面（module 级别，同模块用例共享）"""
    context, page = _ensure_admin_auth_state(browser)
    if context is None:
        context, page = _new_admin_context_from_cache(browser)
    yield page
    context.close()


# ── 子系统 fixtures ────────────────────────────────────────────
# 子系统账号复用主平台登录态缓存机制，但使用独立账号登录主平台。

_SUB_AUTH_CACHE_KEY = "sub_user"


def _ensure_sub_auth_state(browser: Browser):
    """为子系统账号准备登录态缓存"""
    if _SUB_AUTH_CACHE_KEY in _auth_state_cache:
        return None, None
    context = browser.new_context()
    page = context.new_page()
    page.goto(Config.BASE_URL)
    LoginPage(page).login(Config.SUB_USERNAME, Config.SUB_PASSWORD)
    state_path = _save_storage_state(context, "sub")
    _auth_state_cache[_SUB_AUTH_CACHE_KEY] = state_path
    return context, page


def _new_sub_context_from_cache(browser: Browser):
    context = browser.new_context(storage_state=_auth_state_cache[_SUB_AUTH_CACHE_KEY])
    page = context.new_page()
    page.goto(Config.BASE_URL)
    return context, page


@pytest.fixture(scope="function")
def sub_logged_in_page(browser: Browser):
    """子系统账号-已登录主平台页面（用于主平台内子系统页面的测试）"""
    context, page = _ensure_sub_auth_state(browser)
    if context is None:
        context, page = _new_sub_context_from_cache(browser)
    yield page
    _safe_attach(page, "子系统最终截图")
    context.close()


@pytest.fixture(scope="module")
def sub_shared_page(browser: Browser):
    """子系统账号-已登录主平台页面（module 级别）"""
    context, page = _ensure_sub_auth_state(browser)
    if context is None:
        context, page = _new_sub_context_from_cache(browser)
    yield page
    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        for fixture_name in (
            "logged_in_page",
            "shared_page",
            "page",
            "admin_logged_in_page",
            "admin_shared_page",
            "sub_logged_in_page",
            "sub_shared_page",
        ):
            page = item.funcargs.get(fixture_name)
            if page is not None:
                _safe_attach(page, "失败截图")
                break


@pytest.fixture(scope="session")
def db():
    db_client = DBClient()
    yield db_client
    db_client.close()


# 企业微信通知
_session_start: float = 0.0


def pytest_sessionstart(session: pytest.Session) -> None:
    global _session_start
    _session_start = time.time()


def _collect_severity_stats(stats: dict) -> dict[str, int]:
    """从 terminalreporter.stats 中提取各严重级别失败数（按 nodeid 去重）。"""
    result: dict[str, int] = {"p0": 0, "p1": 0, "p2": 0, "p3": 0}
    seen: set[str] = set()
    for report in (*stats.get("failed", []), *stats.get("error", [])):
        if report.nodeid in seen:
            continue
        seen.add(report.nodeid)
        for sev in result:
            if sev in report.keywords:
                result[sev] += 1
                break
    return result


def pytest_terminal_summary(terminalreporter, exitstatus: int) -> None:
    """测试结束后通过企业微信机器人发送摘要通知（仅 runner.py 触发时）。"""
    if not Config.WECOM_NOTIFY:
        return

    webhook_url = Config.WECOM_WEBHOOK_URL
    if not webhook_url:
        return

    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    error = len(stats.get("error", []))
    total = passed + failed + skipped + error

    if total == 0:
        return

    duration = time.time() - _session_start
    severity_failures = _collect_severity_stats(stats)

    allure_dir = getattr(terminalreporter.config.option, "allure_report_dir", "")

    markdown = build_test_report_markdown(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        error=error,
        severity_failures=severity_failures,
        duration_seconds=duration,
        report_dir=Path(allure_dir).name if allure_dir else "",
    )

    try:
        WeComNotifier(webhook_url).send_markdown(markdown)
        terminalreporter.write_line("\n[WeCom] 测试报告已推送至企业微信群机器人\n")
    except Exception as e:
        terminalreporter.write_line(f"\n[WeCom] 推送测试报告失败: {e}\n")
