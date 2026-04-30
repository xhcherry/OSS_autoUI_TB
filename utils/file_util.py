import os

def get_project_root() -> str:
    """获取项目根目录的绝对路径"""
    # 假设 utils 目录与顶层目录同级，这里获取 __file__ 所在目录的上一级
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_asset_path(filename: str) -> str:
    """
    获取项目根目录下 assets 文件夹中的文件绝对路径
    :param filename: 文件名，例如 "意向学员模板_20260429153508.xlsx"
    :return: 文件的绝对路径
    """
    return os.path.join(get_project_root(), "assets", filename)
