import os
from datetime import datetime
import allure
import pytest
from playwright.sync_api import Page, Browser
from pages.login_page import LoginPage
from config.settings import Config
from utils.db_client import DBClient


def pytest_configure(config):
    # 如果已经通过命令行设置了 allure_report_dir (例如在 runner.py 中设置了)，或者当前是 worker 进程，就不执行动态生成
    if getattr(config.option, "allure_report_dir", None) or hasattr(config, "workerinput"):
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'report', f'allure-results-{timestamp}')
    os.makedirs(results_dir, exist_ok=True)
    # 动态设置 alluredir，每次运行独立目录，历史报告全部保留
    config.option.allure_report_dir = results_dir


@pytest.fixture(scope="session")
def account_config(worker_id):
    """
    根据 worker_id (gw0, gw1...) 从账号池中分配账号。
    如果是单线程运行，worker_id 为 'master'。
    """
    if not Config.ACCOUNTS:
        raise ValueError("未在 .env 或 settings 中配置 OSS 账号")

    if worker_id == "master":
        return Config.ACCOUNTS[0]

    # worker_id 格式为 gw0, gw1, gw2...
    worker_index = int(worker_id[2:])
    # 使用取模运算分配账号，支持 线程数 > 账号数 或 线程数 < 账号数
    return Config.ACCOUNTS[worker_index % len(Config.ACCOUNTS)]


@pytest.fixture(scope="function")
def logged_in_page(page: Page, account_config):
    login_page = LoginPage(page)
    page.goto(Config.BASE_URL)
    login_page.login(account_config["username"], account_config["password"])
    yield page
    # 测试结束后截图附加到报告
    allure.attach(
        page.screenshot(full_page=True),
        name="最终截图",
        attachment_type=allure.attachment_type.PNG,
    )


# 新增一个module fixture
@pytest.fixture(scope="module")
def shared_page(browser: Browser, account_config):
    context = browser.new_context()
    page = context.new_page()

    login_page = LoginPage(page)
    page.goto(Config.BASE_URL)
    login_page.login(account_config["username"], account_config["password"])

    yield page

    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图附加到 Allure 报告"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # 尝试从 fixture 中获取 page 对象
        page: Page = None
        for fixture_name in ("logged_in_page", "shared_page", "page"):
            page = item.funcargs.get(fixture_name)
            if page is not None:
                break

        if page is not None:
            allure.attach(
                page.screenshot(full_page=True),
                name="失败截图",
                attachment_type=allure.attachment_type.PNG,
            )


@pytest.fixture(scope="session")
def db():
    """
    Session级别的数据库夹具，整个测试过程只实例化一次连接
    """
    db_client = DBClient()
    yield db_client
    db_client.close()
