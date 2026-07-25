import requests
import sqlite3
import re
from datetime import datetime

DB_FILE = r"D:\car_project\bama.db"
API_URL = "https://api.tgju.org/v1/market/indicator/summary-table-data/geram18"

def parse_price(text):
    if text is None:
        return None
    text = str(text)
    text = re.sub(r"[^0-9.,]", "", text)
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None

def get_last_date(conn):
    row = conn.execute("SELECT MAX(date) FROM gold").fetchone()
    return row[0] if row and row[0] else None

def update_gold():
    print("Checking for new gold data...")

    params = {
        "lang": "fa",
        "draw": "1",
        "start": "0",
        "length": "20",
        "convert_to_ad": "1"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tgju.org/",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json().get("data", [])
    except Exception as e:
        print(f"Failed to fetch data from TGJU: {e}")
        return

    if not data:
        print("No data received.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            gold18 REAL
        )
    """)

    last_date = get_last_date(conn)
    print(f"Last stored date: {last_date if last_date else 'None'}")

    new_rows = 0

    for row in data:
        try:
            raw_price = row[3]
            raw_date = row[6]

            price = parse_price(raw_price)
            date_obj = datetime.strptime(raw_date, "%Y/%m/%d")
            date_str = date_obj.strftime("%Y-%m-%d")

            if price is None:
                continue

            if last_date and date_str <= last_date:
                continue

            cursor.execute("""
                INSERT INTO gold (date, gold18)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET gold18 = excluded.gold18
            """, (date_str, price))
            new_rows += 1

        except Exception:
            continue

    conn.commit()
    conn.close()

    if new_rows > 0:
        print(f"Done. {new_rows} new rows inserted or updated.")
    else:
        print("No new rows were found.")

if __name__ == "__main__":
    update_gold()
