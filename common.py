import jdatetime

# ============================================================
# ثابت‌های مشترک (دقیقاً همان مقادیر قبلی dash1.py)
# ============================================================
MIN_ADS_PER_DAY = 2
BASELINE_DAYS = 5
MAX_GAP_DAYS = 60


def to_jalali_str(dt):
    g = dt.date() if hasattr(dt, "date") else dt
    j = jdatetime.date.fromgregorian(date=g)
    return j.strftime("%Y/%m/%d")


def compute_growth_index(df, price_col, baseline_days=BASELINE_DAYS):
    """
    شاخص رشد (پایه = 100) — همان فرمولی که قبلاً مستقیم در dash1.py
    برای car_index/tether_index نوشته شده بود.
    خروجی: (ستون شاخص، درصد رشد نهایی)
    """
    n_base = min(baseline_days, len(df))
    baseline = df[price_col].iloc[:n_base].mean()
    index_series = df[price_col] / baseline * 100
    growth_pct = index_series.iloc[-1] - 100
    return index_series, growth_pct


# ============================================================
# آیکون‌های خطی SVG (بدون ایموجی) — دقیقاً همان دیکشنری قبلی dash1.py
# فقط یک آیکون جدید ("gold") برای بخش طلا اضافه شده.
# ============================================================
def icon(name, color, size=17):
    icons = {
        "car": '<path d="M3 13l1.5-4.5A2 2 0 0 1 6.4 7h11.2a2 2 0 0 1 1.9 1.5L21 13"/><rect x="2" y="13" width="20" height="5" rx="1"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/>',
        "dollar": '<path d="M12 2v20M17 6H9.5a3 3 0 0 0 0 6h5a3 3 0 0 1 0 6H6"/>',
        "target": '<path d="M3 17l5-5 4 4 8-9M20 7h-4M20 7v4"/>',
        "check": '<path d="M20 6L9 17l-5-5"/>',
        "warning": '<path d="M12 9v4M12 17h.01M10.3 3.9L2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
        "minus": '<path d="M5 12h14"/>',
        "chart_bars": '<path d="M4 19h16" stroke-linecap="round"/><path d="M6 19V13M11 19V8M16 19V11" stroke-linecap="round"/>',
        "sparkle": '<path d="M12 3v3m0 12v3m9-9h-3M6 12H3m14.5-6.5l-2 2m-9 9l-2 2m0-13l2 2m9 9l2 2"/>',
        # 🆕 آیکون جدید برای بخش طلا (یک سکه‌ی ساده)
        "gold": '<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8M9.5 10h3.2a1.6 1.6 0 0 1 0 3.2H9.8a1.6 1.6 0 0 0 0 3.2h3.2"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2">{icons[name]}</svg>'


def metric_card(label, value, icon_name, color, highlight=False):
    cls = "metric-card highlight" if highlight else "metric-card"
    bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)"
    return f"""
    <div class="{cls}">
        <div class="metric-icon" style="background:{bg};">{icon(icon_name, color)}</div>
        <div>
            <p class="metric-label">{label}</p>
            <p class="metric-value" style="color:{color if highlight else '#E4E7EB'};">{value}</p>
        </div>
    </div>
    """
