import time
from datetime import datetime, timedelta

import requests

from core.db import get_conn
from core.dates import now_tehran, today_str, yesterday_str, TEHRAN_TZ
from core.log import get_logger

logger = get_logger(__name__)

URL = "https://api.wallex.ir/v1/udf/history"

MAX_RETRY = 10
RETRY_DELAY = 5


def init_tether_table(conn):
    """Create tether table if not exists"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tether (
            date TEXT PRIMARY KEY,
            close REAL
        )
    """)
    conn.commit()


def get_row_by_date(conn, date_str):
    """Get record for a specific date"""
    row = conn.execute(
        "SELECT date, close FROM tether WHERE date = ?",
        (date_str,)
    ).fetchone()
    return row if row else None


def get_last_date(conn):
    """Get the latest date from database"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM tether")
    result = cursor.fetchone()
    return result[0] if result and result[0] else None


def ts_to_tehran_date(ts):
    """تبدیل timestamp به تاریخ (YYYY-MM-DD) به وقت تهران"""
    return datetime.fromtimestamp(ts, TEHRAN_TZ).strftime("%Y-%m-%d")


def fetch_tether_data(start_date, end_date):
    """Fetch tether data from Wallex API"""
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())

    params = {
        "symbol": "USDTTMN",
        "resolution": "D",
        "from": start_ts,
        "to": end_ts
    }

    try:
        response = requests.get(URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "t" in data and len(data["t"]) > 0:
            return data
        return None

    except Exception as e:
        logger.error(f"❌ Failed to fetch data from Wallex: {e}")
        return None


def validate_and_fix_tether():
    """
    Validate and fix tether prices:
    1. Check yesterday's closing price (End of Day Candle)
    2. Fix if wrong
    3. Get today's live price (Intraday)
    4. Update database
    """
    logger.info("🔄 Starting tether price validation and fix...")

    attempt = 0
    while attempt < MAX_RETRY:
        try:
            conn = get_conn()
            init_tether_table(conn)

            today = today_str()
            yesterday = yesterday_str()
            current_time = now_tehran().strftime("%H:%M")

            logger.info(f"📅 Today: {today}")
            logger.info(f"📅 Yesterday: {yesterday}")
            logger.info(f"🕐 Current time: {current_time}")

            # ============================================================
            # 1. Get data from API (last 35 days to be safe)
            # ============================================================
            end_dt = now_tehran()
            start_dt = end_dt - timedelta(days=35)

            data = fetch_tether_data(start_dt, end_dt)

            if not data:
                logger.error("❌ Failed to get data from API")
                conn.close()
                return False

            # ============================================================
            # 2. Check and fix yesterday's record (End of Day Candle)
            # ============================================================
            logger.info("-" * 60)
            logger.info("📊 Checking yesterday's record (End of Day Candle)...")

            yesterday_close = None
            for ts, close_price in zip(data["t"], data["c"]):
                if ts_to_tehran_date(ts) == yesterday:
                    yesterday_close = float(close_price)
                    break

            if yesterday_close:
                existing_yesterday = get_row_by_date(conn, yesterday)

                if existing_yesterday:
                    existing_date, existing_price = existing_yesterday

                    if abs(existing_price - yesterday_close) > 0.01:
                        conn.execute("""
                            INSERT OR REPLACE INTO tether (date, close)
                            VALUES (?, ?)
                        """, (yesterday, yesterday_close))
                        logger.info(f"🔄 Fixed yesterday's closing price:")
                        logger.info(f"   ❌ Old price: {existing_price:,.0f}")
                        logger.info(f"   ✅ Correct price: {yesterday_close:,.0f}")
                    else:
                        logger.info(f"✅ Yesterday's price is correct: {yesterday_close:,.0f}")
                else:
                    conn.execute("""
                        INSERT OR REPLACE INTO tether (date, close)
                        VALUES (?, ?)
                    """, (yesterday, yesterday_close))
                    logger.info(f"➕ Added yesterday's closing price: {yesterday_close:,.0f}")
            else:
                logger.warning(f"⚠️ Yesterday's closing price not found in API data")

            # ============================================================
            # 3. Update today's price (Intraday)
            # ============================================================
            logger.info("-" * 60)
            logger.info("📊 Getting today's live price (Intraday)...")

            today_price = None
            for ts, close_price in zip(data["t"], data["c"]):
                if ts_to_tehran_date(ts) == today:
                    today_price = float(close_price)
                    break

            if today_price:
                existing_today = get_row_by_date(conn, today)

                if existing_today:
                    existing_date, existing_price = existing_today

                    if abs(existing_price - today_price) > 0.01:
                        conn.execute("""
                            INSERT OR REPLACE INTO tether (date, close)
                            VALUES (?, ?)
                        """, (today, today_price))
                        logger.info(f"🔄 Updated today's live price:")
                        logger.info(f"   ❌ Old price: {existing_price:,.0f}")
                        logger.info(f"   ✅ New price: {today_price:,.0f}")
                    else:
                        logger.info(f"✅ Today's live price is correct: {today_price:,.0f}")
                else:
                    conn.execute("""
                        INSERT OR REPLACE INTO tether (date, close)
                        VALUES (?, ?)
                    """, (today, today_price))
                    logger.info(f"➕ Added today's live price: {today_price:,.0f}")
            else:
                logger.warning(f"⚠️ Today's price not found in API data")

                # Fallback: if today's price not in API, use latest available
                if data["t"] and len(data["t"]) > 0:
                    latest_ts = data["t"][-1]
                    latest_price = data["c"][-1]
                    latest_date = ts_to_tehran_date(latest_ts)

                    if latest_date == today:
                        today_price = float(latest_price)
                        existing_today = get_row_by_date(conn, today)

                        if not existing_today:
                            conn.execute("""
                                INSERT OR REPLACE INTO tether (date, close)
                                VALUES (?, ?)
                            """, (today, today_price))
                            logger.info(f"➕ Added today's price from latest data: {today_price:,.0f}")

            conn.commit()

            # ============================================================
            # 4. Final Report
            # ============================================================
            print("\n" + "=" * 70)
            print("📊 TETHER Price Update Report")
            print("=" * 70)

            cursor = conn.cursor()
            last_records = cursor.execute(
                "SELECT date, close FROM tether ORDER BY date DESC LIMIT 5"
            ).fetchall()

            print("\n📋 Last 5 records:")
            print(f"{'Date':<15} {'Price (IRR)':<20} {'Type':<15}")
            print("-" * 55)

            for date_str, price in last_records:
                if date_str == today:
                    price_type = "🟢 INTRADAY"
                elif date_str == yesterday:
                    price_type = "🔵 CLOSE (EOD)"
                else:
                    price_type = "📊 HISTORY"
                print(f"{date_str:<15} {price:>15,.0f}    {price_type}")

            print("=" * 70)

            conn.close()
            logger.info("🎯 Update completed successfully.")
            return True

        except Exception as e:
            attempt += 1
            logger.error(f"❌ Attempt {attempt}/{MAX_RETRY} failed: {e}")

            try:
                conn.close()
            except:
                pass

            if attempt >= MAX_RETRY:
                logger.error("⛔ Max retries reached. Script stopped.")
                return False

            time.sleep(RETRY_DELAY)

    return False


if __name__ == "__main__":
    validate_and_fix_tether()