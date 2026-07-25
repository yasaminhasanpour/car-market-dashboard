import asyncio
import aiohttp
import sqlite3
import os
import pandas as pd

# ========================
# CONFIG
# ========================

PROJECT_DIR = r"D:\car_project"
DB_FILE = os.path.join(PROJECT_DIR, "bama.db")

BASE_URL = "https://bama.ir/cad/api/search"
PAGE_SIZE = 12
EMPTY_PAGE_STOP = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://bama.ir/",
    "Origin": "https://bama.ir"
}

# کلمات کلیدی که نشان‌دهنده آگهی پیش‌فروش یا حواله هستند
PRESALE_KEYWORDS = [
    "پیش فروش",
    "پیش‌فروش",
    "پیشفروش",
    "حواله",
]

# ========================
# DATABASE
# ========================

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            ad_id         TEXT PRIMARY KEY,
            brand         TEXT,
            title         TEXT,
            mileage       TEXT,
            modified_date TEXT,
            price         INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_brand_title ON ads(brand, title)")
    conn.commit()

# ========================
# PRICE FILTER
# Filters both unreasonably low AND unreasonably high prices
# (e.g. typo with an extra zero) using an IQR-based range
# ========================

def is_price_valid(price, brand, title, conn):
    if price is None or price <= 0:
        return False

    df = pd.read_sql_query("""
        SELECT price FROM ads
        WHERE brand = ? AND title = ? AND price > 0
    """, conn, params=(brand, title))

    if len(df) < 5:
        return True

    Q1    = df["price"].quantile(0.25)
    Q3    = df["price"].quantile(0.75)
    IQR   = Q3 - Q1
    lower = Q1 - 2 * IQR
    upper = Q3 + 3 * IQR  # سقف هم اضافه شد تا قیمت‌های اشتباهاً بزرگ (مثلاً یه صفر اضافه) رد بشن

    return lower <= price <= upper

# ========================
# PRESALE / HAVALE FILTER
# ========================

def is_presale_or_havale(ad, row):
    """
    آگهی‌های پیش‌فروش و حواله را تشخیص می‌دهد.
    هم متن‌های شناخته‌شده (title, mileage) و هم چند فیلد رایج دیگر
    که ممکن است در پاسخ API این اطلاعات را حمل کنند بررسی می‌شود.
    """
    detail = ad.get("detail") or {}

    candidate_texts = [
        row.get("title"),
        row.get("mileage"),
        detail.get("subtitle"),
        detail.get("description"),
        detail.get("adType"),
        detail.get("saleType"),
        ad.get("adType"),
        ad.get("label"),
        ad.get("badge"),
    ]

    # برخی پاسخ‌ها ممکن است لیست تگ داشته باشند
    tags = ad.get("tags") or detail.get("tags")
    if isinstance(tags, list):
        candidate_texts.extend(tags)

    for text in candidate_texts:
        if not text:
            continue
        text = str(text)
        if any(keyword in text for keyword in PRESALE_KEYWORDS):
            return True

    return False

# ========================
# HELPERS
# ========================

def normalize_price(value):
    try:
        if value is None:
            return None
        if isinstance(value, dict):
            value = value.get("price")
        s = str(value).replace(",", "").replace(" ", "")
        return int(float(s))
    except:
        return None

def extract_ads(payload):
    if not isinstance(payload, dict):
        return []
    ads = []
    raw = []
    if "data" in payload and "ads" in payload["data"]:
        raw = payload["data"]["ads"]
    elif "ads" in payload:
        raw = payload["ads"]

    for ad in raw:
        # رد کردن بنر و آگهی‌های بدون detail
        if ad.get("type") == "banner":
            continue
        if not ad.get("detail"):
            continue
        ads.append(ad)

    return ads

def parse_ad(ad):
    detail        = ad.get("detail") or {}
    ad_id         = detail.get("code") or ad.get("id")
    brand         = detail.get("brand")
    title         = detail.get("title")
    mileage       = detail.get("mileage")
    modified_date = detail.get("modified_date")

    raw_price = None
    if isinstance(ad.get("price"), dict):
        raw_price = ad["price"].get("price")
    else:
        raw_price = ad.get("price")

    return {
        "ad_id":         str(ad_id) if ad_id else None,
        "brand":         brand,
        "title":         title,
        "mileage":       mileage,
        "modified_date": modified_date,
        "price":         normalize_price(raw_price)
    }

# ========================
# NETWORK
# ========================

async def fetch_page(session, page_index):
    params = {"pageIndex": page_index, "pageSize": PAGE_SIZE}
    try:
        async with session.get(
            BASE_URL, params=params,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    except Exception as e:
        print(f"  [fetch error] page {page_index}: {e}")
        return None

# ========================
# MAIN UPDATE
# ========================

async def update_bama_daily():
    conn = get_conn()
    init_db(conn)
    cur = conn.cursor()

    empty_streak    = 0
    page            = 0
    total_new       = 0
    total_skipped   = 0
    total_presale   = 0

    print("=" * 55)
    print("Bama scraper started — fetching all pages...")
    print("=" * 55)

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            payload = await fetch_page(session, page)
            ads     = extract_ads(payload)

            if not ads:
                empty_streak += 1
                print(f"Page {page:>4} | Empty ({empty_streak}/{EMPTY_PAGE_STOP})")
                if empty_streak >= EMPTY_PAGE_STOP:
                    print("Empty page limit reached — stopping.")
                    break
                page += 1
                continue

            empty_streak = 0
            page_new     = 0
            page_dup     = 0
            page_skip    = 0
            page_presale = 0

            for ad in ads:
                row = parse_ad(ad)

                if not row["ad_id"]:
                    continue

                if not row["price"] or row["price"] <= 0:
                    page_skip += 1
                    continue

                if not row["mileage"] or "صفر" not in str(row["mileage"]):
                    page_skip += 1
                    continue

                if not row["brand"] or not row["title"]:
                    page_skip += 1
                    continue

                # رد کردن آگهی‌های پیش‌فروش و حواله
                if is_presale_or_havale(ad, row):
                    page_presale  += 1
                    total_presale += 1
                    continue

                if not is_price_valid(row["price"], row["brand"], row["title"], conn):
                    page_skip    += 1
                    total_skipped += 1
                    continue

                cur.execute("""
                    INSERT OR IGNORE INTO ads
                    (ad_id, brand, title, mileage, modified_date, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row["ad_id"], row["brand"], row["title"],
                    row["mileage"], row["modified_date"], row["price"]
                ))

                if cur.rowcount == 0:
                    page_dup += 1
                else:
                    page_new  += 1
                    total_new += 1

            conn.commit()
            print(f"Page {page:>4} | New: {page_new:>3} | Dup: {page_dup:>3} | Skip: {page_skip:>3} | Presale/Havale: {page_presale:>3} | Total new: {total_new}")

            page += 1

    total_in_db = conn.execute("SELECT COUNT(*) FROM ads").fetchone()[0]
    conn.close()

    print("=" * 55)
    print(f"Done.")
    print(f"New ads saved         : {total_new}")
    print(f"Ads skipped           : {total_skipped}")
    print(f"Presale/Havale skipped: {total_presale}")
    print(f"Total in DB           : {total_in_db}")
    print("=" * 55)

if __name__ == "__main__":
    asyncio.run(update_bama_daily())