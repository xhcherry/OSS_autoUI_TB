import random
import string
import datetime


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


def generate_textbook_name():
    """
    生成随机教材名称：ui教材 + 10位字母数字混合（a-z, 0-9）
    """
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"ui教材{suffix}"


# ── 题库资源专用 ──

def generate_paper_name() -> str:
    """生成随机试卷名称：自动化试卷_ + 日期时间戳"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=3))
    return f"自动化试卷_{ts}_{suffix}"


def generate_question_title(prefix: str = "题目") -> str:
    """生成随机题干"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    suffix = ''.join(random.choices(string.ascii_letters, k=3))
    return f"{prefix}_自动化_{ts}_{suffix}"


def generate_random_options(count: int = 4) -> dict[str, str]:
    """生成随机选项 dict，如 {"A": "option_a", "B": "option_b", ...}"""
    options = {}
    for i in range(count):
        key = chr(65 + i)
        suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
        options[key] = f"选项{suffix}"
    return options


def generate_random_correct_answer(options: dict[str, str], count: int = 1) -> list[str]:
    """从选项中随机选择正确答案"""
    keys = list(options.keys())
    return random.sample(keys, min(count, len(keys)))
