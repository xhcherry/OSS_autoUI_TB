"""
统一 Header 出口模块。

三个 Header 类的实际代码在各平台目录下：
- pages/primary/header.py → Header      （主平台，支持 default / alt 两种菜单布局）
- pages/admin/header.py   → AdminHeader （管理后台）
- pages/sub/header.py     → SubHeader   （子系统）

本文件保持向后兼容，所有 `from pages.header import X` 不受影响。
"""
from pages.admin.header import AdminHeader
from pages.primary.header import Header
from pages.sub.header import SubHeader

__all__ = ["Header", "AdminHeader", "SubHeader"]
