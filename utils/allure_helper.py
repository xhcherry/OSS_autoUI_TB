from pathlib import Path
from datetime import datetime


def generate_allure_report_dir() -> str:
    # 项目根目录 = utils/ 的上一级
    project_root = Path(__file__).resolve().parent.parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = project_root / 'report' / f'allure-results-{timestamp}'
    report_dir.mkdir(parents=True, exist_ok=True)
    return str(report_dir)


def attach_screenshot(page, name="截图"):
    if page is None:
        return
    import allure
    allure.attach(
        page.screenshot(full_page=True),
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def attach_text(content, name="文本内容", print_to_console=True):
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
