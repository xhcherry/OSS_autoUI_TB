# autoUI 架构

基于 **Python + Playwright + Pytest + Allure** 的 Web UI 自动化测试**框架架构**。
本仓库已剥离所有业务代码，仅保留可复用的框架骨架，供具体业务项目在此之上落地用例。

> 业务实现请基于本架构扩展 `pages/<模块>/` 与 `tests/<模块>/`，不要修改架构核心
> （`config/`、`utils/`、`pages/base_page.py`、`pages/header.py`、`tests/conftest.py`、`runner.py`）。

---

## 一、架构组成

```
.
├── config/settings.py        # 统一配置：环境变量加载 + 账号池解析
├── pages/
│   ├── base_page.py          # 页面对象基类：多平台 Header 懒加载 + 表格操作通用方法
│   ├── header.py             # 统一 Header 出口：按 platform 派发主平台/管理后台/子系统
│   ├── primary/              # 主平台
│   │   ├── header.py         #   导航 Header（default 标准布局 + alt 备用布局）
│   │   └── login_page.py     #   登录页（白名单账号免验证码兼容）
│   ├── admin/                # 管理后台
│   │   ├── header.py         #   AdminHeader
│   │   └── login_page.py     #   AdminLoginPage
│   └── sub/                  # 子系统
│       └── header.py         #   SubHeader + SubSidebar（SPA 侧边栏）
├── tests/
│   ├── conftest.py           # 核心夹具：登录态缓存、多平台 fixtures、企微通知、marker 注册
│   └── test_main.py          # 架构冒烟测试（改架构后必跑）
├── utils/                    # 工具集
│   ├── allure_helper.py      #   Allure 报告目录 / 截图 / 文本附件
│   ├── captcha_solver.py     #   ddddocr 点选验证码识别（双引擎投票 + IoU 去重）
│   ├── db_client.py          #   MySQL 客户端
│   ├── wecom_notifier.py     #   企业微信机器人通知
│   ├── booking_helper.py     #   约课时间格随机选取（纯样式识别）
│   ├── data_generator.py     #   随机测试数据生成
│   └── file_util.py          #   项目根 / 资源路径
├── runner.py                 # CI 回归执行器（覆盖调试 addopts，触发企微通知）
├── pyproject.toml            # 依赖与 pytest 配置
└── .env.example              # 环境变量模板（复制为 .env 后填写）
```

## 二、核心能力

### 1. 多平台 Header 动态导航
`Header`（主平台）/ `AdminHeader`（管理后台）/ `SubHeader`（子系统）基于路由表
`_routes` 自动派发 `navigate_to_{key}()` 方法，无需手写每个导航函数。
新增菜单只需在路由表追加一行。

`pages/base_page.py` 按 `platform` 参数（`default` / `alt` / `admin` / `sub`）
懒加载对应 Header，业务页面对象继承 `BasePage` 即可直接用 `self.header.navigate_to_xxx()`。

### 2. 登录态缓存（storageState）
`conftest.py` 首次登录后将 `storage_state` 落盘到系统临时目录，后续用例/模块
直接从缓存创建 context，避免重复登录。主平台 / 管理后台 / 子系统 三套缓存相互独立。

### 3. 账号池 + marker 自动注册
`config/settings.py` 用 `_parse_account_pool` 解析 `XXX_ACCOUNTS` 为账号池；
`conftest.py` 扫描 `Config.*_ACCOUNTS` 自动注册同名 pytest marker，
按 `worker_id` 轮询分配账号，实现并发隔离。新增模块账号池即自动可用，无需改 conftest。

### 4. CI 回归执行器
`runner.py` 默认无头 + 自动并发跑全量用例，覆盖 `pyproject.toml` 的调试 addopts，
并通过 `Config.WECOM_NOTIFY` 触发企微结果推送。支持 CLI 覆盖：

```bash
python runner.py                              # 默认无头全量回归
python runner.py --headed --slowmo 500        # 有头调试
python runner.py --workers 4 --reruns 2       # 4 并发 + 失败重试
```

### 5. 失败自动截图 + Allure 报告
`pytest_runtest_makereport` 钩子在用例失败时自动截图附加到报告；
每次运行按时间戳生成独立报告目录 `report/allure-results-YYYYMMDD_HHmmss`。

## 三、环境搭建

### 1. 安装 Python 3.13+ 与依赖
```bash
python -m pip install --upgrade pip
pip install -e .
playwright install chromium
```

### 2. 安装 Allure
下载 [Allure Releases](https://github.com/allure-framework/allure2/releases)，
将其 `bin` 目录加入系统 `Path`，终端执行 `allure --version` 验证。

### 3. 配置环境变量
```bash
cp .env.example .env   # Windows: copy .env.example .env
```
按 `.env` 注释填写 `BASE_URL`、账号、数据库等。模块账号池格式见 `.env.example`。

## 四、运行测试

```bash
# 本地调试（pyproject.toml 默认 --headed --slowmo=500）
pytest

# 架构冒烟（改架构后必跑）
pytest tests/test_main.py

# 指定模块 / 单用例
pytest tests/<module>/
pytest tests/<module>/test_xxx.py::test_case

# 无头快速模式
pytest --headed=false --slowmo=0
```

## 五、查看报告
```bash
allure serve report/allure-results-YYYYMMDD_HHmmss
# 导出单文件
allure generate report/allure-results-YYYYMMDD_HHmmss -o report/html_report --clean
allure-combine ./report/html_report   # → report/html_report/complete.html
```

## 六、基于本架构开发业务用例

1. **新增页面**：在 `pages/<平台>/<模块>/` 下创建页面对象，继承 `BasePage`，
   定位器与操作写在页面类中（POM 模式，禁止在用例里写定位）。
2. **导航复用**：进入页面前用 `self.header.navigate_to_xxx()`；菜单需新增时，
   在对应平台 `header.py` 的路由表追加一行即可自动生成导航方法。
3. **新增模块账号**：在 `.env` 配置 `XXX_ACCOUNTS`，conftest 自动注册
   marker，用例加 `@pytest.mark.xxx` 即按账号池分配。
4. **编写用例**：在 `tests/<模块>/` 下编写，使用 `logged_in_page` / `shared_page`
   等夹具获取已登录页面，调用页面对象方法并断言。
