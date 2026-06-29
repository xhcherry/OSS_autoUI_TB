from playwright.sync_api import Page
from config.settings import Config
from pages.header import Header, AdminHeader, SubHeader

class BasePage:
    """页面对象基类。

    platform 参数决定懒加载哪个平台的 Header：
    - "default"：主平台标准布局（Header）
    - "alt"   ：主平台备用布局（Header，菜单不同）
    - "admin" ：管理后台（AdminHeader）
    - "sub"   ：子系统（SubHeader）
    """

    def __init__(self, page: Page, platform: str = "default"):
        self.page = page
        self._platform = platform
        self._header = None

    @property
    def header(self):
        """懒加载 Header，弹窗等不需要导航的页面可以避免无效初始化"""
        if self._header is None:
            if self._platform == "admin":
                self._header = AdminHeader(self.page)
            elif self._platform == "sub":
                self._header = SubHeader(self.page)
            else:
                # default / alt 均使用主平台 Header（alt 切换备用菜单）
                self._header = Header(self.page, self._platform)
        return self._header

    def navigate(self, url: str | None = None):
        if url:
            self.page.goto(url)
        else:
            self.page.goto(Config.BASE_URL)

    def _trigger_hover(self, filter_text: str, trigger_text: str):
        """在表格中定位特定行，悬浮触发按钮"""
        target_row = self.page.locator("tr").filter(has_text=filter_text)
        operation_btn = target_row.get_by_text(trigger_text).first
        operation_btn.hover()

    def hover_operation(self, filter_text: str, trigger_text: str = "操作"):
        self._trigger_hover(filter_text, trigger_text)

    def hover_more(self, filter_text: str, trigger_text: str = "更多"):
        self._trigger_hover(filter_text, trigger_text)

    def hover_trial(self, filter_text: str, trigger_text: str = "试听"):
        self._trigger_hover(filter_text, trigger_text)
