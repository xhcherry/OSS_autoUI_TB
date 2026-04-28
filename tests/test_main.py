from playwright.sync_api import expect
from pages.level1_menu.level2_menu.main_page import Level2MenuPage
from utils.data_generator import generate_random_account

# 模块级共享数据
_shared_data = {}

def test_add_action(shared_page):
    """新建演示"""
    page_obj = Level2MenuPage(shared_page)
    page_obj.header.navigate_to_student() # User still left it as navigate_to_student in header

    account = generate_random_account()
    print(f"生成的测试号: {account}")
    # User simplified Tab1 add_student to take no args, so we just call it
    page_obj.tab1.inner_tab1.add_student()
    
    _shared_data["account"] = account
