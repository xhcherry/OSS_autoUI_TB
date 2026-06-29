"""
约课相关辅助工具
- pick_random_available_time_slots: 在约课时间表中随机点击 N 个「可约」（绿色）时间格
"""

import random
import time

# 在页面 DOM 中查找所有"可约"（绿色背景）时间格，并打上临时标记 data-auto-pick-slot
# 完全不依赖时间文本格式（hh:mm~hh:mm / hh:mm～hh:mm 都可），仅靠样式颜色识别。
_MARK_AVAILABLE_SLOTS_JS = r"""
() => {
  // 清除上一次的标记，避免脏数据
  document.querySelectorAll('[data-auto-pick-slot]').forEach(
    el => el.removeAttribute('data-auto-pick-slot')
  );

  const isGreen = (rgb) => {
    const m = rgb && rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) return false;
    const r = +m[1], g = +m[2], b = +m[3];
    // 绿色判定：G 显著高于 R 与 B
    return g > r && g > b && (g - Math.max(r, b)) >= 15;
  };

  const candidates = [];
  document.querySelectorAll('*').forEach(el => {
    const rect = el.getBoundingClientRect();
    // 时间格大小约束（时间格通常宽 60~150px、高 20~50px），过滤掉大容器与图标
    if (rect.width < 40 || rect.width > 220) return;
    if (rect.height < 18 || rect.height > 80) return;
    // 必须可见
    if (rect.width === 0 || rect.height === 0) return;
    const text = (el.innerText || '').trim();
    if (!text) return;
    // 时间格通常含 ~ 或 ～
    if (!/[~～]/.test(text)) return;
    // 优先选叶子节点（避免父容器把整列都选中）
    if (el.children && el.children.length > 0) return;

    // 背景色（向上回溯第一个非透明）
    let bg = '';
    let n = el;
    while (n) {
      const c = getComputedStyle(n).backgroundColor;
      if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') { bg = c; break; }
      n = n.parentElement;
    }
    if (isGreen(bg)) candidates.push(el);
  });

  candidates.forEach((el, i) => el.setAttribute('data-auto-pick-slot', String(i)));
  return candidates.length;
}
"""


def pick_random_available_time_slots(
    page,
    count: int = 2,
    timeout: float = 15.0,
    poll_interval: float = 0.5,
) -> list[int]:
    """
    在约课时间表中随机点击 count 个「可约」时间格。

    识别策略：纯粹基于背景色（绿色 = 可约），不依赖具体时间文本格式，
    可兼容不同时长的时间格（10 分钟 / 20 分钟 / 不定长 等）。

    等待策略：约课页加载较慢，函数会在 timeout 内轮询，直到可约时间格数
    量 >= count 才进行随机选择。

    :param page: Playwright Page 实例
    :param count: 需要选择的可约时间数量
    :param timeout: 等待可约时间加载的最大秒数
    :param poll_interval: 轮询间隔秒数
    :return: 实际被点击的标记索引列表
    :raises RuntimeError: 超过 timeout 后仍不足 count 个可约时间时
    """
    deadline = time.monotonic() + timeout
    total = 0
    while True:
        total = page.evaluate(_MARK_AVAILABLE_SLOTS_JS)
        if total >= count:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError(f"可约时间不足 {count} 个，当前仅 {total} 个（已等待 {timeout}s）")
        page.wait_for_timeout(int(poll_interval * 1000))

    chosen = random.sample(range(total), count)
    for idx in chosen:
        page.locator(f"[data-auto-pick-slot='{idx}']").click()
    return chosen
