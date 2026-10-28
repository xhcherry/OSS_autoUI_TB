"""UI 操作步骤日志：将每一步 UI 操作打印到 stdout。
通过给 Playwright 的 Page / Locator / Keyboard 类方法打补丁，在执行点击、
输入等用户可见操作前打印一行中文日志（配合 pytest -s 输出到控制台），
使无头模式 / CI / 测试平台下也能看到每一步点了什么。
采用类级补丁而非对象代理，保证 expect() 等断言收到的仍是真实 Locator。
"""
import re
import time
from typing import Any
from playwright.sync_api import Keyboard, Locator, Page, Error as PlaywrightError

# Locator 级动作 → 中文动词
_LOCATOR_ACTIONS: dict[str, str] = {
    "click": "点击",
    "dblclick": "双击",
    "fill": "输入",
    "type": "键入",
    "press_sequentially": "键入",
    "press": "按键",
    "hover": "悬停",
    "check": "勾选",
    "uncheck": "取消勾选",
    "select_option": "选择下拉选项",
    "set_input_files": "上传文件",
    "drag_to": "拖拽到",
}

# Page 级动作 → 中文动词（旧式 selector 写法，部分用例可能使用）
_PAGE_ACTIONS: dict[str, str] = {
    "goto": "打开页面",
    "click": "点击",
    "dblclick": "双击",
    "fill": "输入",
    "hover": "悬停",
    "press": "按键",
}

# Keyboard 级动作 → 中文动词
_KEYBOARD_ACTIONS: dict[str, str] = {
    "press": "按键",
    "insert_text": "插入文本",
}

_installed = False


def _log_step(verb: str, detail: str) -> None:
    """打印步骤日志到 stdout（需 pytest -s 关闭输出捕获）。"""
    print(f"[步骤] {time.strftime('%H:%M:%S')} {verb} {detail}", flush=True)


def _quote(text: str, limit: int = 30) -> str:
    """给可读描述加上「」并截断。"""
    text = text.strip()
    return f"「{text[:limit]}」" if len(text) <= limit else f"「{text[:limit - 3]}...」"


# selector 清洗：把 Playwright 内部选择器翻译成人类可读描述

_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")
_SELECTOR_REPR = re.compile(r"""selector=(['"])(.+)\1""")
_INTERNAL_LABEL = re.compile(r'internal:label="([^"]*)"')
_INTERNAL_ROLE_NAME = re.compile(r'internal:role=[\w-]+\[name="([^"]*)"')
_INTERNAL_TEXT = re.compile(r'internal:text="([^"]*)"')
_INTERNAL_ROLE = re.compile(r"internal:role=[\w-]+")
_NTH = re.compile(r"nth=(\d+)")
_REQUIRED_STAR = re.compile(r"^\*\s*")


def _clean_name(text: str) -> str:
    """解码 Playwright 对中文生成的 \\uXXXX 转义，并去掉必填星号前缀。"""
    text = _UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), text)
    return _REQUIRED_STAR.sub("", text).strip()


def _humanize_part(part: str) -> str:
    """将一段 selector 片段转为可读描述；iframe/控制段等技术噪声返回空串。"""
    part = part.strip()
    if not part:
        return ""
    # iframe 入口、进入 frame 的控制段属于技术细节，直接丢弃
    if part.startswith("internal:control"):
        return ""
    if part.startswith("#") and "iframe" in part.lower():
        return ""
    for pattern in (_INTERNAL_LABEL, _INTERNAL_ROLE_NAME, _INTERNAL_TEXT):
        m = pattern.search(part)
        if m:
            return _clean_name(m.group(1))
    if _INTERNAL_ROLE.search(part):
        return ""  # 无 name 的 role 段（如 paragraph）没有有效业务信息
    if part.startswith("[contenteditable"):
        return "可编辑区域"
    if part.startswith(("#", ".")):
        return part[1:]
    return part


