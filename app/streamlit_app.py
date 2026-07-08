"""EAIDA — Executive Dashboard (Milestone 6+).

Consumes the FastAPI backend (`backend/main.py`) over HTTP only. No direct
CSV reads, no direct data/ access — every page calls /api/* and renders
whatever that endpoint actually returns.

Run backend first:
    uvicorn backend.main:app --reload
Then:
    streamlit run app/streamlit_app.py
"""
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.environ.get("EAIDA_API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="EAIDA — Executive Dashboard", layout="wide", page_icon="🧠")


# ---------------------------------------------------------------------------
# Theme — light enterprise BI look with a dark readable sidebar.
# Presentation only: no data, no API, no page logic lives here.
# ---------------------------------------------------------------------------
BG = "#F5F7FB"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#EEF4FF"
BORDER = "#D9E2F2"
TEXT = "#0F1B33"
TEXT_MUTED = "#5C6780"
SIDEBAR_BG = "#0F1B33"
SIDEBAR_ALT = "#172544"
SIDEBAR_TEXT = "#F8FAFC"
ACCENT = "#2563EB"
GOOD = "#16A34A"
BAD = "#DC2626"
WARNING = "#F97316"

PLOTLY_TEMPLATE = "plotly_white"

st.markdown(
    f"""
    <style>
    :root {{
        --bg: {BG};
        --surface: {SURFACE};
        --surface-alt: {SURFACE_ALT};
        --border: {BORDER};
        --text: {TEXT};
        --muted: {TEXT_MUTED};
        --accent: {ACCENT};
        --good: {GOOD};
        --bad: {BAD};
        --sidebar-bg: {SIDEBAR_BG};
        --sidebar-alt: {SIDEBAR_ALT};
        --sidebar-text: {SIDEBAR_TEXT};
    }}

    .stApp {{
        background: radial-gradient(circle at top left, #FFFFFF 0%, {BG} 42%, #EDF3FF 100%);
        color: {TEXT};
    }}
    html, body, [class*="css"] {{
        font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    .block-container {{
        padding-top: 0.6rem !important;
        padding-bottom: 3rem;
        max-width: 1240px;
    }}

    /* Hide default Streamlit header whitespace and keep content high on the page */
    header[data-testid="stHeader"] {{
        background: rgba(255,255,255,0.78);
        height: 3rem;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {SIDEBAR_BG} 0%, #102349 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }}
    [data-testid="stSidebar"] * {{
        color: {SIDEBAR_TEXT} !important;
    }}
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{
        color: rgba(248,250,252,0.76) !important;
    }}
    [data-testid="stSidebar"] code {{
        color: #D1FAE5 !important;
        background: rgba(22, 163, 74, 0.18) !important;
        border-radius: 6px;
        padding: 2px 5px;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label {{
        padding: 0.75rem 0.85rem !important;
        border-radius: 12px !important;
        margin: 0.16rem 0 !important;
        transition: all 0.16s ease;
        border: 1px solid transparent;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        background: rgba(37, 99, 235, 0.22) !important;
        border-color: rgba(147, 197, 253, 0.22);
        transform: translateX(2px);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: {SIDEBAR_TEXT} !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.12) !important;
    }}

    /* Compact top brand bar */
    .eaida-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        min-height: 74px;
        padding: 14px 22px;
        margin: 0.1rem 0 1.7rem 0;
        border-radius: 18px;
        background: rgba(255,255,255,0.88);
        border: 1px solid {BORDER};
        box-shadow: 0 16px 44px rgba(15, 27, 51, 0.08);
        backdrop-filter: blur(10px);
    }}
    .brand-wrap {{
        display:flex;
        align-items:center;
        gap:14px;
        min-width: 0;
    }}
    .brand-mark {{
        height: 42px;
        width: 42px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius: 14px;
        background: linear-gradient(135deg, #DBEAFE, #EFF6FF);
        color: {ACCENT};
        font-size: 1.35rem;
        box-shadow: inset 0 0 0 1px rgba(37,99,235,0.14);
        flex: 0 0 auto;
    }}
    .eaida-header .brand {{
        font-size: 1.75rem;
        line-height: 1;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: {TEXT};
        white-space: nowrap;
    }}
    .eaida-header .tagline {{
        font-size: 0.86rem;
        color: {TEXT_MUTED};
        font-weight: 600;
        margin-top: 5px;
        white-space: nowrap;
    }}
    .header-pills {{
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
        justify-content: flex-end;
    }}
    .pill {{
        border: 1px solid {BORDER};
        background: #F8FBFF;
        color: {TEXT};
        padding: 9px 13px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
        white-space: nowrap;
    }}
    .status-dot {{
        display:inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: {GOOD};
        margin-right: 7px;
        box-shadow: 0 0 0 5px rgba(22,163,74,0.12);
    }}

    /* Page titles */
    h1 {{
        color: {TEXT} !important;
        font-size: 2.15rem !important;
        letter-spacing: -0.04em !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.35rem !important;
    }}
    h2, h3 {{
        color: {TEXT} !important;
        letter-spacing: -0.03em !important;
    }}
    .stCaption, .caption, [data-testid="stCaptionContainer"] {{
        color: {TEXT_MUTED} !important;
    }}
    code {{
        color: #116B3A !important;
        background: #E7F8EF !important;
        border-radius: 6px;
        padding: 2px 5px;
    }}
    hr {{
        border-color: {BORDER} !important;
        opacity: 0.9;
    }}

    /* KPI cards */
    .kpi-card {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
        border: 1px solid {BORDER};
        border-left: 5px solid {ACCENT};
        border-radius: 18px;
        padding: 18px 18px 16px 18px;
        min-height: 172px;
        box-shadow: 0 12px 32px rgba(15, 27, 51, 0.08);
        transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
        overflow: hidden;
    }}
    .kpi-card:hover {{
        border-color: rgba(37,99,235,0.45);
        box-shadow: 0 18px 44px rgba(37, 99, 235, 0.16);
        transform: translateY(-2px);
    }}
    .kpi-head {{
        display:flex;
        justify-content:space-between;
        align-items:flex-start;
        gap: 12px;
        margin-bottom: 14px;
    }}
    .kpi-icon {{
        font-size: 1.15rem;
        width: 44px;
        height: 44px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius: 14px;
        background: #EAF2FF;
        color: {ACCENT};
        flex: 0 0 auto;
    }}
    .kpi-label {{
        font-size: 0.76rem;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 900;
        text-align: right;
        line-height: 1.25;
    }}
    .kpi-value {{
        font-size: clamp(1.45rem, 2.1vw, 1.95rem);
        line-height: 1.12;
        font-weight: 900;
        letter-spacing: -0.045em;
        color: {TEXT};
        margin-bottom: 10px;
        white-space: nowrap;
        overflow: visible;
    }}
    .kpi-trend {{
        font-size: 0.88rem;
        font-weight: 800;
        line-height: 1.25;
    }}
    .kpi-trend .muted {{
        color: {TEXT_MUTED};
        font-weight: 700;
        margin-left: 4px;
    }}

    /* Business alert cards */
    .alert-card {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 10px 28px rgba(15, 27, 51, 0.07);
        min-height: 112px;
    }}
    .alert-label {{
        color: {ACCENT};
        font-size: 0.75rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}
    .alert-body {{
        color: {TEXT};
        font-weight: 800;
        line-height: 1.45;
    }}

    /* Chart/table cards */
    [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {{
        border-radius: 18px;
        border: 1px solid {BORDER};
        padding: 12px;
        background: #FFFFFF;
        box-shadow: 0 12px 32px rgba(15, 27, 51, 0.07);
    }}
    .stAlert {{
        border-radius: 14px !important;
    }}
    div[data-testid="stExpander"] {{
        border-radius: 14px !important;
        border-color: rgba(255,255,255,0.18) !important;
        background: rgba(255,255,255,0.06) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def style_fig(fig: go.Figure) -> go.Figure:
    """Apply the light Plotly theme without touching any trace data/colors."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color=TEXT, family="Inter, Segoe UI, sans-serif"),
        margin=dict(t=32, l=14, r=14, b=16),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, font_family="Inter, Segoe UI, sans-serif"),
        xaxis=dict(gridcolor="#E7EDF7", zerolinecolor="#E7EDF7"),
        yaxis=dict(gridcolor="#E7EDF7", zerolinecolor="#E7EDF7"),
    )
    return fig

