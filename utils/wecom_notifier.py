import json
import urllib.request
from datetime import datetime
from typing import Any


class WeComNotifier:
    """企业微信机器人 Webhook 通知工具。"""

    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise ValueError("webhook_url 不能为空")
        self._url = webhook_url

    def send_markdown(self, content: str) -> dict[str, Any]:
        """发送 Markdown 消息到企业微信群机器人。"""
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("errcode", 0) != 0:
            raise RuntimeError(f"企微 API 错误: {result}")
        return result


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    if seconds < 3600:
        return f"{int(seconds // 60)} 分 {int(seconds % 60)} 秒"
    return f"{int(seconds // 3600)} 时 {int((seconds % 3600) // 60)} 分"


def build_test_report_markdown(
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    error: int,
    severity_failures: dict[str, int] | None = None,
    duration_seconds: float = 0,
    report_dir: str = "",
) -> str:
    """组装测试报告 Markdown 消息体。

    severity_failures: 各严重级别失败数，如 {"p0": 0, "p1": 2, "p2": 1, "p3": 0}
    report_dir:        report/ 下的 allure 结果目录名
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pass_rate = f"{passed / total * 100:.1f}%" if total > 0 else "N/A"

    # 状态图标 & 文案
    if failed > 0 and severity_failures and severity_failures.get("p0", 0) > 0:
        status = '❌ <font color="warning">P0 级失败，请立即处理！</font>'
    elif failed > 0 and severity_failures and severity_failures.get("p1", 0) > 0:
        status = '❌ <font color="warning">P1 级失败，请尽快处理</font>'
    elif failed > 0:
        status = "❌ 测试未通过"
    else:
        status = "✅ 全部通过"

    md = (
        f"# UI自动化测试报告\n\n"
        f"> 执行时间：{now}\n"
        f"> 耗时：{_format_duration(duration_seconds)}\n\n"
        f"**结果概览**：{status}\n\n"
        f"> 总计：{total}\n"
        f'> 通过：<font color="info">{passed}</font>\n'
        f'> 失败：<font color="warning">{failed}</font>\n'
        f'> 跳过：<font color="comment">{skipped}</font>\n'
        f'> 错误：<font color="warning">{error}</font>\n'
        f"> 通过率：{pass_rate}\n"
    )

    if severity_failures and failed > 0:
        md += "\n**失败严重级别分布**：\n\n"
        for sev in ("p0", "p1", "p2", "p3"):
            count = severity_failures.get(sev, 0)
            color = "warning" if sev in ("p0", "p1") else "comment"
            md += f'> {sev.upper()}：<font color="{color}">{count}</font> 条\n'

    if report_dir:
        md += f"\n> 报告目录：report/{report_dir}\n"

    return md
