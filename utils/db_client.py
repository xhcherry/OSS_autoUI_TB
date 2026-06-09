import pymysql
from pymysql.cursors import DictCursor
from config.settings import Config
import logging

logger = logging.getLogger(__name__)


class DBClient:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=True
            )
            logger.info(f"成功连接到数据库: {Config.DB_HOST}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise e

    def execute_query(self, sql: str, params: tuple | None = None) -> list:
        if not self.conn or not self.conn.open:
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchall()
                return result
        except Exception as e:
            logger.error(f"执行查询失败 SQL: {sql}, Params: {params}, Error: {e}")
            return []

    def execute_update(self, sql: str, params: tuple | None = None) -> int:
        if not self.conn or not self.conn.open:
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
                return affected_rows
        except Exception as e:
            self.conn.rollback()
            logger.error(f"执行更新失败 SQL: {sql}, Params: {params}, Error: {e}")
            raise e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        if self.conn and self.conn.open:
            self.conn.close()
            logger.info("数据库连接已关闭")