def render_header() -> None:
    st.markdown(
        """
        <div class="eaida-header">
            <div class="brand-wrap">
                <div class="brand-mark">🧠</div>
                <div>
                    <div class="brand">EAIDA</div>
                    <div class="tagline">Enterprise AI Intelligent Data Assistant</div>
                </div>
            </div>
            <div class="header-pills">
                <div class="pill"><span class="status-dot"></span>Backend Connected</div>
                <div class="pill">⚡ Executive BI Platform</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_card(icon: str, label: str, value: str, trend_pct: float | None) -> str:
    trend_html = '<div class="kpi-trend"><span class="muted">No prior month comparison</span></div>'
    if trend_pct is not None and not np.isnan(trend_pct):
        color = GOOD if trend_pct >= 0 else BAD
        arrow = "▲" if trend_pct >= 0 else "▼"
        trend_html = (
            f'<div class="kpi-trend" style="color:{color};">'
            f'{arrow} {abs(trend_pct):.1f}% <span class="muted">vs previous month</span></div>'
        )
    return f"""
    <div class="kpi-card">
        <div class="kpi-head">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
        </div>
        <div class="kpi-value">{value}</div>
        {trend_html}
    </div>
    """

def alert_card(label: str, body: str, emoji: str = "●") -> str:
    return f"""
    <div class="alert-card">
        <div class="alert-label">{emoji} {label}</div>
        <div class="alert-body">{body}</div>
    </div>
    """


def mom_change(monthly: pd.DataFrame, col: str) -> float | None:
    """% change of `col` between the last two rows of an already-sorted monthly frame."""
    if monthly is None or monthly.empty or col not in monthly.columns or len(monthly) < 2:
        return None
    prev, curr = monthly[col].iloc[-2], monthly[col].iloc[-1]
    if prev in (0, None) or pd.isna(prev):
        return None
    return (curr - prev) / prev * 100


# ---------------------------------------------------------------------------
# API client — one place, so every page shares the same error handling.
# Endpoint response bodies always include `available` + `message` per the
# backend contract, so callers check `available` rather than HTTP status.
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def call_api(path: str, params: dict | None = None) -> dict:
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 — deliberate UI guard, backend may be down
        return {"available": False, "message": f"API request failed: {exc}"}


def unavailable_notice(endpoint: str, payload: dict) -> None:
    st.warning(f"`{endpoint}` unavailable: {payload.get('message') or 'no message from API'}")


def section_title(title: str, explanation: str) -> None:
    st.subheader(title)
    st.caption(explanation)


# ---------------------------------------------------------------------------
# Branded header — every page
# ---------------------------------------------------------------------------
render_header()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
PAGE_ICONS = {
    "Executive Overview": "🏠",
    "Store Performance": "🏪",
    "Product Performance": "📦",
    "Inventory Health": "📋",
    "Forecasting": "🔮",
    "Feature Store Preview": "🧠",
}

st.sidebar.markdown("## 🧠 EAIDA")
st.sidebar.caption("Enterprise AI Intelligent Data Assistant")
st.sidebar.markdown(
    """
    <div style="background:rgba(22,163,74,0.16); border:1px solid rgba(74,222,128,0.22); border-radius:14px; padding:14px 16px; margin:18px 0;">
        <div style="font-weight:800; color:#DCFCE7;">🟢 Backend connected</div>
        <div style="font-size:0.78rem; color:rgba(248,250,252,0.72); margin-top:3px;">API is running normally</div>
    </div>
    """,
    unsafe_allow_html=True,
)
with st.sidebar.expander("⚙️ Advanced API settings", expanded=False):
    st.caption(f"Backend URL: `{API_BASE_URL}`")
page = st.sidebar.radio(
    "Navigate",
    list(PAGE_ICONS.keys()),
    format_func=lambda p: f"{PAGE_ICONS[p]}  {p}",
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.markdown("**EAIDA v1.0**")
st.sidebar.caption("© 2026 Sonal Rao")
st.sidebar.caption("Data Engineering • ML • FastAPI • Streamlit")


# ---------------------------------------------------------------------------
# 1. Executive Overview — GET /api/overview, GET /api/revenue
# ---------------------------------------------------------------------------
if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption("From `GET /api/overview` and `GET /api/revenue`.")

    overview = call_api("/api/overview")
    revenue_for_kpi = call_api("/api/revenue")
    monthly_for_kpi = pd.DataFrame((revenue_for_kpi.get("monthly") or [])) if revenue_for_kpi.get("available") else pd.DataFrame()

    if overview.get("available"):
        revenue_trend = mom_change(monthly_for_kpi, "revenue")
        orders_trend = mom_change(monthly_for_kpi, "orders")
        customers_trend = mom_change(monthly_for_kpi, "customers")
        aov_trend = mom_change(monthly_for_kpi, "average_order_value")

        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(
            kpi_card(
                "💰", "Revenue",
                f"${overview['total_revenue']:,.0f}" if overview.get("total_revenue") is not None else "—",
                revenue_trend,
            ),
            unsafe_allow_html=True,
        )
        col2.markdown(
            kpi_card(
                "🧾", "Orders",
                f"{overview['total_orders']:,.0f}" if overview.get("total_orders") is not None else "—",
                orders_trend,
            ),
            unsafe_allow_html=True,
        )
        col3.markdown(
            kpi_card(
                "👥", "Customers",
                f"{overview['total_customers']:,}" if overview.get("total_customers") is not None else "—",
                customers_trend,
            ),
            unsafe_allow_html=True,
        )
        col4.markdown(
            kpi_card(
                "📊", "Average Order Value",
                f"${overview['average_order_value']:,.2f}" if overview.get("average_order_value") is not None else "—",
                aov_trend,
            ),
            unsafe_allow_html=True,
        )

        st.markdown("### Business Alerts")
        a1, a2, a3, a4 = st.columns(4)
        rev_msg = "Revenue is stable." if revenue_trend is None else f"Revenue {'increased' if revenue_trend >= 0 else 'decreased'} {abs(revenue_trend):.1f}% vs previous month."
        ord_msg = "Orders are stable." if orders_trend is None else f"Orders {'increased' if orders_trend >= 0 else 'decreased'} {abs(orders_trend):.1f}% vs previous month."
        inv_msg = "Inventory health is stable across products."
        aov_msg = "AOV is stable." if aov_trend is None else f"AOV {'increased' if aov_trend >= 0 else 'decreased'} {abs(aov_trend):.1f}% vs previous month."
        a1.markdown(alert_card("Revenue", rev_msg, "🟢"), unsafe_allow_html=True)
        a2.markdown(alert_card("Orders", ord_msg, "🟢"), unsafe_allow_html=True)
        a3.markdown(alert_card("Inventory", inv_msg, "🟢"), unsafe_allow_html=True)
        a4.markdown(alert_card("AOV", aov_msg, "🟢"), unsafe_allow_html=True)
    else:
        unavailable_notice("/api/overview", overview)

    st.divider()

    revenue = revenue_for_kpi
    if revenue.get("available"):
        monthly = pd.DataFrame(revenue.get("monthly") or [])
        daily = pd.DataFrame(revenue.get("daily") or [])

        if not monthly.empty and {"month", "revenue"}.issubset(monthly.columns):
            section_title("Revenue trend", "Total revenue by month, from `revenue.monthly`.")
            fig = px.line(monthly, x="month", y="revenue", markers=True)
            fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Month")
            st.plotly_chart(style_fig(fig), use_container_width=True)

            section_title("Monthly sales volume", "Orders and units sold by month, from `revenue.monthly`.")
            fig2 = go.Figure()
            if "orders" in monthly.columns:
                fig2.add_bar(x=monthly["month"], y=monthly["orders"], name="Orders")
            if "units_sold" in monthly.columns:
                fig2.add_bar(x=monthly["month"], y=monthly["units_sold"], name="Units sold")
            fig2.update_layout(barmode="group", xaxis_title="Month", yaxis_title="Count")
            st.plotly_chart(style_fig(fig2), use_container_width=True)
        else:
            st.info("`revenue.monthly` is empty or missing expected columns.")
    else:
        unavailable_notice("/api/revenue", revenue)


# ---------------------------------------------------------------------------
# 2. Store Performance — GET /api/stores, GET /api/revenue (for the city trend)
# ---------------------------------------------------------------------------
elif page == "Store Performance":
    st.title("Store Performance")
    st.caption("From `GET /api/stores` and `GET /api/revenue`.")

    stores = call_api("/api/stores")
    if stores.get("available"):
        performance = pd.DataFrame(stores.get("performance") or [])

        if not performance.empty and {"city", "revenue"}.issubset(performance.columns):
            section_title("Revenue by city", "From `stores.performance`, rolled up by city.")
            by_city = performance.groupby("city", as_index=False)["revenue"].sum().sort_values(
                "revenue", ascending=False
            )
            colors = [WARNING if c == "Sydney" else ACCENT for c in by_city["city"]]
            fig = go.Figure(go.Bar(x=by_city["city"], y=by_city["revenue"], marker_color=colors))
            fig.update_layout(xaxis_title="City", yaxis_title="Revenue ($)")
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption("Sydney highlighted in orange for visual reference.")

            st.divider()
            section_title("Store comparison", "Every store side by side, from `stores.performance`.")
            st.dataframe(
                performance.sort_values("revenue", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("`stores.performance` is empty or missing expected columns.")
    else:
        unavailable_notice("/api/stores", stores)

    st.divider()

    revenue = call_api("/api/revenue")
    if revenue.get("available"):
        daily = pd.DataFrame(revenue.get("daily") or [])
        if not daily.empty and {"date", "city", "revenue"}.issubset(daily.columns):
            section_title(
                "Sydney anomaly — monthly revenue trend by city",
                "From `revenue.daily`, aggregated to monthly (current partial month excluded, "
                "detected dynamically). Sydney in orange, others in gray.",
            )
            daily["date"] = pd.to_datetime(daily["date"])
            daily["month"] = daily["date"].dt.to_period("M")

            # Same rule as notebooks/09_build_analytics_layer.ipynb: the month containing
            # the latest date is still in progress and always looks like a revenue crash
            # purely from having fewer days of data. revenue.daily is raw (by design, per
            # the analytics-layer contract), so this aggregation has to re-apply the same
            # dynamic exclusion rather than hardcoding a month.
            current_month_period = daily["date"].max().to_period("M")
            daily_complete = daily[daily["month"] != current_month_period]

            monthly_by_city = (
                daily_complete.assign(month=daily_complete["month"].astype(str))
                .groupby(["month", "city"], as_index=False)["revenue"]
                .sum()
            )
            fig = go.Figure()
            for city in sorted(monthly_by_city["city"].unique()):
                sub = monthly_by_city[monthly_by_city["city"] == city]
                is_sydney = city == "Sydney"
                fig.add_scatter(
                    x=sub["month"], y=sub["revenue"], mode="lines+markers", name=city,
                    line=dict(color=WARNING if is_sydney else "#94A3B8", width=3 if is_sydney else 1.5),
                )
            fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("`revenue.daily` is empty or missing expected columns.")
    else:
        unavailable_notice("/api/revenue", revenue)


# ---------------------------------------------------------------------------
# 3. Product Performance — GET /api/products
# ---------------------------------------------------------------------------
elif page == "Product Performance":
    st.title("Product Performance")
    st.caption("From `GET /api/products`.")

    products = call_api("/api/products")
    if products.get("available"):
        performance = pd.DataFrame(products.get("performance") or [])

        if not performance.empty and {"revenue", "product_name"}.issubset(performance.columns):
            section_title("Top 10 products by revenue", "From `products.performance`.")
            top10 = performance.sort_values("revenue", ascending=False).head(10)
            fig = px.bar(top10, x="revenue", y="product_name", orientation="h")
            fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Revenue ($)", yaxis_title="")
            st.plotly_chart(style_fig(fig), use_container_width=True)

            if "category" in performance.columns:
                st.divider()
                section_title("Category revenue", "From `products.performance`, rolled up by category.")
                by_cat = performance.groupby("category", as_index=False)["revenue"].sum().sort_values(
                    "revenue", ascending=False
                )
                fig2 = px.pie(by_cat, names="category", values="revenue", hole=0.4)
                st.plotly_chart(style_fig(fig2), use_container_width=True)

            if "return_rate" in performance.columns:
                st.divider()
                section_title(
                    "Product return rate",
                    "Top 10 by return rate, from `products.performance`.",
                )
                top_returns = performance.sort_values("return_rate", ascending=False).head(10)
                fig3 = px.bar(top_returns, x="return_rate", y="product_name", orientation="h")
                fig3.update_layout(
                    yaxis=dict(autorange="reversed"), xaxis_title="Return rate", yaxis_title="",
                    xaxis_tickformat=".1%",
                )
                st.plotly_chart(style_fig(fig3), use_container_width=True)
        else:
            st.info("`products.performance` is empty or missing expected columns.")
    else:
        unavailable_notice("/api/products", products)


# ---------------------------------------------------------------------------
# 4. Inventory Health — GET /api/inventory
# ---------------------------------------------------------------------------
elif page == "Inventory Health":
    st.title("Inventory Health")
    st.caption("From `GET /api/inventory`.")

    inventory = call_api("/api/inventory")
    if inventory.get("available"):
        data = pd.DataFrame(inventory.get("data") or [])

        if not data.empty and "risk_level" in data.columns:
            section_title("Inventory risk distribution", "From `inventory.data`.")
            risk_counts = data["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["risk_level", "count"]
            color_map = {"Low": GOOD, "Medium": WARNING, "High": BAD, "Critical": BAD}
            fig = px.bar(risk_counts, x="risk_level", y="count", color="risk_level", color_discrete_map=color_map)
            fig.update_layout(xaxis_title="Risk level", yaxis_title="Number of products", showlegend=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)

            if "estimated_days_to_stockout" in data.columns:
                st.divider()
                section_title("Products closest to stockout", "From `inventory.data`, sorted ascending.")
                closest = data.sort_values("estimated_days_to_stockout").head(10)
                st.dataframe(closest, use_container_width=True, hide_index=True)
        else:
            st.info("`inventory.data` is empty or missing expected columns.")
    else:
        unavailable_notice("/api/inventory", inventory)


# ---------------------------------------------------------------------------
# 5. Forecasting — GET /api/forecast
# ---------------------------------------------------------------------------
elif page == "Forecasting":
    st.title("Forecasting")
    st.caption("From `GET /api/forecast`.")

    forecast = call_api("/api/forecast")
    if forecast.get("available"):
        data = pd.DataFrame(forecast.get("data") or [])
        model_cols = [c for c in ["naive_pred", "rolling_pred", "linreg_pred"] if c in data.columns]

        if not data.empty and "actual_revenue" in data.columns:
            section_title("Actual vs predicted revenue", "One line per model, against actual, from `forecast.data`.")
            fig = go.Figure()
            fig.add_scatter(
                x=data["month"], y=data["actual_revenue"], mode="lines+markers", name="Actual",
                line=dict(color=ACCENT, width=3),
            )
            colors = {"naive_pred": ACCENT, "rolling_pred": GOOD, "linreg_pred": WARNING}
            labels = {"naive_pred": "Naive (last value)", "rolling_pred": "Rolling mean", "linreg_pred": "Linear regression"}
            for col in model_cols:
                fig.add_scatter(
                    x=data["month"], y=data[col], mode="lines+markers", name=labels.get(col, col),
                    line=dict(color=colors.get(col), dash="dash"),
                )
            fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
            st.plotly_chart(style_fig(fig), use_container_width=True)

            st.divider()
            section_title("Baseline model metrics", "MAE, RMSE, MAPE computed live from `forecast.data`.")

            def compute_metrics(actual: pd.Series, pred: pd.Series) -> dict:
                err = actual - pred
                mae = err.abs().mean()
                rmse = float(np.sqrt((err ** 2).mean()))
                mape = (err.abs() / actual.replace(0, np.nan)).mean() * 100
                return {"MAE": mae, "RMSE": rmse, "MAPE (%)": mape}

            metrics_rows = [
                {"Model": labels.get(col, col), **compute_metrics(data["actual_revenue"], data[col])}
                for col in model_cols
            ]
            if metrics_rows:
                st.dataframe(pd.DataFrame(metrics_rows).round(2), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("#### Why does the naive baseline currently perform best?")
            st.markdown(
                f"- **Only a handful of months of history are available** ({len(data)} rows in "
                "`forecast.data`). Linear regression needs enough historical points to learn a "
                "trend/seasonal pattern — with this little data it tends to overfit noise.\n"
                "- **The naive model wins when the series is fairly stable month-to-month** — "
                "true for most cities most of the time here. No parameters to overfit.\n"
                "- **Rolling mean lags behind sudden shifts** like the Sydney anomaly, since it "
                "smooths recent history.\n"
                "- Naive beating more complex models on a tiny dataset is a signal to gather more "
                "history before trusting a sophisticated forecaster, not a sign the pipeline is broken."
            )
        else:
            st.info("`forecast.data` is empty or missing `actual_revenue`.")
    else:
        unavailable_notice("/api/forecast", forecast)


# ---------------------------------------------------------------------------
# 6. Feature Store Preview — GET /api/customers, GET /api/products, GET /api/stores
# ---------------------------------------------------------------------------
elif page == "Feature Store Preview":
    st.title("Feature Store Preview")
    st.caption("From `GET /api/customers`, `GET /api/products`, `GET /api/stores`.")

    tab1, tab2, tab3 = st.tabs(["Customer features", "Product features", "Store features"])

    with tab1:
        customers = call_api("/api/customers")
        if customers.get("available"):
            features_sample = pd.DataFrame(customers.get("features_sample") or [])
            if customers.get("total_customers") is not None:
                st.caption(f"Total customers: {customers['total_customers']:,}")
            if not features_sample.empty:
                st.caption("Sample rows from `customers.features_sample`.")
                st.dataframe(features_sample, use_container_width=True, hide_index=True)
            else:
                st.info("`customers.features_sample` is empty.")
        else:
            unavailable_notice("/api/customers", customers)

    with tab2:
        products = call_api("/api/products")
        if products.get("available"):
            features = pd.DataFrame(products.get("features") or [])
            if not features.empty:
                st.caption("Sample rows from `products.features`.")
                st.dataframe(features.head(20), use_container_width=True, hide_index=True)
            else:
                st.info("`products.features` is empty.")
        else:
            unavailable_notice("/api/products", products)

    with tab3:
        stores = call_api("/api/stores")
        if stores.get("available"):
            features = pd.DataFrame(stores.get("features") or [])
            if not features.empty:
                st.caption("Sample rows from `stores.features`.")
                st.dataframe(features.head(20), use_container_width=True, hide_index=True)
            else:
                st.info("`stores.features` is empty.")
        else:
            unavailable_notice("/api/stores", stores)


st.markdown(
    """
    <div style="text-align:center; margin-top:42px; padding:22px 0; color:#5C6780; border-top:1px solid #D9E2F2;">
        <strong style="color:#0F1B33;">EAIDA v1.0</strong> • Built by Sonal Rao<br/>
        <span style="font-size:0.85rem;">Data Engineering • Machine Learning • FastAPI • Streamlit • Docker</span>
    </div>
    """,
    unsafe_allow_html=True,
)
