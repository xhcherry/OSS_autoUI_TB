import random
import string


def generate_random_account():
    """
    总共11位
    """
    return f"1111{random.randint(1111111, 9999999)}"


def generate_textbook_name():
    """
    生成随机教材名称：ui教材 + 10位字母数字混合（a-z, 0-9）
    """
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"ui教材{suffix}"
