import time
from playwright.sync_api import Page, Error as PlaywrightError
from pages.base_page import BasePage
from config.settings import Config


class AdminLoginPage(BasePage):
    """管理后台登录页面"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_role("textbox", name="请输入账号")
        self.password_input = page.get_by_role("textbox", name="请输入密码")
        self.login_button = page.get_by_role("button", name="登  录")

    def login(
        self,
        username: str = Config.ADMIN_USERNAME,
        password: str = Config.ADMIN_PASSWORD,
    ):
        self.page.goto(Config.ADMIN_BASE_URL)
        self.username_input.click()
        self.username_input.fill(username)
        self.password_input.click()
        self.password_input.fill(password)
        self.login_button.click()

        # 登录后等待页面跳转
        try:
            self.page.wait_for_function(
                "window.location.hash !== '#/login'", timeout=15000
            )
        except PlaywrightError:
            pass

        time.sleep(1)
