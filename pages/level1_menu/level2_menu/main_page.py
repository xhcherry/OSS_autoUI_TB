from pages.base_page import BasePage
from pages.level1_menu.level2_menu.tab1 import Tab1
from pages.level1_menu.level2_menu.tab2 import Tab2
from pages.level1_menu.level2_menu.tab3 import Tab3


class Level2MenuPage(BasePage):
    """
    二级菜单
    1. 继承 BasePage (拥有 Header 和 navigate 权限)
    2. 管理 一级Tab/二级Tab/三级Tab 切换
    3. 实例化子组件
    """

    def __init__(self, page):
        super().__init__(page)

        # Tab切换定位器
        self.tab1_btn = page.get_by_text("一级Tab")
        self.tab2_btn = page.get_by_text("二级Tab")
        self.tab3_btn = page.get_by_text("三级Tab")

        # 实例化子组件
        self.tab1 = Tab1(page)
        self.tab2 = Tab2(page)
        self.tab3 = Tab3(page)

    # 切换至一级Tab
    def switch_to_tab1(self):
        self.tab1_btn.click()

    # 切换至二级Tab
    def switch_to_tab2(self):
        self.tab2_btn.click()

    # 切换至三级Tab
    def switch_to_tab3(self):
        self.tab3_btn.click()