import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # OSS登录
    BASE_URL = os.getenv("BASE_URL", "")
    USERNAME = os.getenv("OSS_USERNAME", "")
    PASSWORD = os.getenv("OSS_PASSWORD", "")

    # vs2数据库
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")