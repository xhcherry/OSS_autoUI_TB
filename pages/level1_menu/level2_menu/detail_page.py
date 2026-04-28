from pages.base_page import BasePage


class DetailPage(BasePage):
    """
    【页面】详情页
    点击列表中的名字后进入的页面
    """

    def __init__(self, page):
        super().__init__(page)

        # 1. 详情页的校验元素

        # 2. 详情页的业务按钮

        # 3. 详情页的 Tab

    def get_detail_name_title(self):
        """获取页面顶部的名字，用于断言"""
        # 假设详情页有个 h2 或 h3 显示名字
        return self.page.locator("h3.detail-name").text_content()