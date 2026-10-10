# کلمات آگهی‌های پیش‌فروش و حواله (هم توی اسکرپر هم داشبورد استفاده می‌شه)
PRESALE_KEYWORDS = ["پیش فروش", "پیش‌فروش", "پیشفروش", "حواله"]

# ضریب‌های فیلتر IQR: پایین ۲ برابر، بالا ۳ برابر
IQR_LOWER_MULT = 2
IQR_UPPER_MULT = 3


def iqr_bounds(prices):
    """prices یه pandas Series از قیمت‌هاست. خروجی: (حد پایین، حد بالا)"""
    q1, q3 = prices.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - IQR_LOWER_MULT * iqr, q3 + IQR_UPPER_MULT * iqr