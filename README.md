# OSS_autoUI

本指南旨在帮助测试人员快速搭建环境并上手 **OSS_autoUI** 自动化框架。该框架基于 **Python + Playwright + Pytest + Allure** 构建。

- Pytest 文档：<https://docs.pytest.org/en/latest/getting-started.html>
- Playwright 文档：<https://playwright.dev/python/docs/intro>

## 一、软件环境安装

### 1. 安装 Python（版本 3.13+）

1. **下载**：访问 [Python 官网](https://www.python.org/downloads/windows/)，下载最新的 Python 3.13+ 安装包。

2. **安装**：
   - 双击运行安装包。
   - 勾选底部的 **"Add Python.exe to PATH"**（也可以不勾，项目会单独配置 `.venv` 虚拟环境）。
   - 选择 "Install Now"。

3. **验证**：打开命令行（CMD）输入 `python --version`，显示 `Python 3.13.x` 即为成功。

### 2. 安装 IDE

- **PyCharm（推荐，配合 Qoder 插件或 CodeBuddy）**：
  - 下载 [PyCharm](https://www.jetbrains.com/pycharm/download/) 任意版本。
  - 默认安装即可。
  - PyCharm 在跑单用例及单文件时更快捷方便。

### 3. 安装 Allure 测试报告

Allure 用于生成可视化测试报告。

1. **下载**：前往 [Allure GitHub Releases](https://github.com/allure-framework/allure2/releases) 下载最新版 `.zip` 包（例如 `allure-x.x.x.zip`）。

2. **解压**：将 zip 包解压到你电脑的一个固定位置（如 `D:\software\allure`）。

3. **配置环境变量**：
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"。
   - 在"系统变量"中找到 `Path`，点击编辑。
   - 点击"新建"，将 Allure 的 `bin` 目录路径添加进去（例如 `D:\software\allure\bin`）。

4. **验证**：重启终端，输入 `allure --version`，显示版本号即可。

### 4. 安装 Git

前往 [Git 官网](https://git-scm.com/install/windows) 下载最新版，安装全部默认即可。

**第 1 步：在本地电脑生成 SSH 密钥**

1. 打开电脑上的终端。

2. 输入以下命令（邮箱替换为你的 GitLab 邮箱）：

   ```bash
   ssh-keygen -t rsa -C "your_email@lingshi.com"
   ```

3. 一路回车到底，不要设置密码。这会在你的用户目录下的 `.ssh` 文件夹里生成两个文件：`id_rsa`（私钥）和 `id_rsa.pub`（公钥）。

**第 2 步：把公钥配置到 GitLab**

1. 用记事本打开刚才生成的 `id_rsa.pub` 文件，复制里面所有的内容（一长串以 `ssh-rsa` 开头的字符）。

2. 登录 GitLab 网页版。

3. 点击右上角头像 → **Settings（设置）** → 左侧菜单找 **SSH Keys**。

4. 将复制的内容粘贴到 "Key" 文本框中，点击 "Add key" 保存。

**第 3 步：在 PyCharm 中拉取代码**

1. 回到 PyCharm，在左侧上方点击"克隆仓库"，粘贴仓库地址 `git`，直接 Clone。

2. 克隆完成后即完成。

> ⚠️ **重要**：记得在下图位置创建自己的分支（默认是 master），然后可以把分支推上去。需要合到 master 的，在 GitLab 网页版提 Merge Request。
>
> ![](http://kf.51tyty.com/server/index.php?s=/api/attachment/visitFile&sign=8ed8b8b6cccbb4b91f26b7474154e5e5)

## 二、项目初始化

将名为 `ossautoui` 的文件夹直接拖到 PyCharm 里面即可，PyCharm 会自动打开项目。

### 1. 创建虚拟环境（Virtual Env）

直接在 PyCharm 右下角创建环境。

![](http://kf.51tyty.com/server/index.php?s=/api/attachment/visitFile&sign=52438aaf0ffa7cb5e09f4c4363423dc2)

初次打开显示的是未配置解释器，点一下，然后选择"添加新的解释器" → "添加本地解释器"。

按如下图片配置后点击确定即可：

![](http://kf.51tyty.com/server/index.php?s=/api/attachment/visitFile&sign=47ea9a7b6ebd6593b3425eced3368f4f)

### 2. 安装项目依赖

打开 PyCharm 自带的终端（Terminal），确认终端开头显示 `(.venv)` 后，运行下面命令：

```bash
# 更新 pip
python -m pip install --upgrade pip
# 安装 pyproject.toml 中声明的所有依赖
pip install -e .
```

### 3. 安装 Playwright 浏览器驱动

Playwright 需要下载内置的浏览器内核（Chromium）：

```bash
playwright install chromium
```

### 4. 配置环境变量

项目中已有 `.env` 文件，在其中配置自己机构的账号密码即可：

```env
# 基础环境（必填）
BASE_URL=https://your-oss-system.com/#/login
OSS_USERNAME=your_username
OSS_PASSWORD=your_password

# 模块专用账号（可选，格式：账号池 OSS_<MODULE>_ACCOUNTS=user:pass,user:pass）
OSS_SALES_ACCOUNTS=sales_user1:pass1,sales_user2:pass2
OSS_ACADEMIC_ACCOUNTS=academic_user:pass
OSS_WJGL_ACCOUNTS=wjgl_user:pass
```

## 三、运行测试

### 方式 A：使用统一运行器 runner.py（推荐）

`runner.py` 面向 CI 回归，默认无头运行全量用例，也支持 CLI 参数覆盖：

```bash
# 默认配置（无头 + 自动并发）
python runner.py

# CLI 覆盖常用参数
python runner.py --headed --slowmo 500     # 有头调试
python runner.py --workers 4 --reruns 2    # 4 并发 + 失败重试
```

### 方式 B：PyCharm 直接运行

运行测试用例文件夹：

![](http://kf.51tyty.com/server/index.php?s=/api/attachment/visitFile&sign=a7083ee9821f2cef1d84d1fa938404c6)

运行单个测试用例：

![](http://kf.51tyty.com/server/index.php?s=/api/attachment/visitFile&sign=5c095424620d5497e1b64ef6e5adff46)

### 方式 C：pytest 命令行

```bash
pytest                           # 运行所有用例
pytest tests/sales/              # 只跑销售模块
pytest tests/academic/           # 只跑教务模块
pytest -n 4 --reruns 2           # 4 并发 + 失败重试
pytest --headed=false            # 无头快速模式
```

## 四、查看测试报告

测试完成后，Allure 原始数据保存在 `report/allure-results-YYYYMMDD_HHmmss` 中。

```bash
# 启动本地服务查看（最常用）
allure serve report/allure-results-2026XXXX_XXXXXX

# 导出为静态 HTML 文件
allure generate report/allure-results-2026XXXX_XXXXXX -o report/html_report --clean

# 合并为单个 HTML 文件（便于分享）
allure-combine ./report/html_report
# → 生成 report/html_report/complete.html
```

## 五、拿到项目后该做什么？（开发建议）

1. **熟悉目录结构**：

   - `pages`：页面操作逻辑，新增页面请参考 `base_page.py`。
   - `tests`：存放测试用例代码。
   - `utils`：工具类，如 `captcha_solver.py`（验证码识别）、`db_client.py`（数据库查询）、`allure_helper.py`（Allure 报告辅助）。

2. **理解 POM 模式**：

   - 本项目严格执行页面对象模型（Page Object Model）。
   - **不要**在测试用例里写具体的元素定位，所有定位写在 `pages` 对应的类中。

3. **编写新用例的流程**：

   1. 在 `pages` 下创建或寻找对应的页面模块。
   2. 在 `Header` 组件中检查是否有进入该页面的导航方法。
   3. 在 `tests` 下编写脚本，调用 `page` 对象的方法并进行断言。

4. **调试技巧**：

   - `pyproject.toml` 已配置 `--headed --slowmo=500` 作为默认调试模式。
   - CI 回归使用 `python runner.py` 自动切换为无头模式。
   - 需要更慢速度时，使用 `python runner.py --headed --slowmo 1000`。

> 💡 如果你在运行中遇到验证码识别失败，项目内置了 `ddddocr`，它会自动重试。如需更高级配置，请查看 `utils/captcha_solver.py`。
