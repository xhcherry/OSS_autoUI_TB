from playwright.sync_api import Page

# (一级 tab key, 二级菜单文本, navigate 方法名, 定位器配置)
# menu_text=None 表示只点击一级 tab，无二级菜单
# kwarg: exact=True / role="menuitem" / css="#selector"
_MENUS = [
    # 一级菜单1
    ("home", None, "home", None),
    # 一级菜单2"
    ("brand", "二级菜单1", "menu_leavel2", None),
]

# 一级 Tab：中文名 → 属性 key
_TABS = {
    "一级菜单1": "home", "一级菜单2": "brand", 
}


class Header:
    """
    导航至指定的二级菜单的管理页面。
    - Tab 定位器自动生成：self.{key}_tab
    - 菜单定位器自动生成：self.{nav_key}_menu
    - 导航方法自动解析：self.navigate_to_{nav_key}()
    """

    def __init__(self, page: Page):
        self.page = page

        # 1. 自动生成一级 Tab 定位器
        for name, key in _TABS.items():
            setattr(self, f"{key}_tab", page.get_by_text(name).first)

        # 2. 独立定位器（非菜单项）
        self.collapse = page.get_by_text("收起")

        # 3. 自动生成二级菜单定位器 + 构建路由表
        self._routes = {}
        for tab_key, menu_text, nav_key, kw in _MENUS:
            tab = getattr(self, f"{tab_key}_tab")
            if menu_text is None:
                self._routes[nav_key] = (tab, None)
            else:
                menu = self._build_locator(page, menu_text, kw or {})
                self._routes[nav_key] = (tab, menu)

    def _build_locator(self, page: Page, text: str, kw: dict):
        """根据配置构建二级菜单定位器"""
        if "role" in kw:
            return page.get_by_role(kw["role"], name=text)
        if "css" in kw:
            return page.locator(kw["css"]).get_by_text(text)
        return page.get_by_text(text, exact=kw.get("exact", False))

    def _click_menu(self, primary_tab, secondary_menu):
        if not secondary_menu.is_visible():
            primary_tab.click()
        secondary_menu.click()

    def __getattr__(self, name):
        if name.startswith("navigate_to_"):
            key = name[len("navigate_to_"):]
            route = self._routes.get(key)
            if route is not None:
                tab, menu = route
                if menu is None:
                    return lambda: tab.click()
                return lambda: self._click_menu(tab, menu)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
