import re

import requests

from datetime import datetime

from core.db import get_conn
from core.dates import now_tehran, today_str, yesterday_str
from core.log import get_logger

logger = get_logger(__name__)

HISTORY_API_URL = "https://api.tgju.org/v1/market/indicator/summary-table-data/geram18"
LIVE_API_URL = "https://api.tgju.org/v1/market/indicator/live-data/geram18"


def parse_price(text):
    """Convert price text to number"""
    if text is None:
        return None
    text = str(text)
    text = re.sub(r"[^0-9.,]", "", text)
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def get_row_by_date(conn, date_str):
    """Get record for a specific date"""
    row = conn.execute(
        "SELECT date, gold18 FROM gold WHERE date = ?",
        (date_str,)
    ).fetchone()
    return row if row else None


def fetch_gold_history():
    """Fetch historical gold data from API (for yesterday's close price)"""
    params = {
        "lang": "fa",
        "draw": "1",
        "start": "0",
        "length": "30",
        "convert_to_ad": "1"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tgju.org/",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.get(HISTORY_API_URL, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        result = response.json()
        return result.get("data", [])
    except Exception as e:
        logger.error(f"❌ Failed to fetch history data: {e}")
        return None


def fetch_gold_live():
    """Fetch live gold price from API (for today's intraday price)"""
    params = {
        "lang": "fa"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tgju.org/",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.get(LIVE_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()

        # ساختار پاسخ API لحظه‌ای معمولاً به این صورته:
        # {"price": 178789000, "date": "2026-07-27", ...}
        price = result.get("price") or result.get("last") or result.get("close")
        date_str = result.get("date") or today_str()

        if price:
            return float(price), date_str
        return None, None

    except Exception as e:
        logger.error(f"❌ Failed to fetch live price: {e}")
        return None, None


def validate_and_fix_gold():
    """
    Validate and fix gold prices:
    1. Get yesterday's closing price from history API
    2. Get today's live price from live API
    3. Update database
    """
    logger.info("🔄 Starting gold price validation and fix...")

    conn = get_conn()
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            gold18 REAL,
            ounce REAL
        )
    """)

    today = today_str()
    yesterday = yesterday_str()
    current_time = now_tehran().strftime("%H:%M")

    logger.info(f"📅 Today: {today}")
    logger.info(f"📅 Yesterday: {yesterday}")
    logger.info(f"🕐 Current time: {current_time}")

    # ============================================================
    # 1. Get yesterday's closing price (End of Day Candle)
    # ============================================================
    logger.info("-" * 60)
    logger.info("📊 Getting yesterday's closing price (End of Day Candle)...")

    history_data = fetch_gold_history()

    if history_data:
        # Find yesterday's close price
        yesterday_close = None
        for row in history_data:
            try:
                raw_date = row[6]  # Gregorian date
                date_obj = datetime.strptime(raw_date, "%Y/%m/%d")
                date_str = date_obj.strftime("%Y-%m-%d")

                if date_str == yesterday:
                    # Close price is in column 3
                    yesterday_close = parse_price(row[3])
                    break
            except Exception as e:
                continue

        if yesterday_close:
            existing_yesterday = get_row_by_date(conn, yesterday)

            if existing_yesterday:
                existing_date, existing_price = existing_yesterday
                if abs(existing_price - yesterday_close) > 0.01:
                    cursor.execute("""
                        UPDATE gold SET gold18 = ? WHERE date = ?
                    """, (yesterday_close, yesterday))
                    logger.info(f"🔄 Fixed yesterday's closing price:")
                    logger.info(f"   ❌ Old price: {existing_price:,.0f}")
                    logger.info(f"   ✅ Correct price: {yesterday_close:,.0f}")
                else:
                    logger.info(f"✅ Yesterday's price is correct: {yesterday_close:,.0f}")
            else:
                cursor.execute("""
                    INSERT INTO gold (date, gold18) VALUES (?, ?)
                """, (yesterday, yesterday_close))
                logger.info(f"➕ Added yesterday's closing price: {yesterday_close:,.0f}")
        else:
            logger.warning(f"⚠️ Yesterday's closing price not found in history API")
    else:
        logger.warning(f"⚠️ Failed to get history data")

    # ============================================================
    # 2. Get today's live price (Intraday)
    # ============================================================
    logger.info("-" * 60)
    logger.info("📊 Getting today's live price (Intraday)...")

    live_price, live_date = fetch_gold_live()

    if live_price and live_date == today:
        existing_today = get_row_by_date(conn, today)

        if existing_today:
            existing_date, existing_price = existing_today
            if abs(existing_price - live_price) > 0.01:
                cursor.execute("""
                    UPDATE gold SET gold18 = ? WHERE date = ?
                """, (live_price, today))
                logger.info(f"🔄 Updated today's live price:")
                logger.info(f"   ❌ Old price: {existing_price:,.0f}")
                logger.info(f"   ✅ New price: {live_price:,.0f}")
            else:
                logger.info(f"✅ Today's live price is correct: {live_price:,.0f}")
        else:
            cursor.execute("""
                INSERT INTO gold (date, gold18) VALUES (?, ?)
            """, (today, live_price))
            logger.info(f"➕ Added today's live price: {live_price:,.0f}")
    else:
        logger.warning(f"⚠️ Could not get live price for today")

        # Fallback: if live API fails, use the latest price from history API
        if history_data:
            latest_price = parse_price(history_data[0][3])
            if latest_price:
                existing_today = get_row_by_date(conn, today)
                if not existing_today:
                    cursor.execute("""
                        INSERT INTO gold (date, gold18) VALUES (?, ?)
                    """, (today, latest_price))
                    logger.info(f"➕ Added today's price from history (fallback): {latest_price:,.0f}")

    conn.commit()

    # ============================================================
    # Final Report
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 Gold Price Update Report")
    print("=" * 70)

    # Show last 5 records
    last_records = cursor.execute(
        "SELECT date, gold18 FROM gold ORDER BY date DESC LIMIT 5"
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


def check_gold_health():
    """Check gold data health"""
    logger.info("🔍 Checking gold data health...")

    conn = get_conn()
    cursor = conn.cursor()

    rows = cursor.execute(
        "SELECT date, gold18 FROM gold ORDER BY date DESC"
    ).fetchall()

    if not rows:
        logger.warning("⚠️ No data found in database!")
        conn.close()
        return False

    print("\n" + "=" * 70)
    print("📊 Gold Data Health Report")
    print("=" * 70)
    print(f"📅 Total records: {len(rows)}")

    print("\n📋 Last 10 records:")
    print(f"{'Date':<15} {'Price (IRR)':<20} {'Status':<10}")
    print("-" * 50)

    problems = 0
    for date_str, price in rows[:10]:
        status = "✅ VALID"
        if price is None or price <= 0:
            status = "❌ INVALID"
            problems += 1
        print(f"{date_str:<15} {price:>15,.0f}    {status}")

    print("-" * 50)

    print("\n🔍 Checking unusual fluctuations (>10%):")
    issues_found = 0
    for i in range(len(rows) - 1):
        try:
            current_price = rows[i][1]
            next_price = rows[i + 1][1]

            if current_price and next_price and current_price > 0 and next_price > 0:
                change_pct = abs((current_price - next_price) / next_price * 100)
                if change_pct > 10:
                    print(f"  ⚠️ {rows[i][0]}: Fluctuation {change_pct:.1f}% (Price: {current_price:,.0f} - Previous: {next_price:,.0f})")
                    issues_found += 1
        except:
            continue

    if issues_found == 0:
        print("  ✅ No unusual fluctuations found")

    print("=" * 70)

    if problems > 0:
        print(f"\n⚠️ {problems} issues found in data!")
        print("💡 Suggestion: Run fix command: python -m scrapers.gold fix")
        conn.close()
        return False
    else:
        print("\n✅ All data is healthy!")
        conn.close()
        return True


# ============================================================
# Main Execution
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            check_gold_health()
        elif command == "fix":
            validate_and_fix_gold()
            check_gold_health()
        else:
            print("Available commands:")
            print("  python -m scrapers.gold check  - Just check data")
            print("  python -m scrapers.gold fix    - Check and fix")
    else:
        validate_and_fix_gold()