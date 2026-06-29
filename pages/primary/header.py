"""
主平台导航 Header。

支持两种菜单布局：
- platform='default'：标准布局（一级菜单1/一级菜单2/...）
- platform='alt'    ：备用布局（适用于菜单结构不同的同平台账号）

新增二级菜单只需在 _MENUS / _ALT_MENUS 追加一行：
    (一级tab key, 二级菜单文本, navigate 方法名, 定位器配置)
menu_text=None 表示只点击一级 tab，无二级菜单。
定位器配置 kwarg：exact=True / role="menuitem" / css="#selector"
"""
from playwright.sync_api import Page

# ── default 布局 ──
_MENUS = [
    ("home", None, "home", None),
    ("menu1", "二级菜单1", "menu1_sub1", None),
    ("menu1", "二级菜单2", "menu1_sub2", {"exact": True}),
    ("menu2", "二级菜单3", "menu2_sub1", None),
]

_TABS = {
    "一级菜单1": "home", "一级菜单2": "menu1", "一级菜单3": "menu2",
}

# ── alt 布局（备用菜单结构）──
_ALT_MENUS = [
    ("alt_main", None, "alt_main", None),
    ("alt_main", "备用二级菜单1", "alt_sub1", None),
    ("alt_main", "备用二级菜单2", "alt_sub2", None),
    ("alt_resource", "备用二级菜单3", "alt_sub3", {"exact": True}),
]

_ALT_TABS = {"备用一级菜单1": "alt_main", "备用一级菜单2": "alt_resource"}


class Header:
    """主平台导航 Header。

    - platform='default'：标准布局
    - platform='alt'    ：备用布局

    - Tab 定位器自动生成：self.{key}_tab
    - 导航方法自动解析：self.navigate_to_{nav_key}()
    """

    def __init__(self, page: Page, platform: str = "default"):
        self.page = page
        self._platform = platform
        tabs = _ALT_TABS if platform == "alt" else _TABS
        menus = _ALT_MENUS if platform == "alt" else _MENUS

        for name, key in tabs.items():
            setattr(self, f"{key}_tab", page.get_by_text(name).first)

        self.collapse = page.get_by_text("收起")

        self._routes = {}
        for tab_key, menu_text, nav_key, kw in menus:
            tab = getattr(self, f"{tab_key}_tab")
            if menu_text is None:
                self._routes[nav_key] = (tab, None)
            else:
                menu = self._build_locator(page, menu_text, kw or {})
                self._routes[nav_key] = (tab, menu)

    @staticmethod
    def _build_locator(page: Page, text: str, kw: dict):
        if "role" in kw:
            return page.get_by_role(kw["role"], name=text)
        if "css" in kw:
            return page.locator(kw["css"]).get_by_text(text)
        return page.get_by_text(text, exact=kw.get("exact", False))

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
                if menu is None:
                    return lambda: tab.click()
                return lambda: self._click_menu(tab, menu)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )
