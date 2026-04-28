from playwright.sync_api import Page


class Header:
    """
    导航至指定的二级菜单的管理页面
    """
    def __init__(self, page: Page):
        self.page = page
        # 一级菜单
        self.leavl1 = page.get_by_text("一级菜单").first

        # 二级菜单
        # 一级菜单模块
        self.leavl2 = page.get_by_text("二级菜单",exact=True)

    def _click_menu(self, primary_tab, secondary_menu):
        if not secondary_menu.is_visible():
            primary_tab.click()
        secondary_menu.click()

    # 一级菜单模块
    ## 二级菜单
    def navigate_to_student(self):
        self._click_menu(self.leavl2, self.leavl1)
