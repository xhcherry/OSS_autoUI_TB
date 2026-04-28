import random

def generate_random_account():
    """
    总共11位
    """
    return f"3333{random.randint(1111111, 9999999)}"
