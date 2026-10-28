import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser

from config.settings import Config
from pages.admin.login_page import AdminLoginPage
from pages.primary.login_page import LoginPage
from utils.allure_helper import (
    attach_screenshot,
    generate_allure_report_dir,
    generate_single_file_html,
)
from utils.db_client import DBClient
from utils.wecom_notifier import WeComNotifier, build_test_report_markdown


# marker
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

    # 线上可执行 marker：标注可在生产环境安全执行的用例
    config.addinivalue_line("markers", "online: 可在线上(生产)环境执行")

    if getattr(config.option, "allure_report_dir", None) or hasattr(config, "workerinput"):
        return
    config.option.allure_report_dir = generate_allure_report_dir()


def pytest_runtest_logstart(nodeid: str) -> None:
    """用例开始前打印分隔线，便于在控制台日志中定位步骤归属的用例。"""
    print(f"\n{'=' * 60}\n==> 开始执行用例: {nodeid}\n{'=' * 60}")


def _safe_attach(page, name="截图"):
    """安全截图，页面已关闭则跳过"""
    try:
        attach_screenshot(page, name)
    except Exception:
        pass


def _new_logged_in_context(browser: Browser, account: dict):
    """创建已登录的独立 context。

    采用单会话策略：目标系统限制同账号多会话时，重新打开新页面必须
    重新登录，登录态缓存（storage_state）无法复用，每次调用都执行
    完整登录。
    """
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    # 不等 load：页面挂载的第三方 SDK（埋点等）偶发挂起会让 load 事件
    # 迟迟不触发，而 default_timeout 仅 10s 导致 goto 超时；
    # 登录流程首步会自动等元素，DOM ready 即可
    page.goto(Config.BASE_URL, wait_until="domcontentloaded", timeout=30000)

    LoginPage(page).login(account["username"], account["password"])
    # 此时 page 已在首页，无需再次 goto
    return context, page


@pytest.fixture(scope="function")
def logged_in_page(browser: Browser, request, worker_id):
    """主平台-已登录页面（每个用例独立 context，各自完整登录）"""
    account = _resolve_account(request, worker_id)
    context, page = _new_logged_in_context(browser, account)
    yield page
    _safe_attach(page, "最终截图")
    context.close()


@pytest.fixture(scope="function")
def page_factory(browser: Browser):
    """按指定账号创建已登录页面的工厂（用于单用例内多账号场景）。

    用法：page = page_factory({"username": ..., "password": ...})
    每次创建都执行完整登录；各账号 context 相互隔离。
    """
    contexts = []

    def _create(account: dict):
        context, page = _new_logged_in_context(browser, account)
        contexts.append(context)
        return page

    yield _create

    for context in contexts:
        context.close()


@pytest.fixture(scope="module")
def shared_page(browser: Browser, request, worker_id):
    """主平台-已登录页面（module 级别共享：每模块独立 context，完整登录）"""
    account = _resolve_account(request, worker_id)
    context, page = _new_logged_in_context(browser, account)
    yield page
    context.close()


# 管理后台 fixtures
# 管理后台是独立系统，与主平台各自走完整登录流程


def _new_admin_logged_in_context(browser: Browser):
    """创建已登录的管理后台 context（每次都完整登录）"""
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)

    AdminLoginPage(page).login()
    return context, page


@pytest.fixture(scope="function")
def admin_logged_in_page(browser: Browser):
    """管理后台-已登录页面（function 级别，用例间隔离）"""
    context, page = _new_admin_logged_in_context(browser)
    yield page
    _safe_attach(page, "管理后台最终截图")
    context.close()


@pytest.fixture(scope="module")
def admin_shared_page(browser: Browser):
    """管理后台-已登录页面（module 级别，同模块用例共享）"""
    context, page = _new_admin_logged_in_context(browser)
    yield page
    context.close()


# 子系统 fixtures
# 子系统账号复用主平台登录流程，但使用独立账号


def _new_sub_logged_in_context(browser: Browser):
    """子系统账号-已登录主平台 context（每次都完整登录）"""
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto(Config.BASE_URL, wait_until="domcontentloaded", timeout=30000)
    LoginPage(page).login(Config.SUB_USERNAME, Config.SUB_PASSWORD)
    return context, page


@pytest.fixture(scope="function")
def sub_logged_in_page(browser: Browser):
    """子系统账号-已登录主平台页面（用于主平台内子系统页面的测试）"""
    context, page = _new_sub_logged_in_context(browser)
    yield page
    _safe_attach(page, "子系统最终截图")
    context.close()


@pytest.fixture(scope="module")
def sub_shared_page(browser: Browser):
    """子系统账号-已登录主平台页面（module 级别）"""
    context, page = _new_sub_logged_in_context(browser)
    yield page
    context.close()


def _strip_aria_snapshot(excinfo) -> None:
    """剥离 Playwright 断言失败异常消息中的 Aria snapshot 部分（保留 Call log 之前的摘要）。

    Playwright expect 断言失败会把整页 Aria snapshot 拼进异常消息，
    导致控制台与 Allure 报告被页面快照刷屏；
    在 makereport 生成报告前改写异常消息，各输出渠道随之只保留精简摘要。
    """
    value = excinfo.value
    message = str(value)
    marker = "\nAria snapshot:"
    if marker not in message or not value.args:
        return
    value.args = (message.split(marker)[0].rstrip(),)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # 报告生成前先剥离 Aria snapshot，确保 longrepr / Allure 各渠道一致降噪
    if call.excinfo is not None:
        _strip_aria_snapshot(call.excinfo)
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


def pytest_unconfigure(config) -> None:
    """测试结束后自动生成单文件 HTML 报告（Allure 3 awesome）。

    确保直接 pytest 运行（非 runner.py）时也能生成可分享的单 HTML；
    xdist worker 进程跳过，只在主进程执行。
    """
    # xdist worker 进程不生成报告
    if hasattr(config, "workerinput"):
        return

    allure_dir = getattr(config.option, "allure_report_dir", None)
    if not allure_dir:
        return

    html = generate_single_file_html(allure_dir)
    if html:
        rel = str(Path(allure_dir).relative_to(Path.cwd())).replace("\\", "/")
        print(f"\n单文件 HTML 报告已生成：{rel}/index.html")
        print(f"在线查看：allure open {rel}")
