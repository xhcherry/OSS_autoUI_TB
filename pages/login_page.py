from playwright.sync_api import Page
from pages.base_page import BasePage
from config.settings import Config
from utils.captcha_solver import solve_click_captcha

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # 登录
        self.username_input = page.get_by_role("textbox", name="请输入账号")
        self.password_input = page.get_by_role("textbox", name="请输入密码")
        self.login_button = page.get_by_role("button", name="登 录")

    def login(self, username: str = Config.USERNAME, password: str = Config.PASSWORD):
        self.username_input.click()
        self.username_input.fill(username)
        self.password_input.click()
        self.password_input.fill(password)
        self.login_button.click()

        # 验证码
        success = solve_click_captcha(self.page)
        if not success:
            raise Exception("登录失败：AI验证码识别或通关失败，已超过最大重试次数！")
            
        # 并发时网络/系统响应会变慢，必须死等页面实质上离开 login 状态，才能将 page 交给测试用例
        self.page.wait_for_function("window.location.hash !== '#/login'", timeout=15000)

        # 关闭首页可能会弹出的公告/广告对话框（最多等 3 秒）
        # 不能用 add_locator_handler 全局监听
        try:
            self.page.get_by_role("button", name="关闭此对话框").first.click(timeout=3000)
        except Exception:
            pass