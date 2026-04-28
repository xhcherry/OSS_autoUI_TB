from playwright.sync_api import Page
from config.settings import Config
from pages.components.header import Header

class BasePage:
    def __init__(self, page: Page):
        self.page = page
        # 实例化 Header，并赋值给 self.header
        self.header = Header(page)

    def navigate(self, url: str = None):
        if url:
            self.page.goto(url)
        else:
            self.page.goto(Config.BASE_URL)

    # 数据列表中"操作"的通用函数
    def open_operation_menu(self, filter_text: str, trigger_text: str = "操作"):
        """
        在表格中定位特定行，并悬浮触发按钮以显示下拉菜单
        """
        # 1. 锁定目标行
        target_row = self.page.locator("tr").filter(has_text=filter_text)

        # 2. 找到触发按钮
        operation_btn = target_row.get_by_text(trigger_text).first

        # 3. 悬浮触发
        operation_btn.hover()
