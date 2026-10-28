import random

from playwright.sync_api import Page, Locator, Error as PlaywrightError


def _drag_slider_to_right(
    page: Page,
    slider_locator: Locator,
    track_locator: Locator,
    max_retries: int,
) -> bool:
    """模拟人类拖拽行为将滑块从轨道左侧拖到最右侧，支持重试。"""
    for attempt in range(max_retries):
        try:
            slider_locator.first.wait_for(state="visible", timeout=5000)
            # 滑块弹层有滑入动画，短暂稳定后再取坐标（防抖，非业务等待）
            page.wait_for_timeout(150)

            slider_box = slider_locator.first.bounding_box()
            track_box = track_locator.first.bounding_box()
            if not slider_box or not track_box:
                print(f"[滑块验证] 第 {attempt + 1} 次：无法获取滑块或轨道位置")
                continue

            start_x = slider_box["x"] + slider_box["width"] / 2
            start_y = slider_box["y"] + slider_box["height"] / 2
            end_x = track_box["x"] + track_box["width"] - slider_box["width"] / 2
            distance = end_x - start_x

            print(f"[滑块验证] 第 {attempt + 1} 次：拖拽距离 {distance:.0f}px")

            page.mouse.move(start_x, start_y)
            page.mouse.down()

            # 模拟人类拖拽：ease-out 快滑 + 纵向微抖动，
            # "拖到最右"型滑块实测快速匀加速拖动可通过风控
            steps = 5
            for i in range(1, steps + 1):
                progress = i / steps
                # ease-out 缓动：前半段快，后半段慢
                eased = 1 - (1 - progress) ** 2
                jitter_y = random.uniform(-1.0, 1.0)
                page.mouse.move(
                    start_x + distance * eased,
                    start_y + jitter_y,
                    steps=1,
                )
                page.wait_for_timeout(random.randint(2, 5))

            page.mouse.up()

            # 验证成功信号：滑块元素消失
            # （wait_for 内部即按后端校验耗时轮询，无需前置固定等待）
            try:
                slider_locator.first.wait_for(state="hidden", timeout=5000)
                print("[滑块验证] 验证成功！")
                return True
            except PlaywrightError:
                print(f"[滑块验证] 第 {attempt + 1} 次验证未通过，重试中...")
                page.wait_for_timeout(1000)

        except (PlaywrightError, ValueError) as e:
            print(f"[滑块验证] 第 {attempt + 1} 次运行出错: {e}")
            page.wait_for_timeout(1000)

    print("[滑块验证] 超过最大重试次数")
    return False


def solve_slide_captcha(page: Page, max_retries: int = 3) -> bool:
    """自动完成登录滑块拖拽验证（ls-slide-verify 组件，role=slider）。"""
    return _drag_slider_to_right(
        page,
        page.get_by_role("slider"),
        page.locator(".ls-slide-verify__track"),
        max_retries,
    )
