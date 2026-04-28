import re
from io import BytesIO
from typing import TypedDict

import ddddocr
from PIL import Image
from playwright.sync_api import Page, Error as PlaywrightError, Position

type BoundingBox = tuple[int, int, int, int]
type CenterPoint = tuple[float, float]

class DetectionResult(TypedDict):
    char: str
    box: BoundingBox
    center: CenterPoint


# 全局初始化 OCR 实例（避免重复初始化，提升性能）
_det = ddddocr.DdddOcr(det=True, ocr=False, show_ad=False)
_ocr = ddddocr.DdddOcr(show_ad=False)


def _parse_click_order(instruction_text: str) -> list[str]:
    """从提示文字中解析需要点击的字符顺序"""
    
    # 🌟 Python 3.8+ 新特性：海象运算符 (:=)，边赋值边判断，省去冗余代码
    if not (match := re.search(r'【(.+?)】', instruction_text)):
        raise ValueError(f"无法解析点击顺序: {instruction_text}")
        
    content = match.group(1)
    chars = re.split(r'[、，,]', content)
    return [c.strip() for c in chars if c.strip()]


def _detect_and_recognize(image_bytes: bytes) -> list[DetectionResult]:
    """检测图片中所有字符的位置"""
    bboxes = _det.detection(image_bytes)
    img = Image.open(BytesIO(image_bytes))

    results: list[DetectionResult] = []
    for box in bboxes:
        x1, y1, x2, y2 = box
        pad = 4
        crop = img.crop((
            max(0, x1 - pad), max(0, y1 - pad),
            min(img.width, x2 + pad), min(img.height, y2 + pad)
        ))
        buf = BytesIO()
        crop.save(buf, format="PNG")
        
        res = _ocr.classification(buf.getvalue())
        char = res.strip() if isinstance(res, str) else str(res)

        # 构建标准的返回值
        results.append({
            "char": char,
            "box": (x1, y1, x2, y2),
            "center": ((x1 + x2) / 2, (y1 + y2) / 2)
        })

    return results


def solve_click_captcha(page: Page, max_retries: int = 3) -> bool:
    """自动识别并解决点选验证码（canvas 类型）"""
    for attempt in range(max_retries):
        try:
            canvas = page.locator("canvas")
            canvas.wait_for(state="visible", timeout=10000)

            instruction_locator = page.locator("text=/请依次点击/").first
            instruction_locator.wait_for(state="visible", timeout=500)
            page.wait_for_timeout(500)

            instruction_text = instruction_locator.text_content() or ""
            print(f"[验证码] 第 {attempt + 1} 次尝试，提示: {instruction_text}")

            target_chars = _parse_click_order(instruction_text)
            print(f"[验证码] 需要依次点击: {target_chars}")

            screenshot_bytes = canvas.screenshot()
            
            img_for_size = Image.open(BytesIO(screenshot_bytes))
            pixel_width, pixel_height = img_for_size.size

            if not (canvas_box := canvas.bounding_box()): # 🌟 再次使用海象运算符精简检查逻辑
                continue
                
            scale_x = canvas_box["width"] / pixel_width
            scale_y = canvas_box["height"] / pixel_height

            detected = _detect_and_recognize(screenshot_bytes)
            print(f"[验证码] 检测到: {[(d['char'], d['center']) for d in detected]}")

            click_success = True
            for target in target_chars:
                matched = None
                for d in detected:
                    if target in d["char"] or d["char"] in target:
                        matched = d
                        break
                        
                if matched:
                    cx, cy = matched["center"]
                    target_x = cx * scale_x
                    target_y = cy * scale_y
                    print(f"[验证码] 点击 '{target}' -> 物理:({cx:.0f}, {cy:.0f}), CSS:({target_x:.0f}, {target_y:.0f})")
                    
                    pos: Position = {"x": target_x, "y": target_y}
                    canvas.click(position=pos)
                    page.wait_for_timeout(300)
                else:
                    print(f"[验证码] 未识别到字符 '{target}'")
                    click_success = False
                    break

            if not click_success:
                _try_refresh(page)
                continue

            page.wait_for_timeout(2000)
            try:
                canvas.wait_for(state="hidden", timeout=5000)
                print("[验证码] 验证成功！")
                return True
            except PlaywrightError as e:
                print(f"[验证码] 第 {attempt + 1} 次验证未通过: {e}")
                _try_refresh(page)

        except (PlaywrightError, ValueError, RuntimeError) as e:
            print(f"[验证码] 第 {attempt + 1} 次运行出错: {e}")
            _try_refresh(page)

    print("[验证码] 超过最大重试次数")
    return False


def _try_refresh(page: Page) -> None:
    """点击刷新按钮重试"""
    try:
        page.locator(".verify-refresh").click(timeout=2000)
        page.wait_for_timeout(1000)
    except PlaywrightError:
        pass