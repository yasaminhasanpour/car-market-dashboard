import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import jdatetime
import streamlit.components.v1 as components

st.set_page_config(
    page_title="خودرو مارکت",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# استایل: فونت فارسی، راست‌به‌چپ، پالت ترمینال مالی مینیمال
# ============================================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/estedad-font@v3.0.1/dist/font-face.css');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, h1, h2, h3, label {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
}

/* ---------- پس‌زمینه‌ی عمیق‌تر با گرادینت شعاعی ملایم ---------- */
.stApp {
    background:
        radial-gradient(ellipse 900px 500px at 90% -5%, rgba(201,162,39,0.07), transparent 60%),
        radial-gradient(ellipse 800px 500px at -5% 105%, rgba(76,141,255,0.05), transparent 60%),
        #0A0C10 !important;
}

/* ---------- راست‌چین کردن محتوای اصلی ---------- */
section.main {
    direction: rtl;
}
section.main .block-container {
    direction: rtl;
    text-align: right;
    padding-top: 2.2rem;
}
section.main [data-testid="stExpander"] {
    direction: rtl;
    text-align: right;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    background: linear-gradient(145deg, #12161C, #0e1116) !important;
}
section.main [data-testid="stDataFrame"] {
    direction: rtl;
}

h1 { font-size: 1.9rem !important; font-weight: 600 !important; text-align: right; }
h2, h3 { font-weight: 600 !important; text-align: right; }

.sidebar-label {
    font-size: 11px; color: #7C8494; margin: 0 0 5px;
    display: flex; align-items: center; justify-content: center; gap: 5px;
}
section[data-testid="stSidebar"] { text-align: center; direction: ltr; }
section[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #0d1015, #0A0C10) !important;
    border-left: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stSlider { text-align: center; }
section[data-testid="stSidebar"] .sidebar-label { direction: rtl; }

.app-title {
    font-family: 'Estedad', 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px;
    background: linear-gradient(90deg, #E4E7EB, #C9A227 60%, #E4E7EB);
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 5s linear infinite;
}
@keyframes shine { to { background-position: -200% center; } }

h1 { position: relative; display: inline-block; }
h1::after {
    content: "";
    position: absolute;
    right: 0; bottom: -6px;
    width: 56px; height: 3px;
    border-radius: 3px;
    background: linear-gradient(90deg, #C9A227, transparent);
}

/* خط جداکننده‌ی ظریف زیر سایدبار */
section[data-testid="stSidebar"] hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,162,39,0.35), transparent);
    margin: 18px 0;
}

/* دکمه‌ی تحلیل هوشمند */
section[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(145deg, #171B22, #10141a) !important;
    border: 1px solid rgba(201,162,39,0.3) !important;
    color: #E4E7EB !important;
    border-radius: 8px !important;
    transition: all 0.25s ease !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    border-color: rgba(201,162,39,0.7) !important;
    box-shadow: 0 0 16px rgba(201,162,39,0.12) !important;
}

/* اسکرول بار سفارشی */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0A0C10; }
::-webkit-scrollbar-thumb { background: #C9A227; border-radius: 4px; }

@media (max-width: 640px) {
    h1 { font-size: 1.4rem !important; }
}
</style>
""", unsafe_allow_html=True)


def icon(name, color, size=17):
    """SVG آیکون‌های خطی ساده، بدون ایموجی"""
    icons = {
        "car": '<path d="M3 13l1.5-4.5A2 2 0 0 1 6.4 7h11.2a2 2 0 0 1 1.9 1.5L21 13"/><rect x="2" y="13" width="20" height="5" rx="1"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/>',
        "dollar": '<path d="M12 2v20M17 6H9.5a3 3 0 0 0 0 6h5a3 3 0 0 1 0 6H6"/>',
        "target": '<path d="M3 17l5-5 4 4 8-9M20 7h-4M20 7v4"/>',
        "check": '<path d="M20 6L9 17l-5-5"/>',
        "warning": '<path d="M12 9v4M12 17h.01M10.3 3.9L2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
        "minus": '<path d="M5 12h14"/>',
        "chart_bars": '<path d="M4 19h16" stroke-linecap="round"/><path d="M6 19V13M11 19V8M16 19V11" stroke-linecap="round"/>',
        "sparkle": '<path d="M12 3v3m0 12v3m9-9h-3M6 12H3m14.5-6.5l-2 2m-9 9l-2 2m0-13l2 2m9 9l2 2"/>',
        "coin": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v9M9.2 9.8c0-1.2 1.2-1.8 2.8-1.8s2.8.7 2.8 1.7c0 2.3-5.6 1-5.6 3.3 0 1 1.2 1.7 2.8 1.7s2.8-.6 2.8-1.8"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2">{icons[name]}</svg>'


conn = sqlite3.connect("bama.db", check_same_thread=False)

EXCLUDED_KEYWORDS = ["پیش فروش", "پیش‌فروش", "پیشفروش", "حواله"]
exclude_clause = " AND ".join(["title NOT LIKE ?"] * len(EXCLUDED_KEYWORDS))
exclude_params = [f"%{kw}%" for kw in EXCLUDED_KEYWORDS]

MIN_ADS_PER_DAY = 2
BASELINE_DAYS = 5
MAX_GAP_DAYS = 60

def to_jalali_str(dt):
    g = dt.date() if hasattr(dt, "date") else dt
    j = jdatetime.date.fromgregorian(date=g)
    return j.strftime("%Y/%m/%d")

# ---------- سایدبار ----------
st.sidebar.markdown(
    f'<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:22px;">'
    f'{icon("chart_bars", "#C9A227", 26)}'
    f'<p class="app-title" style="font-size:24px;margin:0;">خودرو مارکت</p></div>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    f'<p class="sidebar-label">{icon("car", "#7C8494", 13)} برند</p>',
    unsafe_allow_html=True
)
brands = pd.read_sql(
    f"SELECT DISTINCT brand FROM ads WHERE {exclude_clause} ORDER BY brand",
    conn, params=exclude_params
)
brand = st.sidebar.selectbox("برند", brands["brand"].dropna().tolist(), label_visibility="collapsed")

# ---------- مدل ----------
st.sidebar.markdown('<p class="sidebar-label">مدل</p>', unsafe_allow_html=True)

titles_df = pd.read_sql(
    f"SELECT DISTINCT title FROM ads WHERE brand = ? AND {exclude_clause} ORDER BY title",
    conn, params=[brand] + exclude_params
)
titles = titles_df["title"].dropna().tolist()

trims_df = pd.read_sql(
    f"""
    SELECT DISTINCT title, trim FROM ads
    WHERE brand = ? AND trim IS NOT NULL AND trim <> '' AND {exclude_clause}
    """,
    conn, params=[brand] + exclude_params
)

model_options = []  # (label, title, trim_filter_or_None)
for t in titles:
    t_trims = sorted(trims_df.loc[trims_df["title"] == t, "trim"].dropna().unique().tolist())

    if len(t_trims) == 1:
        label = f"{t} - {t_trims[0]}"
        model_options.append((label, t, None))
    else:
        model_options.append((t, t, None))
        for tr in t_trims:
            model_options.append((f"{t} - {tr}", t, tr))

option_labels = [o[0] for o in model_options]
selected_label = st.sidebar.selectbox("مدل", option_labels, label_visibility="collapsed")
_selected = next(o for o in model_options if o[0] == selected_label)
model, selected_trim = _selected[1], _selected[2]

# ---------- لودینگ کل صفحه ----------
loader_placeholder = st.empty()
loader_placeholder.markdown(f"""
<div style="background:#0A0C10;border-radius:8px;padding:70px 20px;
            display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;">
    <div style="animation:pulse 1.4s ease-in-out infinite;">
        {icon("chart_bars", "#C9A227", 40)}
    </div>
    <p style="font-size:13px;color:#7C8494;margin:0;">در حال دریافت داده‌ها...</p>
</div>
<style>
@keyframes pulse {{ 0%,100% {{ opacity:0.4; }} 50% {{ opacity:1; }} }}
</style>
""", unsafe_allow_html=True)

# ---------- قیمت خودرو (خام) ----------
trim_clause = ""
trim_params = []
if selected_trim:
    trim_clause = "AND trim = ?"
    trim_params = [selected_trim]

df_car = pd.read_sql(
    f"""
    SELECT substr(modified_date, 1, 10) AS day, price
    FROM ads
    WHERE brand = ? AND title = ? {trim_clause} AND price > 0
    """,
    conn, params=[brand, model] + trim_params
)
df_car["price"] = pd.to_numeric(df_car["price"], errors="coerce")
df_car = df_car.dropna()

q1, q3 = df_car["price"].quantile([0.25, 0.75])
iqr = q3 - q1
lower, upper = q1 - 2 * iqr, q3 + 3 * iqr
df_car = df_car[(df_car["price"] >= lower) & (df_car["price"] <= upper)]

df_car = df_car.groupby("day", as_index=False).agg(
    price=("price", "median"),
    ads_count=("price", "count")
)
df_car = df_car[df_car["ads_count"] >= MIN_ADS_PER_DAY].drop(columns="ads_count")
df_car["day"] = pd.to_datetime(df_car["day"])

df_tether = pd.read_sql("SELECT date, close FROM tether", conn)
df_tether["date"] = pd.to_datetime(df_tether["date"])
df_tether["close"] = pd.to_numeric(df_tether["close"], errors="coerce")
df_tether = df_tether.dropna()

df = pd.merge(df_car, df_tether, left_on="day", right_on="date", how="inner")
df = df.drop(columns=["date"])
df = df.sort_values("day").reset_index(drop=True)

df["gap_days"] = df["day"].diff().dt.days
df["segment"] = (df["gap_days"] > MAX_GAP_DAYS).cumsum()
latest_segment = df["segment"].max()
df = df[df["segment"] == latest_segment].reset_index(drop=True)
df = df.drop(columns=["gap_days", "segment"])

# ---------- قیمت طلا ----------
df_gold = pd.read_sql("SELECT date, gold18 FROM gold", conn)
df_gold["date"] = pd.to_datetime(df_gold["date"])
df_gold["gold18"] = pd.to_numeric(df_gold["gold18"], errors="coerce")
df_gold = df_gold.dropna().sort_values("date")

df = pd.merge(df, df_gold, left_on="day", right_on="date", how="left")
df = df.drop(columns=["date"])
df["gold18"] = df["gold18"].ffill().bfill()
has_gold = df["gold18"].notna().any()

if len(df) < 2:
    loader_placeholder.empty()
    extra = f" (نسخه {selected_trim})" if selected_trim else ""
    st.warning(f"داده کافی برای این مدل{extra} وجود ندارد.")
    st.stop()

total_span_days = max((df["day"].max() - df["day"].min()).days, 1)
min_slider_days = min(2, total_span_days)

if min_slider_days >= total_span_days:
    loader_placeholder.empty()
    st.warning("بازه‌ی زمانی داده‌های این مدل خیلی کوتاهه (کمتر از ۲ روز) و برای نمایش نمودار کافی نیست.")
    st.stop()

st.sidebar.markdown('<hr>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sidebar-label">بازه نمایش (روز اخیر)</p>', unsafe_allow_html=True)
days_to_show = st.sidebar.slider(
    "بازه نمایش", min_value=min_slider_days, max_value=total_span_days,
    value=total_span_days, step=5, format="%d روز", label_visibility="collapsed"
)

cutoff_date = df["day"].max() - pd.Timedelta(days=days_to_show)
df = df[df["day"] >= cutoff_date].reset_index(drop=True)

if len(df) < 2:
    loader_placeholder.empty()
    st.warning("در این بازه‌ی زمانی داده‌ی کافی وجود ندارد. بازه را بزرگ‌تر کنید.")
    st.stop()

df["day_jalali"] = df["day"].apply(to_jalali_str)

n_base = min(BASELINE_DAYS, len(df))
car_baseline = df["price"].iloc[:n_base].mean()
tether_baseline = df["close"].iloc[:n_base].mean()

df["car_index"] = df["price"] / car_baseline * 100
df["tether_index"] = df["close"] / tether_baseline * 100

if has_gold:
    gold_baseline = df["gold18"].iloc[:n_base].mean()
    df["gold_index"] = df["gold18"] / gold_baseline * 100
    gold_growth = df["gold_index"].iloc[-1] - 100
else:
    gold_growth = None

car_growth = df["car_index"].iloc[-1] - 100
tether_growth = df["tether_index"].iloc[-1] - 100
buy_value_pct = tether_growth - car_growth

if has_gold:
    buy_value_gold_pct = gold_growth - car_growth
else:
    buy_value_gold_pct = None


def get_signal(value, vs_label):
    if value >= 10:
        return "buy", "check", "#34C77B", f"✅ فرصت خرید احتمالی — خودرو نسبت به {vs_label} عقب‌مانده است"
    elif value <= -10:
        return "sell", "warning", "#E24B4A", f"⚠️ خودرو نسبت به {vs_label} جلو زده — نسبتاً گران است"
    else:
        return "flat", "minus", "#7C8494", f"➖ رشد خودرو و {vs_label} تقریباً هم‌راستا بوده"


signal_kind, signal_icon, signal_color, signal_text = get_signal(buy_value_pct, "دلار")
if has_gold:
    gold_signal_kind, gold_signal_icon, gold_signal_color, gold_signal_text = get_signal(buy_value_gold_pct, "طلا")

loader_placeholder.empty()

trim_badge_html = f' <span style="font-size:12px;padding:3px 10px;border-radius:999px;background:rgba(201,162,39,0.12);border:1px solid rgba(201,162,39,0.35);color:#C9A227;">{selected_trim}</span>' if selected_trim else ""
st.markdown(f"<h1>مقایسه رشد {model}{trim_badge_html} با دلار و طلا</h1>", unsafe_allow_html=True)
st.caption(f"بازه‌ی نمایش: {days_to_show} روز اخیر  •  از {df['day_jalali'].iloc[0]} تا {df['day_jalali'].iloc[-1]}")

# ============================================================
# کارت‌های متریک + نوار سیگنال (کامپوننت HTML واحد)
# ============================================================

metrics = [
    {"label": "رشد قیمت خودرو", "value": car_growth, "icon": "car", "color": "#4C8DFF", "highlight": False},
    {"label": "رشد دلار", "value": tether_growth, "icon": "dollar", "color": "#34C77B", "highlight": False},
    {"label": "ارزش خرید نسبت به دلار", "value": buy_value_pct, "icon": "target", "color": "#34C77B", "highlight": True},
]
if has_gold:
    metrics.append({"label": "رشد طلا (۱۸ عیار)", "value": gold_growth, "icon": "coin", "color": "#D4AF37", "highlight": False})
    metrics.append({"label": "ارزش خرید نسبت به طلا", "value": buy_value_gold_pct, "icon": "target", "color": "#C9A227", "highlight": True})

signals_list = [(signal_kind, signal_icon, signal_color, signal_text)]
if has_gold:
    signals_list.append((gold_signal_kind, gold_signal_icon, gold_signal_color, gold_signal_text))

cards_html = ""
for i, m in enumerate(metrics):
    bg = f"rgba({int(m['color'][1:3],16)},{int(m['color'][3:5],16)},{int(m['color'][5:7],16)},0.12)"
    val_color = m["color"] if m["highlight"] else "#FFFFFF"
    cards_html += f"""
    <div class="metric-card {'highlight' if m['highlight'] else ''}" style="animation-delay:{i*0.08}s;">
        <div class="metric-icon" style="background:{bg};">{icon(m['icon'], m['color'])}</div>
        <div class="metric-text">
            <p class="metric-label">{m['label']}</p>
            <p class="metric-value" style="color:{val_color} !important;" data-target="{m['value']:.1f}">0%</p>
        </div>
    </div>
    """

signals_html = ""
for kind, s_icon, s_color, s_text in signals_list:
    signals_html += f'<div class="signal-box signal-{kind}" style="text-align:right;direction:rtl;justify-content:flex-start;">{icon(s_icon, s_color, 15)}<span style="text-align:right;width:100%;">{s_text}</span></div>'

metrics_component = f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

* {{ box-sizing: border-box; }}
html, body {{
    margin:0; padding:0;
    font-family:'Vazirmatn', Tahoma, sans-serif;
    direction: rtl;
    background-color: #0A0C10 !important;
}}

.cards-grid {{
    display:flex; flex-wrap:wrap; gap:12px; margin-bottom:2px;
    direction: rtl;
    justify-content: flex-end;
}}
.metric-card {{
    flex: 1 1 150px;
    min-width: 140px;
    background: linear-gradient(145deg, #12161C, #0e1116);
    border-radius: 10px;
    padding: 14px 16px;
    display: flex; align-items: center; gap: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    opacity: 0;
    transform: translateY(10px) scale(0.98);
    animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), 
                box-shadow 0.3s cubic-bezier(0.22, 1, 0.36, 1), 
                border-color 0.3s cubic-bezier(0.22, 1, 0.36, 1);
    text-align: right;
    direction: rtl;
    cursor: default;
    position: relative;
    overflow: hidden;
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.03), transparent);
    pointer-events: none;
}}
.metric-card:hover {{
    transform: translateY(-4px) scale(1.02);
    border-color: rgba(201,162,39,0.4);
    box-shadow: 0 12px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(201,162,39,0.15);
}}
.metric-card.highlight {{
    border: 1px solid rgba(201,162,39,0.35);
    animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards, glow 2.6s ease-in-out infinite;
}}
@keyframes fadeInUp {{ to {{ opacity: 1; transform: translateY(0) scale(1); }} }}
@keyframes glow {{
    0%, 100% {{ box-shadow: 0 0 0 rgba(201,162,39,0); }}
    50% {{ box-shadow: 0 0 24px rgba(201,162,39,0.15); }}
}}
.metric-icon {{
    width: 34px; height: 34px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}}
.metric-card:hover .metric-icon {{
    transform: scale(1.1) rotate(-5deg);
}}
.metric-text {{ text-align: right; flex: 1 1 auto; min-width: 0; }}
.metric-label {{ font-size: 13px; color: #C7CCD6 !important; margin: 0 0 5px; text-align: right !important; display: block; }}
.metric-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px; font-weight: 600; margin: 0;
    text-align: right !important;
    display: block;
}}

.signal-box {{
    border-radius: 8px;
    padding: 9px 16px;
    margin: 7px 0 0;
    font-size: 13px;
    display: flex; align-items: center; gap: 8px;
    text-align: right;
    direction: rtl;
    opacity: 0;
    animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    animation-delay: 0.35s;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}}
.signal-box:hover {{
    transform: scale(1.01);
}}
.signal-box span {{ color: #F2F4F7 !important; text-align: right !important; }}
.signal-buy   {{ background: rgba(52,199,123,0.10); border: 1px solid rgba(52,199,123,0.3); }}
.signal-buy:hover {{ box-shadow: 0 0 20px rgba(52,199,123,0.08); }}
.signal-sell  {{ background: rgba(226,75,74,0.10);  border: 1px solid rgba(226,75,74,0.3); }}
.signal-sell:hover {{ box-shadow: 0 0 20px rgba(226,75,74,0.08); }}
.signal-flat  {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); }}

@media (max-width: 640px) {{
    .metric-card {{ flex: 1 1 calc(50% - 6px); min-width: 0; padding: 12px; }}
    .metric-label {{ font-size: 11px; }}
    .metric-value {{ font-size: 15px; }}
    .signal-box {{ font-size: 12px; padding: 7px 12px; }}
}}
</style>

<div class="cards-grid">
  {cards_html}
</div>
{signals_html}

<script>
(function() {{
    var els = document.querySelectorAll('.metric-value[data-target]');
    els.forEach(function(el) {{
        var target = parseFloat(el.getAttribute('data-target'));
        var duration = 1000;
        var startTime = null;
        function step(ts) {{
            if (!startTime) startTime = ts;
            var progress = Math.min((ts - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = target * eased;
            var sign = (current >= 0) ? '+' : '';
            el.textContent = sign + current.toFixed(1) + '%';
            if (progress < 1) requestAnimationFrame(step);
        }}
        requestAnimationFrame(step);
    }});
}})();
</script>
"""

cards_height = 118 + (54 * len(signals_list))
components.html(metrics_component, height=cards_height, scrolling=False)

# ---------- نمودار با افکت رسم (مثل مداد) + ریسپانسیو موبایل ----------
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["day_jalali"], y=df["car_index"], mode="lines",
    name="رشد قیمت خودرو", line=dict(color="#4C8DFF", width=3)
))
fig.add_trace(go.Scatter(
    x=df["day_jalali"], y=df["tether_index"], mode="lines",
    name="رشد دلار", line=dict(color="#34C77B", width=3)
))
if has_gold:
    fig.add_trace(go.Scatter(
        x=df["day_jalali"], y=df["gold_index"], mode="lines",
        name="رشد طلا", line=dict(color="#D4AF37", width=3)
    ))
