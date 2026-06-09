import re
from collections import Counter
from io import BytesIO
from typing import TypedDict

import ddddocr
from PIL import Image, ImageEnhance, ImageFilter
from playwright.sync_api import Page, Error as PlaywrightError, Position

type BoundingBox = tuple[int, int, int, int]
type CenterPoint = tuple[float, float]

class DetectionResult(TypedDict):
    char: str
    box: BoundingBox
    center: CenterPoint


_det = ddddocr.DdddOcr(det=True, ocr=False, show_ad=False)
_ocr = ddddocr.DdddOcr(show_ad=False)

try:
    _ocr_beta = ddddocr.DdddOcr(beta=True, show_ad=False)
except (RuntimeError, OSError, ValueError):
    _ocr_beta = None


def _parse_click_order(instruction_text: str) -> list[str]:

    if not (match := re.search(r'【(.+?)】', instruction_text)):
        raise ValueError(f"无法解析点击顺序: {instruction_text}")
        
    content = match.group(1)
    chars = re.split(r'[、，,]', content)
    return [c.strip() for c in chars if c.strip()]

def _preprocess_for_detection(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes))
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_crop_variants(crop: Image.Image) -> list[bytes]:
    min_size = 64

    w, h = crop.size
    if w < min_size or h < min_size:
        scale = max(min_size / w, min_size / h)
        crop = crop.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    def _to_bytes(im: Image.Image) -> bytes:
        b = BytesIO()
        im.save(b, format="PNG")
        return b.getvalue()

    variants = [
        _to_bytes(crop),
        _to_bytes(ImageEnhance.Contrast(crop.convert("L").convert("RGB")).enhance(2.0)),
        _to_bytes(ImageEnhance.Contrast(ImageEnhance.Sharpness(crop).enhance(3.0)).enhance(1.8)),
        _to_bytes(ImageEnhance.Contrast(crop.filter(ImageFilter.MedianFilter(3))).enhance(1.5)),
    ]
    return variants

def _vote_ocr(variants: list[bytes]) -> str:
    engines = [_ocr] + ([_ocr_beta] if _ocr_beta else [])
    votes: list[str] = []

    for img_bytes in variants:
        for engine in engines:
            try:
                res = engine.classification(img_bytes)
                char = res.strip() if isinstance(res, str) else str(res)
                if char:
                    votes.append(char)
            except (RuntimeError, OSError, ValueError):
                continue

    if not votes:
        return ""

    most_common: str = Counter(votes).most_common(1)[0][0]
    return most_common

def _iou(box_a: list[int | float], box_b: list[int | float]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter == 0:
        return 0.0

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return inter / (area_a + area_b - inter)


def _merge_bboxes(bboxes_a: list, bboxes_b: list, iou_threshold: float = 0.5) -> list:
    merged = list(bboxes_a)
    for box_b in bboxes_b:
        if not any(_iou(box_a, box_b) > iou_threshold for box_a in merged):
            merged.append(box_b)
    return merged

def _detect_and_recognize(image_bytes: bytes) -> list[DetectionResult]:
    processed = _preprocess_for_detection(image_bytes)

    # 双重检测 + IoU 去重合并
    bboxes_raw = _det.detection(image_bytes)
    bboxes_processed = _det.detection(processed)
    all_bboxes = _merge_bboxes(bboxes_raw, bboxes_processed)

    img = Image.open(BytesIO(image_bytes))

    results: list[DetectionResult] = []
    pad = 8

    for box in all_bboxes:
        x1, y1, x2, y2 = box
        crop = img.crop((
            max(0, x1 - pad), max(0, y1 - pad),
            min(img.width, x2 + pad), min(img.height, y2 + pad)
        ))

        variants = _build_crop_variants(crop)
        char = _vote_ocr(variants)

        if not char:
            continue

        results.append({
            "char": char,
            "box": (x1, y1, x2, y2),
            "center": ((x1 + x2) / 2, (y1 + y2) / 2)
        })

    return results

def _find_best_match(
    target: str,
    detected: list[DetectionResult],
    used_indices: set[int],
) -> int | None:
    """
    为目标字符找到最佳匹配的检测结果索引
    """
    for priority_fn in [
        lambda t, c: c == t,            # 完全匹配
        lambda t, c: t in c,            # 目标在结果中
        lambda t, c: c in t and c,      # 结果在目标中
    ]:
        for i, d in enumerate(detected):
            if i not in used_indices and priority_fn(target, d["char"]):
                return i
    return None

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

            if not (canvas_box := canvas.bounding_box()):
                continue
                
            scale_x = canvas_box["width"] / pixel_width
            scale_y = canvas_box["height"] / pixel_height

            detected = _detect_and_recognize(screenshot_bytes)
            print(f"[验证码] 检测到: {[(d['char'], d['center']) for d in detected]}")

            click_success = True
            used_indices: set[int] = set()

            for target in target_chars:
                matched_idx = _find_best_match(target, detected, used_indices)

                if matched_idx is not None:
                    used_indices.add(matched_idx)
                    matched = detected[matched_idx]
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
                # 未识别到所有答案，手动点击刷新按钮
                print("[验证码] 未识别到所有答案，手动刷新验证码")
                _try_refresh(page)
                continue

            page.wait_for_timeout(2000)
            try:
                canvas.wait_for(state="hidden", timeout=5000)
                print("[验证码] 验证成功！")
                return True
            except PlaywrightError as e:
                print(f"[验证码] 第 {attempt + 1} 次验证未通过: {e}")
                print("[验证码] 等待1秒后自动刷新验证码")
                page.wait_for_timeout(1000)

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