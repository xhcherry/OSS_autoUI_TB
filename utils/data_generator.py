import random
import string


def generate_random_account():
    """
    总共11位
    """
    return f"1111{random.randint(1111111, 9999999)}"


def generate_random_name():
    """
    生成随机昵称/备注：ui昵称 + 4位字母数字混合（a-z, 0-9）
    """
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"ui昵称{suffix}"



