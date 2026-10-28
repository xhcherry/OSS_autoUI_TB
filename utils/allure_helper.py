import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def generate_allure_report_dir() -> str:
    # 项目根目录 = utils/ 的上一级
    project_root = Path(__file__).resolve().parent.parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = project_root / 'report' / f'allure-results-{timestamp}'
    report_dir.mkdir(parents=True, exist_ok=True)
    return str(report_dir)


def generate_single_file_html(report_dir: str) -> str | None:
    """根据 allure 结果目录生成单文件 HTML 报告（需 Allure 3.15+）。

    在原 allure 结果目录根部生成 index.html（单文件报告），原始结果文件
    归档到 source/ 子目录。幂等：已生成过则直接返回现有报告路径
    （conftest 会话结束钩子与 runner.py 后处理先后触发时不重复生成）。
    若 allure 命令不可用或生成失败，打印原因并返回 None。
    """
    report_path = Path(report_dir)
    if not report_path.exists():
        return None

    html_file = report_path / "index.html"
    if html_file.exists():
        return str(html_file)

    allure_bin = shutil.which("allure")
    if allure_bin is None:
        print("[allure] 未找到 allure 命令，跳过单文件 HTML 报告生成。"
              "请安装 Allure 3：npm install -g allure（需 Node.js），并确认已加入 PATH")
        return None

    # 生成单文件报告到报告目录根部（Allure 3.15+ 中 -o 即最终输出目录）
    cmd = [allure_bin, "awesome", str(report_path), "-o", str(report_path), "--single-file"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        print(f"[allure] 执行 allure awesome 异常，跳过单文件 HTML 报告生成：{e}")
        return None

    if result.returncode != 0:
        err_lines = (result.stderr or result.stdout or "").strip().splitlines()
        tail = err_lines[-1] if err_lines else "无错误输出"
        print(f"[allure] allure awesome 执行失败（返回码 {result.returncode}，需 Allure 3+）：{tail}")
        return None

    if not html_file.exists():
        print("[allure] allure awesome 执行完成但未生成 index.html")
        return None

    # 将原始结果文件归档到 source/ 子目录
    source_dir = report_path / "source"
    source_dir.mkdir(exist_ok=True)
    for f in report_path.glob("*.json"):
        shutil.move(str(f), str(source_dir / f.name))

    return str(html_file)


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
