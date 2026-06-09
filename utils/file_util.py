from pathlib import Path

def get_project_root() -> Path:
    """获取项目根目录的绝对路径"""
    # 假设 utils 目录与顶层目录同级，这里获取 __file__ 所在目录的上一级
    return Path(__file__).resolve().parent.parent

def get_asset_path(filename: str) -> Path:
    """获取assets文件夹中的文件绝对路径"""
    return get_project_root() / "assets" / filename
