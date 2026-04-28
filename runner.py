import os
import glob
import pytest
from datetime import datetime

class TestRunner:
    """
    测试执行控制中心
    """

    def __init__(self):
        # 1. 运行目标配置 (List数据结构)
        # 运行某个目录下所有的测试：   ["tests/"]
        # 运行某一个指定的文件：      ["tests/xxx.py"]
        # 运行多个指定的文件：        ["tests/xxx.py", "tests/xxxx.py"]
        # 运行确切的某一个测试用例：   ["tests/xxx.xxxxx::xxxxxx"]
        self.test_targets = ["tests/"]

        # 2. 运行模式设置
        self.headless = False      # True: 无头 | False: 前台打开浏览器
        self.slowmo = 1000         # 慢放操作延迟(毫秒)。界面模式调试时可设为 1000
        
        # 并发控制；可设置为具体数字(如 "4")，自适应("auto")，或者 None(单进程执行)
        self.workers = "1"

        # 失败重跑次数
        self.reruns = 1

        # 全局重复执行整个测试的次数
        self.count = 1

    def run(self):
        # 初始化组装 pytest 的命令行参数
        args = []
        
        # 加入用例
        args.extend(self.test_targets)

        # 动态创建一个唯一的报告目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = os.path.join(os.path.dirname(__file__), 'report', f'allure-results-{timestamp}')
        
        # 使用相对路径传参
        rel_report_dir = os.path.relpath(report_dir, os.path.dirname(__file__)).replace("\\", "/")
        args.append(f"--alluredir={rel_report_dir}")
        
        # 界面显示模式
        if not self.headless:
            args.append("--headed")
            if self.slowmo > 0:
                args.append(f"--slowmo={self.slowmo}")

        # 并发配置 (-n)
        if self.workers:
            args.append(f"-n={self.workers}")

        # 重跑
        if hasattr(self, 'reruns') and self.reruns > 0:
            args.append(f"--reruns={self.reruns}")

        # 重复次数
        if hasattr(self, 'count') and self.count > 1:
            args.append(f"--count={self.count}")

        print(f"开始根据 runner.py 的配置执行测试...")
        print(f"执行指令映射: pytest {' '.join(args)}\n")
        
        # 调用 pytest main 引擎执行测试
        exit_code = pytest.main(args)
        
        print("\n" + "="*50)
        print(f"测试框架执行完毕！全局返回码 (Exit Code): {exit_code}")
        print("="*50)
        
        # 自动生成 Allure 查看指令
        if os.path.exists(report_dir):
            print(f"测试报告：allure serve {rel_report_dir} \n")
            
            print("将报告渲染为单文件HTML，依次执行：")
            print(f"生成基础报告: allure generate {rel_report_dir} -o report/html_report --clean")
            print(f"打包为单文件: allure-combine ./report/html_report")
            print("单文件：complete.html\n")
        else:
            print(f"\n跑完后未能成功生成 allure 记录文件夹：{rel_report_dir}")

if __name__ == '__main__':
    # 实例化运行器
    runner_instance = TestRunner()
    
    # 可以根据终端 sys.argv 参数来动态覆盖修改配置
    # pass

    runner_instance.run()
