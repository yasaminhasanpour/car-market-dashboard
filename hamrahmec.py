import requests
import sqlite3
import re
import time
from datetime import datetime

# ========================
# CONFIG
# ========================

DB_FILE = r"D:\car_project\bama.db"   # همون دیتابیس خودمون

BASE_HTML_URL = "https://www.hamrah-mechanic.com/cars-for-sale/"
DATA_URL_TEMPLATE = "https://www.hamrah-mechanic.com/_next/data/{build_id}/cars-for-sale.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.hamrah-mechanic.com/cars-for-sale/?km=0",
    "x-nextjs-data": "1",
}

PAGE_SIZE_GUESS = 24          # از پاسخ خودِ سایت گرفتیم (count)
PAGE_PARAM_CANDIDATES = ["page", "pageNumber", "pageIndex", "p"]
MAX_RETRY = 5
RETRY_DELAY = 4


# ========================
# DATABASE
# ========================

def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hm_ads (
            order_id      INTEGER PRIMARY KEY,
            car_id        INTEGER,
            brand         TEXT,
            model         TEXT,
            car_type      TEXT,
            car_name_fa   TEXT,
            car_year      TEXT,
            city          TEXT,
            gearbox       TEXT,
            km            INTEGER,
            price         INTEGER,
            scraped_date  TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hm_brand_model ON hm_ads(brand, model)")
    conn.commit()


# ========================
# BUILD ID (چون با هر دیپلوی سایت عوض میشه)
# ========================

def get_build_id():
    r = requests.get(BASE_HTML_URL, params={"km": 0}, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=20)
    r.raise_for_status()
    match = re.search(r'"buildId":"([^"]+)"', r.text)
    if not match:
        raise RuntimeError("build-id تو صفحه پیدا نشد؛ ممکنه ساختار سایت عوض شده باشه.")
    return match.group(1)


# ========================
# NETWORK
# ========================

def fetch_page(build_id, extra_params):
    url = DATA_URL_TEMPLATE.format(build_id=build_id)
    params = {"km": 0}
    params.update(extra_params)

    for attempt in range(MAX_RETRY):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 404:
                return None  # build-id اشتباهه یا صفحه‌ای وجود نداره
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  [fetch error] attempt {attempt + 1}/{MAX_RETRY}: {e}")
            time.sleep(RETRY_DELAY)

    return None


def extract_cars(payload):
    if not payload:
        return []
    try:
        return payload["pageProps"]["cars"]["list"]
    except (KeyError, TypeError):
        return []


def extract_total_count(payload):
    try:
        return payload["pageProps"]["cars"]["totalCount"]
    except (KeyError, TypeError):
        return None


# ========================
# پیدا کردن اسم درست پارامتر صفحه‌بندی
# ========================

def detect_page_param(build_id):
    page1_payload = fetch_page(build_id, {})
    page1_cars = extract_cars(page1_payload)
    page1_ids = set(c.get("orderId") for c in page1_cars)

    if not page1_ids:
        raise RuntimeError("حتی صفحه‌ی اول هم داده‌ای برنگردوند؛ اسکریپت رو متوقف می‌کنیم.")

    for candidate in PAGE_PARAM_CANDIDATES:
        test_payload = fetch_page(build_id, {candidate: 2})
        test_cars = extract_cars(test_payload)
        test_ids = set(c.get("orderId") for c in test_cars)

        if test_ids and test_ids != page1_ids:
            print(f"✅ پارامتر صفحه‌بندی پیدا شد: '{candidate}'")
            return candidate

    print("⚠️ هیچ‌کدوم از پارامترهای رایج جواب نداد؛ فقط صفحه‌ی اول رو می‌گیریم.")
    return None


# ========================
# PARSE AD
# ========================

def parse_car(car):
    return {
        "order_id": car.get("orderId"),
        "car_id": car.get("carId"),
        "brand": car.get("brandEnglishName"),
        "model": car.get("modelEnglishName"),
        "car_type": car.get("carTypeName"),
        "car_name_fa": car.get("carNamePersian"),
        "car_year": car.get("carYear"),
        "city": car.get("cityNamePersian"),
        "gearbox": car.get("gearBoxPersian"),
        "km": car.get("km"),
        "price": car.get("price"),
    }


# ========================
# MAIN
# ========================

def update_hm_ads():
    print("=" * 55)
    print("Hamrah-Mechanic scraper started (zero-km, inspected cars)")
    print("=" * 55)

    conn = get_conn()
    init_db(conn)
    cur = conn.cursor()

    build_id = get_build_id()
    print(f"Build ID: {build_id}")

    page_param = detect_page_param(build_id)

    total_new = 0
    total_dup = 0
    total_skip = 0

    page_num = 1
    total_count = None
    scraped_date = datetime.now().strftime("%Y-%m-%d")

    while True:
        extra = {} if page_param is None or page_num == 1 else {page_param: page_num}
        payload = fetch_page(build_id, extra)
        cars = extract_cars(payload)

        if total_count is None:
            total_count = extract_total_count(payload)

        if not cars:
            print(f"Page {page_num:>3} | خالی — پایان.")
            break

        page_new = 0
        page_dup = 0
        page_skip = 0

        for car in cars:
            row = parse_car(car)

            if not row["order_id"]:
                page_skip += 1
                continue

            if row["km"] != 0:
                page_skip += 1
                continue

            if car.get("isSold") or car.get("comingSoon"):
                page_skip += 1
                continue

            if not row["price"] or row["price"] <= 0:
                page_skip += 1
                continue

            cur.execute("""
                INSERT OR IGNORE INTO hm_ads
                (order_id, car_id, brand, model, car_type, car_name_fa,
                 car_year, city, gearbox, km, price, scraped_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["order_id"], row["car_id"], row["brand"], row["model"],
                row["car_type"], row["car_name_fa"], row["car_year"],
                row["city"], row["gearbox"], row["km"], row["price"],
                scraped_date
            ))

            if cur.rowcount == 0:
                page_dup += 1
            else:
                page_new += 1

        conn.commit()
        total_new += page_new
        total_dup += page_dup
        total_skip += page_skip

        print(f"Page {page_num:>3} | New: {page_new:>3} | Dup: {page_dup:>3} | Skip: {page_skip:>3}")

        if page_param is None:
            break  # فقط یه صفحه می‌تونیم بگیریم

        if total_count and (page_num * PAGE_SIZE_GUESS) >= total_count:
            print("به انتهای لیست رسیدیم (بر اساس totalCount).")
            break

        page_num += 1
        time.sleep(0.5)  # به سرور فشار نیاریم

    total_in_db = conn.execute("SELECT COUNT(*) FROM hm_ads").fetchone()[0]
    conn.close()

    print("=" * 55)
    print("Done.")
    print(f"New ads saved : {total_new}")
    print(f"Duplicates    : {total_dup}")
    print(f"Skipped       : {total_skip}")
    print(f"Total in DB   : {total_in_db}")
    print("=" * 55)


if __name__ == "__main__":
    update_hm_ads()