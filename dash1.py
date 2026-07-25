import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import jdatetime
import streamlit.components.v1 as components

st.set_page_config(
    page_title="پالس‌نرخ",
    page_icon="📈",  # یا مسیر یه فایل png/ico
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

h1 { font-size: 1.9rem !important; font-weight: 600 !important; text-align: right; }
h2, h3 { font-weight: 600 !important; text-align: right; }

/* ---------- کارت‌های متریک سفارشی ---------- */
.metric-card {
    background: #12161C;
    border-radius: 8px;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}
.metric-card.highlight { border: 1px solid rgba(201,162,39,0.35); }
.metric-icon {
    width: 34px; height: 34px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.metric-label { font-size: 14px; color: #A0A7B4; margin: 0 0 5px; }
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px; font-weight: 500; margin: 0; color: #E4E7EB;
}

/* ---------- نوار سیگنال خرید ---------- */
.signal-box {
    border-radius: 8px;
    padding: 10px 16px;
    margin: 14px 0 6px;
    font-size: 13px;
    display: flex; align-items: center; gap: 8px;
}
.signal-buy   { background: rgba(52,199,123,0.08); border: 1px solid rgba(52,199,123,0.25); }
.signal-sell  { background: rgba(226,75,74,0.08);  border: 1px solid rgba(226,75,74,0.25); }
.signal-flat  { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }

/* ---------- باکس تحلیل هوش مصنوعی (سایدبار) ---------- */
.ai-insight-box {
    background: #12161C;
    border: 1px solid rgba(201,162,39,0.25);
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 10px;
    font-size: 0.9rem;
    line-height: 1.8;
    text-align: right;
    direction: rtl;
}

/* ---------- سایدبار: لیبل‌ها با آیکون ---------- */
.sidebar-label {
    font-size: 11px; color: #7C8494; margin: 0 0 5px;
    display: flex; align-items: center; justify-content: center; gap: 5px;
}

/* ---------- سایدبار: وسط‌چین کردن کل محتوا ---------- */
section[data-testid="stSidebar"] {
    text-align: center;
}
section[data-testid="stSidebar"] .stSelectbox, 
section[data-testid="stSidebar"] .stSlider {
    text-align: center;
}

/* ---------- عنوان برند در سایدبار ---------- */
.app-title {
    font-family: 'Estedad', 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px;
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
    f'<p class="app-title" style="font-size:24px;margin:0;color:#E4E7EB;">پالس‌نرخ</p></div>',
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

st.sidebar.markdown('<p class="sidebar-label">مدل</p>', unsafe_allow_html=True)
models = pd.read_sql(
    f"SELECT DISTINCT title FROM ads WHERE brand = ? AND {exclude_clause} ORDER BY title",
    conn, params=[brand] + exclude_params
)
model = st.sidebar.selectbox("مدل", models["title"].dropna().tolist(), label_visibility="collapsed")

# ---------- لودینگ کل صفحه هنگام محاسبه ----------
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
df_car = pd.read_sql(
    """
    SELECT substr(modified_date, 1, 10) AS day, price
    FROM ads
    WHERE brand = ? AND title = ? AND price > 0
    """,
    conn, params=[brand, model]
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
# بازار طلا بعضی روزها (تعطیلات) بسته است و برای آن روزها قیمتی ثبت نشده.
# به‌جای inner join (که باعث حذف کامل آن روزها از نمودار می‌شد)، قیمت طلا را
# روی همون محور روزهای خودرو/دلار left join می‌کنیم و برای روزهای تعطیل،
# آخرین قیمت شناخته‌شده را carry-forward می‌کنیم (رفتار استاندارد بازارهای مالی).
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
    st.warning("داده کافی برای این مدل وجود ندارد.")
    st.stop()

total_span_days = max((df["day"].max() - df["day"].min()).days, 1)
min_slider_days = min(2, total_span_days)

st.sidebar.markdown('<p class="sidebar-label" style="margin-top:16px;">بازه نمایش (روز اخیر)</p>', unsafe_allow_html=True)
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
        return "signal-buy", "check", "#34C77B", f"فرصت خرید احتمالی — خودرو نسبت به {vs_label} عقب مانده"
    elif value <= -10:
        return "signal-sell", "warning", "#E24B4A", f"خودرو نسبت به {vs_label} جلو زده — نسبتاً گران است"
    else:
        return "signal-flat", "minus", "#7C8494", f"رشد خودرو و {vs_label} تقریباً هم‌راستا بوده"


signal_cls, signal_icon, signal_color, signal_text = get_signal(buy_value_pct, "دلار")
if has_gold:
    gold_signal_cls, gold_signal_icon, gold_signal_color, gold_signal_text = get_signal(buy_value_gold_pct, "طلا")

# چون آماده‌ایم که محتوای واقعی رو نشون بدیم، لودر رو خالی می‌کنیم
loader_placeholder.empty()

st.title(f"مقایسه رشد  {model} با دلار و طلا")
st.caption(f"بازه‌ی نمایش: {days_to_show} روز اخیر  •  از {df['day_jalali'].iloc[0]} تا {df['day_jalali'].iloc[-1]}")

if has_gold:
    c1, c2, c3, c4, c5 = st.columns(5)
else:
    c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(metric_card("رشد قیمت خودرو", f"{car_growth:.1f}%", "car", "#4C8DFF"), unsafe_allow_html=True)
with c2:
    st.markdown(metric_card("رشد دلار", f"{tether_growth:.1f}%", "dollar", "#34C77B"), unsafe_allow_html=True)
with c3:
    st.markdown(metric_card("ارزش خرید نسبت به دلار", f"{buy_value_pct:+.1f}%", "target", "#34C77B", highlight=True), unsafe_allow_html=True)
if has_gold:
    with c4:
        st.markdown(metric_card("رشد طلا (۱۸ عیار)", f"{gold_growth:.1f}%", "coin", "#D4AF37"), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card("ارزش خرید نسبت به طلا", f"{buy_value_gold_pct:+.1f}%", "target", "#C9A227", highlight=True), unsafe_allow_html=True)

st.markdown(
    f'<div class="signal-box {signal_cls}">{icon(signal_icon, signal_color, 15)}<span>{signal_text}</span></div>',
    unsafe_allow_html=True
)
if has_gold:
    st.markdown(
        f'<div class="signal-box {gold_signal_cls}">{icon(gold_signal_icon, gold_signal_color, 15)}<span>{gold_signal_text}</span></div>',
        unsafe_allow_html=True
    )

# ---------- نمودار با افکت رسم (مثل مداد) ----------
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

draw_script = """
<style>
  html, body { margin: 0; padding: 0; }
  #growth_chart_div { opacity: 0; width: 100% !important; }
  #growth_chart_div .plot-container { width: 100% !important; }
</style>
<script>
setTimeout(function() {
    var gd = document.getElementById('growth_chart_div');
    if (!gd) return;
    var paths = gd.querySelectorAll('.scatterlayer .js-line');
    paths.forEach(function(path, i) {
        var length = path.getTotalLength();
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;
        path.style.transition = 'none';
        path.getBoundingClientRect();
        path.style.transition = 'stroke-dashoffset 1.2s ease-in-out';
        path.style.transitionDelay = (i * 0.15) + 's';
        path.style.strokeDashoffset = '0';
    });
    gd.style.transition = 'opacity 0.15s ease';
    gd.style.opacity = '1';
}, 120);
</script>
"""
components.html(chart_html + draw_script, height=520)

# ---------- تحلیل هوشمند با AI (سایدبار) ----------
st.sidebar.markdown("---")
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
            data_summary = f"""
برند و مدل: {brand} {model}
بازه زمانی: {days_to_show} روز اخیر
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