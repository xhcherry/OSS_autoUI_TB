"""管理后台导航 Header。"""
from playwright.sync_api import Page

_ADMIN_MENUS = [
    ("content", "二级菜单1", "admin_menu1", None),
    ("content", "二级菜单2", "admin_menu2", None),
    ("business", "二级菜单3", "admin_menu3", None),
    ("rd", "二级菜单4", "admin_menu4", None),
]

_ADMIN_TABS = {
    "一级菜单1": "content",
    "一级菜单2": "business",
    "一级菜单3": "rd",
}


class AdminHeader:
    """管理后台导航 Header。

    navigate_to_{key}() 动态方法：
    - navigate_to_admin_menu1() → 一级菜单1 → 二级菜单1
    - navigate_to_admin_menu2() → 一级菜单1 → 二级菜单2
    - ...
    """

    def __init__(self, page: Page):
        self.page = page
        for name, key in _ADMIN_TABS.items():
            setattr(self, f"{key}_tab", page.get_by_role("menuitem", name=name))

        self._routes = {}
        for tab_key, menu_text, nav_key, _kw in _ADMIN_MENUS:
            tab = getattr(self, f"{tab_key}_tab")
            menu = page.get_by_text(menu_text, exact=True)
            self._routes[nav_key] = (tab, menu)

    @staticmethod
    def _click_menu(primary_tab, secondary_menu):
        if not secondary_menu.first.is_visible():
            primary_tab.click()
        secondary_menu.first.click()

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
