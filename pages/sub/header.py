"""子系统导航 Header 及子系统 SPA 侧边栏。

子系统账号复用主平台登录，但导航菜单与默认布局不同。
"""
from playwright.sync_api import Page

_SUB_MENUS = [
    ("resource", "子系统菜单1", "sub_menu1", None),
    ("resource", "子系统菜单2", "sub_menu2", None),
    ("resource", "子系统菜单3", "sub_menu3", None),
]

# 子系统账号与主平台共用同一套一级 Tab
_SUB_TABS = {
    "一级菜单1": "workbench", "一级菜单2": "brand", "一级菜单3": "market",
    "一级菜单4": "sales", "一级菜单5": "academic", "一级菜单6": "resource",
}


class SubHeader:
    """子系统导航 Header。

    navigate_to_{key}() 动态方法：
    - navigate_to_sub_menu1() → 一级菜单6 → 子系统菜单1
    - navigate_to_sub_menu2() → 一级菜单6 → 子系统菜单2
    - ...
    """

    def __init__(self, page: Page):
        self.page = page

        for name, key in _SUB_TABS.items():
            setattr(self, f"{key}_tab", page.get_by_text(name).first)

        self.collapse = page.get_by_text("收起")

        self._routes = {}
        for tab_key, menu_text, nav_key, _kw in _SUB_MENUS:
            tab = getattr(self, f"{tab_key}_tab")
            menu = page.get_by_role("link", name=menu_text, exact=True)
            self._routes[nav_key] = (tab, menu)

    def _click_menu(self, primary_tab, secondary_menu):
        primary_tab.click()
        secondary_menu.first.wait_for(state="visible")
        secondary_menu.first.click()

    def get_menu_href(self, nav_key: str) -> str | None:
        """确保菜单可见后，获取菜单链接的 href（SSO 外链）。

        先读 href 避免点击后页面跳走导致元素丢失。
        始终先点击一级 tab 触发下拉展开，避免 is_visible() 误判。
        """
        route = self._routes.get(nav_key)
        if route is None:
            return None
        tab, menu = route
        tab.click()
        menu.first.wait_for(state="visible")
        href = menu.first.get_attribute("href")
        return href if href else None

    def __getattr__(self, name):
        if name.startswith("navigate_to_"):
            key = name[len("navigate_to_"):]
            route = self._routes.get(key)
            if route is not None:
                tab, menu = route
                return lambda: self._click_menu(tab, menu)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )


# ── 子系统 SPA 侧边栏 ──

_SPA_MENUS = {
    "config": "配置管理",
    "paper": "内容管理",
}


class SubSidebar:
    """子系统 SPA 侧边栏导航"""

    def __init__(self, page: Page):
        self.page = page
        for key, name in _SPA_MENUS.items():
            setattr(self, f"{key}_menu", page.get_by_role("menuitem", name=name))

    def go_to_config(self):
        """进入「配置管理」"""
        self.config_menu.click()

    def go_to_paper(self):
        """进入「内容管理」"""
        self.paper_menu.click()
