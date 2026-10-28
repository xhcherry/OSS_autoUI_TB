# autoUI 架构

基于 **Python + Playwright + Pytest + Allure** 的 Web UI 自动化测试**框架架构**。
本仓库已剥离所有业务代码，仅保留可复用的框架骨架，供具体业务项目在此之上落地用例。

> 业务实现请基于本架构扩展 `pages/<模块>/` 与 `tests/<模块>/`，不要修改架构核心
> （`config/`、`utils/`、`pages/base_page.py`、`pages/header.py`、`tests/conftest.py`、`runner.py`）。

---

## 一、架构组成

```
.
├── config/settings.py        # 统一配置：环境变量加载 + 账号池解析 + 通知开关
├── pages/
│   ├── base_page.py          # 页面对象基类：Header 懒加载 + 通用定位器 + 等待收口 + 弹窗/搜索通用方法
│   ├── header.py             # 统一 Header 出口：按 platform 派发主平台/管理后台/子系统
│   ├── primary/              # 主平台
│   │   ├── header.py         #   导航 Header（default 标准布局 + alt 备用布局）
│   │   └── login_page.py     #   登录页（滑块验证自动通过 + 白名单账号免验证）
│   ├── admin/                # 管理后台
│   │   ├── header.py         #   AdminHeader
│   │   └── login_page.py     #   AdminLoginPage
│   └── sub/                  # 子系统
│       └── header.py         #   SubHeader + SubSidebar（SPA 侧边栏）
├── tests/
│   ├── conftest.py           # 核心夹具：单会话完整登录、多平台 fixtures、企微通知、marker 注册
│   └── test_main.py          # 架构冒烟测试（改架构后必跑）
├── utils/                    # 工具集
│   ├── allure_helper.py      #   Allure 报告目录 / 截图 / 文本附件 / 单文件 HTML 报告
│   ├── captcha_solver.py     #   登录滑块拖拽验证（ls-slide-verify，模拟人类轨迹）
│   ├── db_client.py          #   MySQL 客户端
│   ├── wecom_notifier.py     #   企业微信机器人通知
│   ├── data_generator.py     #   随机测试数据生成
│   ├── file_util.py          #   项目根 / 资源路径
│   └── step_logger.py        #   UI 操作步骤日志（Playwright 类级补丁，中文打印每步操作）
├── runner.py                 # CI 回归执行器（覆盖调试 addopts，触发企微通知，运行后自动出单文件报告）
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

### 2. 单会话完整登录
`conftest.py` 的登录 fixtures（`logged_in_page` / `shared_page` / `admin_*` /
`sub_*`）每次创建独立 context 并完整登录。目标系统限制同账号多会话时
storage_state 登录态缓存无法复用（新会话会踢掉旧会话），框架统一改为
每次全量登录；`goto` 使用 `domcontentloaded` 防止第三方 SDK 挂起拖慢
load 事件导致超时。`page_factory` 支持单用例内多账号场景。

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
python runner.py --targets tests/ tests/sub/  # 指定多个运行目标
python runner.py --no-notify                  # 本次运行不推送企微通知
```

### 5. 失败自动截图 + Allure 3 单文件报告
`pytest_runtest_makereport` 钩子在用例失败时自动截图附加到报告，并剥离
Playwright 断言异常中的 Aria snapshot 刷屏噪声；每次运行按时间戳生成独立
报告目录 `report/allure-results-YYYYMMDD_HHmmss`，会话结束自动生成可分享的
单文件 HTML 报告（需 Allure 3.15+，`allure awesome --single-file`）。

### 6. UI 操作步骤日志
`utils/step_logger.py` 给 Playwright 打类级补丁，每一步点击/输入/按键打印
中文步骤日志（配合 `-s` 输出），无头 / CI / 服务器运行也能看到每一步做了
什么；`BasePage` 初始化时自动安装。

## 三、环境搭建

### 1. 安装 Python 3.13+ 与依赖
```bash
python -m pip install --upgrade pip
pip install -e .
playwright install chromium
```

### 2. 安装 Allure 3
```bash
npm install -g allure   # 需先安装 Node.js
allure --version        # 单文件报告需 Allure 3.15+
```

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
# 单文件报告已由框架自动生成（Allure 3.15+），直接分发：
# report/allure-results-YYYYMMDD_HHmmss/index.html
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
