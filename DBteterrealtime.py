
import requests
import sqlite3
import time
from datetime import datetime, timedelta

DB_FILE = r"D:\car_project\bama.db"
URL = "https://api.wallex.ir/v1/udf/history"

MAX_RETRY = 10
RETRY_DELAY = 5


def init_tether_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tether (
            date TEXT PRIMARY KEY,
            close REAL
        )
    """)
    conn.commit()


def update_daily_tether():
    attempt = 0

    while attempt < MAX_RETRY:
        try:
            conn = sqlite3.connect(DB_FILE)
            init_tether_table(conn)

            cursor = conn.cursor()
            cursor.execute("SELECT MAX(date) FROM tether")
            result = cursor.fetchone()
            last_date_str = result[0]

            if last_date_str:
                last_date_dt = datetime.strptime(last_date_str, "%Y-%m-%d")
                start_dt = last_date_dt + timedelta(days=1)
            else:
                # اگر جدول خالی بود، از یه تاریخ پایه شروع کن
                start_dt = datetime(2026, 1, 1)

            end_dt = datetime.now()

            # اگر چیزی برای آپدیت نبود
            if start_dt.date() > end_dt.date():
                print("No new daily candles.")
                conn.close()
                return

            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp())

            params = {
                "symbol": "USDTTMN",
                "resolution": "D",
                "from": start_ts,
                "to": end_ts
            }

            r = requests.get(URL, params=params, timeout=15)
            r.raise_for_status()

            data = r.json()

            if "t" in data and len(data["t"]) > 0:
                rows_inserted = 0

                for ts, close_price in zip(data["t"], data["c"]):
                    date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

                    conn.execute("""
                        INSERT OR REPLACE INTO tether (date, close)
                        VALUES (?, ?)
                    """, (date_str, float(close_price)))

                    rows_inserted += 1

                conn.commit()

                cursor.execute("SELECT MAX(date) FROM tether")
                new_last_date = cursor.fetchone()[0]

                print(f"✅ Updated tether table. Inserted/updated {rows_inserted} rows.")
                print(f"✅ Last date in DB: {new_last_date}")
            else:
                print("No new daily candles.")

            conn.close()
            return

        except Exception as e:
            attempt += 1
            print(f"❌ Attempt {attempt}/{MAX_RETRY} failed: {e}")

            try:
                conn.close()
            except:
                pass

            if attempt >= MAX_RETRY:
                print("⛔ Max retries reached. Script stopped.")
                return

            time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    update_daily_tether()






