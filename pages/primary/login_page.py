from playwright.sync_api import Page, Error as PlaywrightError
from pages.base_page import BasePage
from config.settings import Config
from utils.captcha_solver import solve_click_captcha

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_role("textbox", name="请输入账号")
        self.password_input = page.get_by_role("textbox", name="请输入密码")
        self.login_button = page.get_by_role("button", name="登 录")

    def login(self, username: str = Config.USERNAME, password: str = Config.PASSWORD):
        self.username_input.click()
        self.username_input.fill(username)
        self.password_input.click()
        self.password_input.fill(password)
        self.login_button.click()

        try:
            self.page.locator("canvas").wait_for(state="visible", timeout=2000)
        except PlaywrightError:
            pass  # 白名单账号，无需验证码
        else:
            success = solve_click_captcha(self.page)
            if not success:
                raise Exception("登录失败：AI验证码识别或通关失败，已超过最大重试次数！")

        # 并发响应变慢
        self.page.wait_for_function("window.location.hash !== '#/login'", timeout=15000)

        try:
            heading = self.page.get_by_role("heading", name="安全提示")
            heading.first.wait_for(state="visible", timeout=2000)
            self.page.get_by_role("button", name="关闭此对话框").first.click(timeout=3000)
        except PlaywrightError:
            pass  # 无安全提示对话框，无需关闭
