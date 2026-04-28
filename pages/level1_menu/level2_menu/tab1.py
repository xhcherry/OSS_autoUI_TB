from playwright.sync_api import Page
from pages.base_page import BasePage

class Tab1:
    """
        【二级容器】一级Tab
        功能：
        1. 包含内部 Tab 切换 (内部Tab1/内部Tab2)
        2. 实例化两个子面板
    """
    def __init__(self, page: Page):
        self.page = page
        # 1. 定义内部 Tab 切换按钮
        self.inner_tab1_btn = self.page.get_by_text("一级Tab-内部Tab1", exact=True)
        self.inner_tab2_btn = self.page.get_by_text("一级Tab-内部Tab2", exact=True)

        # 2. 实例化子业务面板
        self.inner_tab1 = InnerTab1(page)
        self.inner_tab2 = InnerTab2(page)

    # 切换动作
    def switch_to_inner_tab1(self):
        self.inner_tab1_btn.click()

    def switch_to_inner_tab2(self):
        self.inner_tab2_btn.click()

class InnerTab1(BasePage):
        # 【子组件】一级Tab - 内部Tab1
    def __init__(self, page: Page):
        super().__init__(page)

        # 1. 定位器
        # 顶部按钮
        self.add_btn = page.get_by_role("button", name="xxx")

    # 2. 业务方法
    def add_student(self):
        # 添加学员

class InnerTab2(BasePage):
    """
    【子组件】一级Tab - 内部Tab2
    这里写内部Tab2特有的按钮和逻辑
    """
    def __init__(self, page: Page):
        super().__init__(page)
        # 试听学员的定位器
