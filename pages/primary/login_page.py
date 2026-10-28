from playwright.sync_api import Page, Error as PlaywrightError

from config.settings import Config
from pages.base_page import BasePage
from utils.captcha_solver import solve_slide_captcha


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
            self.page.get_by_role("slider").first.wait_for(state="visible", timeout=5000)
        except PlaywrightError:
            pass  # 白名单账号，无需验证码
        else:
            success = solve_slide_captcha(self.page)
            if not success:
                raise Exception("登录失败：滑块验证未通过，已超过最大重试次数！")

        # 等登录完成跳转（并发时后端响应变慢，上限 15s）
        self.page.wait_for_function("window.location.hash !== '#/login'", timeout=15000)

        try:
            heading = self.page.get_by_role("heading", name="安全提示")
            heading.first.wait_for(state="visible", timeout=2000)
            self.page.get_by_role("button", name="关闭此对话框").first.click(timeout=1000)
        except PlaywrightError:
            pass  # 无安全提示对话框，无需关闭

        # 可选：提示弹窗（"我知道了"）
        try:
            know_btn = self.page.get_by_role("button", name="我知道了")
            know_btn.first.wait_for(state="visible", timeout=1000)
            know_btn.first.click(timeout=1000)
        except PlaywrightError:
            pass  # 无提示弹窗