fig.update_layout(
    font=dict(family="Vazirmatn, Tahoma, sans-serif", size=14, color="#e2e8f0"),
    yaxis_title="شاخص رشد (پایه = 100)",
    xaxis_title="تاریخ (شمسی)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    autosize=True,
    hovermode="x unified",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(type="category", tickangle=-45, nticks=15, gridcolor="rgba(255,255,255,0.08)", title_standoff=40),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title_standoff=25),
    margin=dict(t=40, b=90, l=50, r=10),
    hoverlabel=dict(bgcolor="#1e293b", font_color="#e2e8f0", font_family="Vazirmatn, Tahoma, sans-serif", bordercolor="#4C8DFF"),
)

chart_html = fig.to_html(
    include_plotlyjs="cdn", full_html=False, div_id="growth_chart_div",
    config={"responsive": True, "displayModeBar": True, "displaylogo": False},
    default_width="100%", default_height="500px",
)

# نمودار داخل یک کارت شیشه‌ای هم‌استایل با metric cardها قرار می‌گیرد
chart_wrapped_html = f'<div class="chart-card">{chart_html}</div>'

draw_script = """
<style>
  html, body { margin: 0; padding: 0; background-color: #0A0C10 !important; }
  .chart-card {
      background: linear-gradient(145deg, #12161C, #0e1116);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 14px;
      padding: 14px 10px 4px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.35);
  }
  #growth_chart_div { width: 100% !important; height: 100% !important; }
  #growth_chart_div .plot-container { width: 100% !important; }
</style>
"""
components.html(chart_wrapped_html + draw_script, height=545)

