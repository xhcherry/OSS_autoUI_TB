from playwright.sync_api import Page
from pages.base_page import BasePage

class Tab3:
    """
    [二级容器]三级Tab
    内部tab切换:内部Tab1/内部Tab2
    实例化两个内部tab
    """
    def __init__(self, page: Page):
        self.page = page
        self.inner_tab1_btn = self.page.get_by_text("三级Tab-内部Tab1", exact=True)
        self.inner_tab2_btn = self.page.get_by_text("三级Tab-内部Tab2", exact=True)

        self.inner_tab1 = Tab3InnerTab1(page)
        self.inner_tab2 = Tab3InnerTab2(page)

    def switch_to_inner_tab1(self):
        self.inner_tab1_btn.click()

    def switch_to_inner_tab2(self):
        self.inner_tab2_btn.click()


class _BaseProgressTab(BasePage):
    """
    【私有基类】两个子tab的共有逻辑
    """
    def __init__(self, page: Page):
        super().__init__(page)


class Tab3InnerTab1(_BaseProgressTab):
    """【子组件】三级Tab - 内部Tab1"""
    pass


class Tab3InnerTab2(_BaseProgressTab):
    """【子组件】三级Tab - 内部Tab2"""
    pass