def _humanize_selector(raw: str) -> str:
    """把 Playwright 内部 selector / Locator repr 转成人类可读描述。"""
    s = raw.strip()
    # 形如 <Locator frame=<Frame ...> selector="...">：先提取 selector 值
    if "<Locator" in s or "<Frame" in s:
        m = _SELECTOR_REPR.search(s)
        if m:
            s = m.group(2)
    if s.startswith("Locator: "):
        s = s[len("Locator: "):]
    out: list[str] = []
    for piece in s.split(">>"):
        m = _NTH.fullmatch(piece.strip())
        if m and out:  # nth 是前一段的序号修饰
            out[-1] += f"(第{int(m.group(1)) + 1}个)"
            continue
        text = _humanize_part(piece)
        if text:
            out.append(text)
    return " > ".join(out) if out else s


def _locator_desc(locator: Any) -> str:
    """尝试获取元素 placeholder/aria-label/文本作为可读描述，失败则回退到清洗后的 selector。"""
    # input/textarea 无文本内容，优先取 placeholder/name；其余元素取 aria-label/title
    try:
        attr = locator.evaluate(
            """el => {
                const t = el.tagName.toLowerCase();
                if (t === 'input' || t === 'textarea') {
                    return el.getAttribute('placeholder') || el.name || '';
                }
                return el.getAttribute('aria-label') || el.getAttribute('title') || '';
            }""",
            timeout=200,
        )
        if attr:
            return _quote(attr)
    except PlaywrightError:
        pass

    try:
        txt = locator.text_content(timeout=200)
        if txt and txt.strip():
            return _quote(" ".join(txt.split()))
    except PlaywrightError:
        pass

    try:
        return _humanize_selector(str(locator))
    except (TypeError, ValueError):
        return ""


def _describe(name: str, target: Any, args: tuple, kwargs: dict) -> str:
    """根据动作类型生成日志描述，target 为 Locator 时附带元素文本。"""
    is_locator = hasattr(target, "text_content")

    if name == "goto":
        return args[0] if args else str(kwargs.get("url", ""))
    if name == "drag_to":
        return _locator_desc(args[-1]) if args else ""
    if name == "press":
        key = args[-1] if args else kwargs.get("key", "")
        return f"「{key}」"

    if name in ("fill", "type", "press_sequentially", "insert_text"):
        value = str(args[-1] if args else kwargs.get("value", ""))[:30]
        base = _locator_desc(target) if is_locator else (_humanize_selector(args[0]) if args else "")
        return f"「{value}」→ {base}" if base else f"「{value}」"
    if name == "select_option":
        v = args[-1] if args else kwargs.get("value", "")
        base = _locator_desc(target) if is_locator else ""
        return f"选项「{v}」→ {base}" if base else f"选项「{v}」"

    # click / dblclick / hover / check / uncheck / set_input_files
    if is_locator:
        return _locator_desc(target)
    return _humanize_selector(args[0]) if args else ""


def _patch(cls: type, actions: dict[str, str]) -> None:
    """给目标类的方法打上日志补丁（跳过已打过补丁的方法）。"""
    for name, verb in actions.items():
        original = getattr(cls, name, None)
        if original is None or getattr(original, "_step_logged", False):
            continue

        def make_wrapper(orig, action_name, action_verb):
            def wrapper(self, *args, **kwargs):
                _log_step(action_verb, _describe(action_name, self, args, kwargs))
                return orig(self, *args, **kwargs)
            wrapper._step_logged = True
            return wrapper

        setattr(cls, name, make_wrapper(original, name, verb))


def install_step_logger() -> None:
    """幂等地安装步骤日志补丁（可重复调用，线程安全由 GIL 保证）。"""
    global _installed
    if _installed:
        return
    _patch(Locator, _LOCATOR_ACTIONS)
    _patch(Page, _PAGE_ACTIONS)
    _patch(Keyboard, _KEYBOARD_ACTIONS)
    _installed = True