# ---------- تحلیل هوشمند با AI (سایدبار) ----------
st.sidebar.markdown('<hr>', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">'
    f'{icon("sparkle", "#C9A227", 15)}<p style="font-size:13px;font-weight:600;margin:0;">تحلیل هوشمند</p></div>',
    unsafe_allow_html=True
)

if st.sidebar.button("تحلیل با هوش مصنوعی"):
    try:
        from ai_analysis import get_ai_insight
    except ImportError:
        get_ai_insight = None

    if get_ai_insight is None:
        st.sidebar.warning(
            "فایل ai_analysis.py پیدا نشد. این قابلیت هنوز راه‌اندازی نشده — "
            "بقیه‌ی داشبورد به‌طور عادی کار می‌کند."
        )
    else:
        with st.spinner("در حال تحلیل..."):
            gold_lines = (
                f"رشد قیمت طلا: {gold_growth:.1f}%\nاختلاف رشد نسبت به طلا: {buy_value_gold_pct:+.1f}%\n"
                if has_gold else ""
            )
            trim_line = f"نسخه: {selected_trim}\n" if selected_trim else ""
            data_summary = f"""
برند و مدل: {brand} {model}
{trim_line}بازه زمانی: {days_to_show} روز اخیر
رشد قیمت خودرو: {car_growth:.1f}%
رشد قیمت دلار: {tether_growth:.1f}%
اختلاف رشد نسبت به دلار: {buy_value_pct:+.1f}%
{gold_lines}"""
            if has_gold:
                instruction = (
                    "در حداکثر ۵ خط، خیلی خلاصه و شفاف تحلیل کن. توضیح بده که چون قیمت خودرو، "
                    "دلار و طلا در بلندمدت معمولاً با هم هماهنگ حرکت می‌کنند، عقب‌ماندگی رشد هرکدام "
                    "نسبت به بقیه ممکن است فرصت خرید باشد یا نشونه‌ی کاهش تقاضا. بر اساس اعداد رشد "
                    "بالا بگو کدام یک از این سه (خودرو، دلار، طلا) در حال حاضر عقب‌مانده‌تر به نظر "
                    "می‌رسد و توصیه نهایی بده: خرید دلار، خرید طلا یا خرید این خودرو؟"
                )
            else:
                instruction = (
                    "در حداکثر ۵ خط، خیلی خلاصه و شفاف تحلیل کن. توضیح بده که چون قیمت خودرو "
                    "در بلندمدت معمولاً خودش را با دلار هماهنگ می‌کند، عقب‌ماندگی رشد ممکن است "
                    "فرصت خرید باشد یا کاهش تقاضا. بر اساس عدد اختلاف رشد بگو کدام تفسیر محتمل‌تر "
                    "است و توصیه نهایی بده: خرید دلار بهتر است یا خرید این خودرو؟"
                )
            try:
                insight = get_ai_insight(data_summary, instruction)
                st.sidebar.markdown(f'<div class="ai-insight-box">{insight}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.sidebar.error(f"خطا در دریافت تحلیل: {e}")

with st.expander("جدول داده‌های خام"):
    cols = ["day_jalali", "price", "close", "car_index", "tether_index"]
    if has_gold:
        cols += ["gold18", "gold_index"]
    st.dataframe(df[cols])