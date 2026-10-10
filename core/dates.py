from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TEHRAN_TZ = ZoneInfo("Asia/Tehran")


def now_tehran():
    return datetime.now(TEHRAN_TZ)


def today_str():
    return now_tehran().strftime("%Y-%m-%d")


def yesterday_str():
    return (now_tehran() - timedelta(days=1)).strftime("%Y-%m-%d")