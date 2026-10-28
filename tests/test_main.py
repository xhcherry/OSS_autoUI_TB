"""
架构冒烟测试。

修改 config / utils / runner / tests/conftest.py 等架构代码后，
必须跑通本文件，确认框架核心链路未被破坏：

1. 登录 fixture（logged_in_page / shared_page 单会话完整登录）
2. Header 动态导航（navigate_to_{key} 自动派发）
3. 账号池 / marker 解析（conftest._resolve_account）
4. BasePage 通用元素与等待收口（loading_mask / error_text）

用例只依赖架构自身（pages.primary.header、config.settings、conftest fixtures），
不引入任何业务页面，便于在剥离架构后独立验证。
"""
import re

import pytest
from playwright.sync_api import expect

from config.settings import Config
from pages.base_page import BasePage
from pages.primary.header import Header
from utils.allure_helper import attach_screenshot


def test_config_loaded():
    """验证 .env 已被加载，BASE_URL 非空。"""
    assert Config.BASE_URL, "BASE_URL 未配置，请检查 .env"


def test_login_fixture_works(logged_in_page):
    """验证登录态 fixture：登录成功后页面应离开 #/login。"""
    expect(logged_in_page).not_to_have_url(re.compile(r"#/login"))


@pytest.mark.p1
def test_all_pages_navigation(shared_page):
    """遍历主平台 Header 所有二级菜单路由，校验页面可正常打开且无报错文案。

    覆盖 Header 的 __getattr__ 动态导航、_click_menu 展开逻辑，
    以及 BasePage 的 loading 遮罩等待与 error_text 校验，
    是架构导航能力的端到端冒烟。
    """
    header = Header(shared_page)
    base = BasePage(shared_page)
    failed = []

    for index, nav_key in enumerate(header._routes, start=1):
        try:
            getattr(header, f"navigate_to_{nav_key}")()
            # 关闭页面可能存在的弹窗，等 loading 遮罩消失（页面稳定）后校验
            base.dismiss_dialog_if_present()
            base.wait_loading_done()
            expect(base.error_text).not_to_be_visible()
        except Exception as e:
            try:
                attach_screenshot(shared_page, f"{index:02d}_{nav_key}_FAILED")
            except Exception:
                pass
            failed.append(f"{nav_key}: {e}")

    if failed:
        pytest.fail("以下页面跳转校验失败:\n" + "\n".join(failed))
