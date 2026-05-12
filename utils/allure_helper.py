import os
from datetime import datetime


def generate_allure_report_dir():
    """
    生成带时间戳的 allure 报告目录（项目根目录下的 report/ 文件夹）
    供 runner.py 和 conftest.py 共用
    """
    # 项目根目录 = utils/ 的上一级
    project_root = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = os.path.join(project_root, 'report', f'allure-results-{timestamp}')
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def attach_screenshot(page, name="截图"):
    """将 Playwright page 的截图附加到 Allure 报告中"""
    if page is None:
        return
    import allure
    allure.attach(
        page.screenshot(full_page=True),
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def attach_text(content, name="文本内容", print_to_console=True):
    """
    将文本附加到 Allure 报告，并可选打印到控制台

    :param content: 要附加的文本内容
    :param name: 报告中显示的名称
    :param print_to_console: 是否同步打印到控制台
    """
    if content is None:
        return
    import allure
    allure.attach(
        str(content),
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )
    if print_to_console:
        print(f"[{name}] {content}")
