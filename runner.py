import sys
from pathlib import Path

import pytest

from config.settings import Config
from utils.allure_helper import generate_allure_report_dir, generate_single_file_html


class TestRunner:
    """CI 全量回归测试执行器。

    默认无头运行 tests/ 下所有用例，覆盖 pyproject.toml 的调试 addopts。
    本地调试请直接用 pytest（pyproject.toml 提供 --headed --slowmo 默认值）。

    CLI 覆盖示例::

        python runner.py --headed --slowmo 500     # 临时有头调试
        python runner.py --workers 4 --reruns 2     # 自定义并发与重试
        python runner.py --targets tests/ tests/sub # 指定多个目标
        python runner.py --no-notify                # 本次不推送企微通知
    """

    # 回归专用 addopts（覆盖 pyproject.toml 中 --headed --slowmo）
    _HEADLESS_ADDOPTS = Config.HEADLESS_ADDOPTS

    def __init__(self, **kwargs):
        # 运行目标（默认全量回归）
        targets = kwargs.get("test_targets", ["tests/"])
        if isinstance(targets, str):
            targets = [targets]
        self.test_targets: list[str] = targets

        # 报告参数透传（用于外部平台与 CI 关联任务）
        self.alluredir: str | None = kwargs.get("alluredir", None)
        self.junitxml: str | None = kwargs.get("junitxml", None)

        # 运行模式（CI 默认无头、无慢放）
        self.headless: bool = kwargs.get("headless", True)
        self.slowmo: int = kwargs.get("slowmo", 0)

        # 并发 / 重试
        self.workers: str | None = kwargs.get("workers", None)
        self.reruns: int = kwargs.get("reruns", 0)
        self.count: int = kwargs.get("count", 1)

        # 企微通知开关，外部平台可关闭
        self.notify: bool = kwargs.get("notify", True)

    def run(self) -> int:
        args: list[str] = [*self.test_targets]

        # Allure 报告目录
        report_dir = self.alluredir if self.alluredir else generate_allure_report_dir()
        args.append(f"--alluredir={report_dir}")

        if self.junitxml:
            args.append(f"--junitxml={self.junitxml}")

        # 界面模式
        if not self.headless:
            args.append("--headed")
            if self.slowmo > 0:
                args.append(f"--slowmo={self.slowmo}")
        else:
            # 无头回归 → 覆盖 pyproject.toml 中的 --headed --slowmo
            args.extend(["-o", f"addopts={self._HEADLESS_ADDOPTS}"])

        # 并发
        if self.workers is not None:
            args.append(f"-n={self.workers}")

        # 失败重跑
        if self.reruns > 0:
            args.append(f"--reruns={self.reruns}")

        # 全局重复
        if self.count > 1:
            args.append(f"--count={self.count}")

        print("开始根据 runner.py 的配置执行测试...")
        print(f"执行指令映射: pytest {' '.join(args)}\n")

        # 标记由 runner 触发，conftest 据此决定是否推送企微通知
        Config.WECOM_NOTIFY = self.notify

        exit_code = pytest.main(args)

        print("\n" + "=" * 50)
        print(f"测试框架执行完毕！全局返回码 (Exit Code): {exit_code}")
        print("=" * 50)

        # Allure 报告处理
        report_path = Path(report_dir)
        if report_path.exists():
            rel = str(report_path.relative_to(Path.cwd())).replace("\\", "/")
            # 自动在原报告目录内生成单文件 HTML 报告
            generate_single_file_html(report_dir)
            print(f"单文件 HTML 报告已生成：{rel}/index.html")
            print(f"在线查看：allure open {rel}")
        else:
            print(f"\n未能成功生成 allure 记录文件夹：{report_dir}")

        return exit_code


# CLI 参数映射
CLI_FLAGS: dict[str, tuple[str, type]] = {
    "--headed": ("headless", bool),
    "--slowmo": ("slowmo", int),
    "--workers": ("workers", str),
    "--reruns": ("reruns", int),
    "--count": ("count", int),
    "--alluredir": ("alluredir", str),
    "--junitxml": ("junitxml", str),
    "--no-notify": ("notify", bool),
}


def _parse_cli(argv: list[str]) -> dict:
    """将命令行参数解析为 TestRunner 构造参数。"""
    kwargs: dict = {}
    i = 0
    targets = []
    while i < len(argv):
        arg = argv[i]
        if arg == "--targets":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                targets.append(argv[i])
                i += 1
            continue
        elif arg in CLI_FLAGS:
            key, typ = CLI_FLAGS[arg]
            if typ is bool:
                kwargs[key] = False
            else:
                i += 1
                if i < len(argv):
                    kwargs[key] = typ(argv[i])
        i += 1

    if targets:
        kwargs["test_targets"] = targets
    return kwargs


if __name__ == "__main__":
    cli_kwargs = _parse_cli(sys.argv[1:])
    runner = TestRunner(**cli_kwargs)
    sys.exit(runner.run())
