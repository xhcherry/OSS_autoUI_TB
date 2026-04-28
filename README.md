# OSS_autoUI

基于 **Python + Playwright + Pytest** 的 Web UI 自动化测试框架，专为 Web UI 自动化测试核心业务流程打造。

---

## ✨ 核心特性

- **POM 页面对象模式**：业务逻辑与测试脚本分离，提升代码可维护性。
- **组件化架构**：复杂页面采用「主容器 + 子组件 (Tab)」结构，降低单文件复杂度。
- **智能导航**：`Header` 组件统一管理全系统一级/二级菜单跳转。
- **自动验证码识别**：内置 `ddddocr` 模块，自动识别 Canvas 点选验证码并支持重试。
- **完善的测试报告**：深度集成 Allure，支持自动截图、失败追溯与运行历史管理。
- **动态数据生成**：自动生成随机账号等测试数据，避免重复数据冲突。

---

## 🛠 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **编程语言** | Python 3.12+ | 核心开发语言 |
| **底层驱动** | Playwright | 现代化的端到端 Web 测试工具 |
| **测试框架** | Pytest | 灵活的测试组织与运行框架 |
| **测试报告** | Allure | 直观详细的可视化测试报告 |
| **图像识别** | ddddocr + Pillow | 专用于处理登录页图形验证码 |

---

## 📁 核心目录结构

框架采用清晰的三层架构：**用例层 -> 业务逻辑层 -> 页面元素层**。

```
OSS_autoUI/
├── config/              # 全局配置（如 BASE_URL，配合 .env 使用）
├── pages/               # 【页面对象层】按业务模块划分
│   ├── base_page.py     # 所有页面的基类（封装通用方法）
│   ├── components/      # 公共组件（如顶部导航 Header）
│   └── level1_menu/     # 模块：一级菜单演示
│       └── level2_menu/ # 二级菜单演示（一级Tab、二级Tab等）
├── tests/               # 【测试用例层】按业务模块组织测试脚本
├── utils/               # 工具库（验证码破解、随机数据生成）
├── pytest.ini           # Pytest 运行策略配置
└── requirements.txt     # Python 依赖清单
```

---

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.12+ 和 Git。

```bash
# 克隆代码(暂无)
git clone <仓库地址>

# 创建并激活虚拟环境 (推荐)
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器依赖
playwright install

# 安装allure测试报告
# 下载最新版的zip：https://github.com/allure-framework/allure2/releases
# 然后将bin目录添加至系统变量
# cmd中输入allure验证
```

### 2. 环境配置
在项目根目录新建 `.env` 文件（请勿提交到 Git）：
```env
BASE_URL=https://your-oss-system.com
OSS_USERNAME=your_username
OSS_PASSWORD=your_password
```

---

## 🧪 运行测试与报告

### 执行测试
```bash
# 运行所有测试（默认带界面展示，适合调试）
pytest

# 运行指定文件或单条用例
pytest tests/xx.py
pytest tests/xx.py::xxx

# 无头模式运行（适合 CI/CD 流水线）
pytest --headed=false --slowmo=0
```

### 查看 Allure 报告
每次运行后，测试结果会自动存入 `report/` 目录。
```bash
# 启动本地服务查看最新的可视化报告
allure serve report/allure-results-<timestamp>
```

---

## 🏗 架构设计规范

为了保证框架的可扩展性，如下开发规范：

### 1. 组件化页面模式 (Container & Leaf)
针对带有多个 Tab 的复杂页面，必须进行拆分：
- **容器类 (Container)**：如 `Level2MenuPage`，只负责管理内部 Tab 的切换逻辑，**不继承** `BasePage`。
- **叶子节点 (Leaf Tab)**：如 `Tab1`，负责具体的业务操作（点击、输入等），**必须继承** `BasePage`，以获取底层导航和通用方法。

### 2. 统一导航出口
严禁在测试用例中直接使用 URL 跳转。所有页面的跳转必须通过 `Header` 组件暴露的 `navigate_to_xxx()` 方法进行，例如：
```python
# 正确的导航方式
page_object.header.navigate_to_student()
```

### 3. Fixture 驱动测试
利用 Pytest fixture 简化前置操作：
- `logged_in_page`: Function 级别，每条用例独立登录，保证完全隔离。
- `shared_page`: Module 级别，文件内多条用例共享登录状态，提升执行效率。

---

## 📝 编写第一条用例

如果你想增加一个新的测试页面，请按以下 3 步走：

1. **新建 Page Object**：在 `pages/<模块>/` 下创建对应的页面类，封装元素定位（推荐使用 `get_by_role` 或 `get_by_text`）和操作方法。
2. **注册导航入口**：确认 `pages/components/header.py` 中有前往该页面的导航方法。
3. **编写测试脚本**：在 `tests/` 下新建 `test_xxx.py`，调用刚刚写好的页面方法并添加 `assert` 断言。
