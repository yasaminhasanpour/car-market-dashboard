import sqlite3
from core.config import DB_PATH


def get_conn(**kwargs):
    """اتصال به دیتابیس. پارامترهای اضافه مستقیم به sqlite3.connect می‌رن
    (مثلاً check_same_thread=False برای استریم‌لیت)."""
    return sqlite3.connect(DB_PATH, **kwargs)