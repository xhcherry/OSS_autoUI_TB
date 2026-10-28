import re

from playwright.sync_api import Page, Error as PlaywrightError
from config.settings import Config
from pages.header import AdminHeader, Header, SubHeader
from utils.step_logger import install_step_logger

class BasePage:
    """页面对象基类。

    platform 参数决定懒加载哪个平台的 Header：
    - "default"：主平台标准布局（Header）
    - "alt"   ：主平台备用布局（Header，菜单不同）
    - "admin" ：管理后台（AdminHeader）
    - "sub"   ：子系统（SubHeader）
    """

    def __init__(self, page: Page, platform: str = "default"):
        # 安装步骤日志补丁：每一步 UI 操作打印到控制台（无头/服务器运行也能看到步骤）
        install_step_logger()
        self.page = page
        self._platform = platform
        self._header = None

        # 通用元素（各页面共享的结构定位器，测试层断言统一从这里取）
        self.loading_mask = page.locator(".el-loading-mask").first
        self.table_rows = page.locator(".el-table__row")
        self.first_table = page.get_by_role("table").first
        self.first_menuitem = page.get_by_role("menuitem").first
        self.last_dialog = page.get_by_role("dialog").last
        # 页面报错文案
        self.error_text = page.get_by_text(
            re.compile(r"错误|请求的资源不存在|获取数据失败，请稍后重试")
        )

    def text_item(self, text: str, exact: bool = False):
        """按文本定位元素（动态业务数据的可见性断言用，文本为数据而非选择器）"""
        return self.page.get_by_text(text, exact=exact)

    def toast_item(self, keyword: str):
        """按关键词定位 el-message 提示条"""
        return self.page.locator(".el-message").filter(has_text=keyword).first

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
        """纯导航：进入本页（默认 BASE_URL）+ 由子类扩展就绪等待。

        语义固定为「进入本页」，禁止切 Tab 与业务前置；
        业务页面应覆盖本方法补充就绪处理。
        """
        self.page.goto(url or Config.BASE_URL)

    def _trigger_hover(self, filter_text: str, trigger_text: str):
        # :visible 过滤隐藏抽屉/浮层内的同名行（如常驻 el-modal-drawer 内表格），
        # 否则 .first 可能命中隐藏行导致 hover 被其 overlay 拦截
        target_row = self.page.locator("tr:visible").filter(has_text=filter_text)
        operation_btn = target_row.get_by_text(trigger_text).first
        operation_btn.hover()

    def hover_operation(self, filter_text: str, trigger_text: str = "操作"):
        self._trigger_hover(filter_text, trigger_text)

    def hover_more(self, filter_text: str, trigger_text: str = "更多"):
        self._trigger_hover(filter_text, trigger_text)

    def hover_trial(self, filter_text: str, trigger_text: str = "试听"):
        self._trigger_hover(filter_text, trigger_text)

    def wait_success_toast(self, keyword: str = "成功", timeout: int = 10000):
        """等待成功 toast（.el-message 含关键词）出现，替代操作后的硬等待。

        用于「点击保存/添加/删除等按钮后，以成功提示作为操作完成信号」的场景。
        """
        toast = self.page.locator(".el-message").filter(has_text=keyword).last
        toast.wait_for(state="visible", timeout=timeout)

    def wait_toast(self, keyword: str, timeout: int = 10000):
        """等待含指定关键词的 toast 出现（不限于成功提示）"""
        toast = self.page.locator(".el-message").filter(has_text=keyword).last
        toast.wait_for(state="visible", timeout=timeout)

    def wait_loading_done(self, timeout: int = 10000):
        """等待 loading 遮罩消失（列表/页面加载完成信号）。无遮罩时直接返回。"""
        try:
            mask = self.page.locator(".el-loading-mask").first
            mask.wait_for(state="visible", timeout=500)
            mask.wait_for(state="hidden", timeout=timeout)
        except PlaywrightError:
            pass

    def wait_frame_loading(self, scope, timeout: int = 10000):
        """等待嵌入应用 frame 内的 loading 消失（自研组件遮罩，如 .ls-loading）。

        scope 传 Frame 或任意 Locator 作用域；
        遮罩未出现时不阻塞（快路径直接返回）。
        """
        try:
            mask = scope.locator(".ls-loading, .loadingMask").first
            mask.wait_for(state="visible", timeout=500)
            mask.wait_for(state="hidden", timeout=timeout)
        except PlaywrightError:
            pass

    def wait_frame_toast(self, scope, keyword: str = "成功", timeout: int = 10000):
        """等待 frame 内的 toast（.el-message 含关键词）出现。

        嵌入 iframe 应用的 toast 渲染在 iframe document 内，
        顶层 page 的 wait_success_toast / wait_toast 查不到。
        """
        toast = scope.locator(".el-message").filter(has_text=keyword).last
        toast.wait_for(state="visible", timeout=timeout)

    def fill_and_search(self, search_input, keyword: str, retry: int = 2):
        """在搜索框输入关键字并回车，带竞态重试。

        搜索组件的值多为防抖 watcher，fill 后立即回车会以「空关键字」
        发出请求导致空结果；以「结果行出现」为业务信号，未出结果时重试
        （重试前清空重输）。搜索目标本就不存在时，重试次数用尽后返回
        （由调用方断言兜底）。
        """
        for _ in range(retry):
            search_input.fill(keyword)
            search_input.press("Enter")
            try:
                self.page.locator(".el-table__row").first.wait_for(
                    state="visible", timeout=5000
                )
                return
            except PlaywrightError:
                continue

    def dismiss_dialog_if_present(self, timeout: int = 1000):
        """尝试关闭可能存在的对话框。

        依次尝试：
        1. 点击"我知道了"按钮（导出提示弹窗）
        2. 检查弹窗是否存在 → 直接返回（无弹窗不按 Escape）
        3. 点击关闭按钮（X 图标）→ 验证弹窗已关闭
        4. 点击"取消"按钮 → 验证弹窗已关闭
        5. 点击"关闭"按钮 → 验证弹窗已关闭
        6. 按 Escape → 验证弹窗已关闭
        7. JS 点击关闭/取消按钮 → 验证弹窗已关闭

        不使用 JS 隐藏 overlay：会导致 Vue 状态不一致，后续页面元素可能不再渲染。
        """
        # 1. 尝试点击"我知道了"
        try:
            know_btn = self.page.get_by_role("button", name="我知道了")
            know_btn.wait_for(state="visible", timeout=timeout)
            know_btn.click(force=True)
            try:
                know_btn.wait_for(state="hidden", timeout=2000)
            except PlaywrightError:
                pass
            return
        except PlaywrightError:
            pass

        # 2. 检查是否有弹窗（500ms 超时）
        try:
            dialog = self.page.get_by_role("dialog").last
            dialog.wait_for(state="visible", timeout=500)
        except PlaywrightError:
            # 没有弹窗，直接返回（不按 Escape，避免副作用）
            return

        # 3. 弹窗存在，尝试多种方式关闭，每次关闭后验证
        # 3a. 关闭按钮 (X)
        try:
            close_btn = dialog.locator(".el-dialog__headerbtn, .el-icon-close, .close-icon").last
            close_btn.wait_for(state="visible", timeout=1000)
            close_btn.click(force=True)
            try:
                dialog.wait_for(state="hidden", timeout=2000)
                return
            except PlaywrightError:
                pass  # 弹窗未关闭，继续尝试其他方式
        except PlaywrightError:
            pass

        # 3b. "取消" 按钮
        try:
            cancel_btn = dialog.get_by_role("button", name="取消")
            cancel_btn.wait_for(state="visible", timeout=1000)
            cancel_btn.click(force=True)
            try:
                dialog.wait_for(state="hidden", timeout=2000)
                return
            except PlaywrightError:
                pass
        except PlaywrightError:
            pass

        # 3c. "关闭" 按钮
        try:
            close_text_btn = dialog.get_by_role("button", name="关闭")
            close_text_btn.wait_for(state="visible", timeout=1000)
            close_text_btn.click(force=True)
            try:
                dialog.wait_for(state="hidden", timeout=2000)
                return
            except PlaywrightError:
                pass
        except PlaywrightError:
            pass

        # 4. 尝试按 Escape（单次）
        try:
            self.page.keyboard.press("Escape")
            try:
                dialog.wait_for(state="hidden", timeout=2000)
                return
            except PlaywrightError:
                pass
        except PlaywrightError:
            pass

        # 5. JS 点击关闭/取消按钮（正确触发 Vue 关闭逻辑）
        try:
            closed = self.page.evaluate("""() => {
                const closeBtns = document.querySelectorAll('.el-dialog__headerbtn, .el-icon-close, .close-icon');
                for (const btn of closeBtns) {
                    if (btn.offsetParent !== null) { btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true})); return true; }
                }
                const btns = document.querySelectorAll('[role="dialog"] button, .el-drawer button');
                for (const btn of btns) {
                    const text = btn.textContent.trim();
                    if ((text === '取消' || text === '关闭') && btn.offsetParent !== null) {
                        btn.click(); return true;
                    }
                }
                return false;
            }""")
            if closed:
                try:
                    dialog.wait_for(state="hidden", timeout=2000)
                except PlaywrightError:
                    pass
        except PlaywrightError:
            pass
