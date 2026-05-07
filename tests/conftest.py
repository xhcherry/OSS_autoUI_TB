import pytest
from playwright.sync_api import Page, Browser
from pages.login_page import LoginPage
from config.settings import Config
from utils.db_client import DBClient
from utils.allure_helper import generate_allure_report_dir, attach_screenshot

# ── 模块 marker → 账号池映射 ──────────────────────────────────────
MODULE_ACCOUNTS = {
    "sales":    Config.SALES_ACCOUNTS,
    "academic": Config.ACADEMIC_ACCOUNTS,
    "resource": Config.RESOURCE_ACCOUNTS,
}


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

    # worker_id 轮询：master → pool[0]；gw0,gw1,... → 取模
    if worker_id == "master":
        return pool[0]
    worker_index = int(worker_id[2:])
    return pool[worker_index % len(pool)]


def pytest_configure(config):
    # 如果 runner.py 已设置 --alluredir，或者当前是 worker 进程，跳过
    if getattr(config.option, "allure_report_dir", None) or hasattr(config, "workerinput"):
        return
    # 直接运行 pytest 命令时的 fallback：动态生成报告目录
    config.option.allure_report_dir = generate_allure_report_dir()


@pytest.fixture(scope="function")
def logged_in_page(page: Page, request, worker_id):
    page.set_default_timeout(10000)  # 10 秒
    account = _resolve_account(request, worker_id)
    login_page = LoginPage(page)
    page.goto(Config.BASE_URL)
    login_page.login(account["username"], account["password"])
    yield page
    attach_screenshot(page, "最终截图")


@pytest.fixture(scope="module")
def shared_page(browser: Browser, request, worker_id):
    account = _resolve_account(request, worker_id)
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)  # 10 秒

    login_page = LoginPage(page)
    page.goto(Config.BASE_URL)
    login_page.login(account["username"], account["password"])

    yield page

    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图附加到 Allure 报告"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        for fixture_name in ("logged_in_page", "shared_page", "page"):
            page = item.funcargs.get(fixture_name)
            if page is not None:
                attach_screenshot(page, "失败截图")
                break


@pytest.fixture(scope="session")
def db():
    """Session级别的数据库夹具，整个测试过程只实例化一次连接"""
    db_client = DBClient()
    yield db_client
    db_client.close()
