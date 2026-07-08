"""EAIDA — Executive Dashboard (Milestone 5).

Reads pre-computed CSVs from data/analytics, data/features, and
data/predictions only. This app does NOT touch data/raw, does not run any
ETL, and does not talk to Postgres — it is a pure presentation layer over
work already done in earlier milestones (Day 3-4 SQL analysis, the feature
store, and the Day 5 forecasting baseline).

Run with:
    streamlit run app/streamlit_app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Paths — resolved relative to this file, so it works regardless of the
# directory the user happens to run `streamlit run` from.
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ANALYTICS_DIR = BASE_DIR / "data" / "analytics"
FEATURES_DIR = BASE_DIR / "data" / "features"
PREDICTIONS_DIR = BASE_DIR / "data" / "predictions"

st.set_page_config(page_title="EAIDA — Executive Dashboard", layout="wide")


# ---------------------------------------------------------------------------
# Loading — every file is optional from the app's point of view. A missing
# or unreadable file degrades that section gracefully instead of crashing
# the whole dashboard, since different milestones populate these folders
# at different times.
# ---------------------------------------------------------------------------
@st.cache_data
def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 — deliberately broad, this is a UI guard
        st.warning(f"Could not read `{path.name}`: {exc}")
        return None


def missing_file_notice(name: str, expected_path: Path) -> None:
    st.warning(
        f"**{name}** not found at `{expected_path.relative_to(BASE_DIR)}`. "
        "This section will populate once that milestone's pipeline has been run."
    )


def section_title(title: str, explanation: str) -> None:
    st.subheader(title)
    st.caption(explanation)


def get_partial_month(daily_df: pd.DataFrame | None) -> str | None:
    """Return the 'YYYY-MM' string of the trailing month if it's a partial
    month (data generation stops "today", so the current calendar month
    never has a full set of days) — otherwise None.

    Derived from daily_sales.csv rather than hardcoded, so this keeps
    working correctly if the dataset is regenerated on a different date.
    """
    if daily_df is None or daily_df.empty:
        return None
    dates = pd.to_datetime(daily_df["date"])
    max_date = dates.max()
    period = max_date.to_period("M")
    if max_date.day < period.days_in_month:
        return str(period)
    return None


def exclude_partial_month(df: pd.DataFrame, month_col: str, partial_month: str | None) -> pd.DataFrame:
    if partial_month is None:
        return df
    return df[df[month_col].astype(str) != partial_month]


# ---------------------------------------------------------------------------
# Data loads — one place, so every page shares the same cached frames.
# ---------------------------------------------------------------------------
monthly_sales = load_csv(ANALYTICS_DIR / "monthly_sales.csv")
daily_sales = load_csv(ANALYTICS_DIR / "daily_sales.csv")
customer_summary = load_csv(ANALYTICS_DIR / "customer_summary.csv")
store_performance = load_csv(ANALYTICS_DIR / "store_performance.csv")
product_performance = load_csv(ANALYTICS_DIR / "product_performance.csv")
returns_summary = load_csv(ANALYTICS_DIR / "returns_summary.csv")
inventory_health = load_csv(ANALYTICS_DIR / "inventory_health.csv")

customer_features = load_csv(FEATURES_DIR / "customer_features.csv")
product_features = load_csv(FEATURES_DIR / "product_features.csv")
store_features = load_csv(FEATURES_DIR / "store_features.csv")

sales_forecast = load_csv(PREDICTIONS_DIR / "sales_forecast_baseline.csv")

# Trailing partial month (e.g. the current calendar month, if data generation
# stopped mid-month) — computed once here and reused by every trend chart.
PARTIAL_MONTH = get_partial_month(daily_sales)


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("EAIDA")
st.sidebar.caption("Enterprise AI Intelligent Data Assistant")
page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Store Performance",
        "Product Performance",
        "Inventory Health",
        "Forecasting",
        "Feature Store Preview",
    ],
)
st.sidebar.divider()
st.sidebar.caption(
    "Data sources: `data/analytics/`, `data/features/`, `data/predictions/`. "
    "This app reads pre-computed CSVs only — it does not run any pipeline."
)


# ---------------------------------------------------------------------------
# 1. Executive Overview
# ---------------------------------------------------------------------------
if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption(
        "Top-line business health across the full history in the dataset. "
        "Figures are computed from `monthly_sales.csv` and `customer_summary.csv`."
    )

    if monthly_sales is not None:
        full_months = exclude_partial_month(monthly_sales, "month", PARTIAL_MONTH)

        total_revenue = full_months["revenue"].sum()
        total_orders = full_months["orders"].sum()
        avg_order_value = total_revenue / total_orders if total_orders else float("nan")

        # Month-over-month deltas, based on the last two FULL months only —
        # comparing against a partial month would show a fake, huge "drop".
        delta_revenue = delta_orders = delta_aov = None
        if len(full_months) >= 2:
            last_row = full_months.iloc[-1]
            prev_row = full_months.iloc[-2]
            delta_revenue = (last_row["revenue"] - prev_row["revenue"]) / prev_row["revenue"] * 100
            delta_orders = (last_row["orders"] - prev_row["orders"]) / prev_row["orders"] * 100
            last_aov = last_row["revenue"] / last_row["orders"] if last_row["orders"] else np.nan
            prev_aov = prev_row["revenue"] / prev_row["orders"] if prev_row["orders"] else np.nan
            delta_aov = (last_aov - prev_aov) / prev_aov * 100 if prev_aov else None
    else:
        total_revenue = total_orders = avg_order_value = None
        delta_revenue = delta_orders = delta_aov = None

    total_customers = len(customer_summary) if customer_summary is not None else None

    col1, col2, col3, col4 = st.columns(4)
    with col1.container(border=True):
        st.metric(
            "Total revenue",
            f"${total_revenue:,.0f}" if total_revenue is not None else "—",
            delta=f"{delta_revenue:+.1f}% vs prior month" if delta_revenue is not None else None,
        )
    with col2.container(border=True):
        st.metric(
            "Total orders",
            f"{total_orders:,.0f}" if total_orders is not None else "—",
            delta=f"{delta_orders:+.1f}% vs prior month" if delta_orders is not None else None,
        )
    with col3.container(border=True):
        st.metric("Total customers", f"{total_customers:,}" if total_customers is not None else "—")
    with col4.container(border=True):
        st.metric(
            "Average order value",
            f"${avg_order_value:,.2f}" if avg_order_value is not None and not np.isnan(avg_order_value) else "—",
            delta=f"{delta_aov:+.1f}% vs prior month" if delta_aov is not None else None,
        )

    if PARTIAL_MONTH is not None:
        st.caption(
            f"KPI totals and month-over-month deltas exclude **{PARTIAL_MONTH}**, "
            "which is a partial month in the underlying data."
        )

    st.divider()

    if monthly_sales is not None:
        trend_df = exclude_partial_month(monthly_sales, "month", PARTIAL_MONTH)
        partial_note = f" (**{PARTIAL_MONTH}** excluded — partial month)" if PARTIAL_MONTH else ""

        section_title(
            "Revenue trend",
            f"Total revenue by month across all stores and cities.{partial_note}",
        )
        fig = px.line(trend_df, x="month", y="revenue", markers=True)
        fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Month")
        st.plotly_chart(fig, use_container_width=True)

        section_title(
            "Monthly sales volume",
            "Orders and units sold by month — useful for separating a revenue "
            f"drop caused by fewer orders from one caused by smaller baskets.{partial_note}",
        )
        fig2 = go.Figure()
        fig2.add_bar(x=trend_df["month"], y=trend_df["orders"], name="Orders")
        if "units_sold" in trend_df.columns:
            fig2.add_bar(x=trend_df["month"], y=trend_df["units_sold"], name="Units sold")
        fig2.update_layout(barmode="group", xaxis_title="Month", yaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        missing_file_notice("monthly_sales.csv", ANALYTICS_DIR / "monthly_sales.csv")


# ---------------------------------------------------------------------------
# 2. Store Performance
# ---------------------------------------------------------------------------
elif page == "Store Performance":
    st.title("Store Performance")
    st.caption("Revenue and health by store and city, with the Sydney anomaly called out explicitly.")

    if store_performance is not None:
        section_title("Revenue by city", "Store-level revenue rolled up to the city it belongs to.")
        by_city = store_performance.groupby("city", as_index=False)["revenue"].sum().sort_values(
            "revenue", ascending=False
        )
        colors = ["#D85A30" if c == "Sydney" else "#378ADD" for c in by_city["city"]]
        fig = go.Figure(go.Bar(x=by_city["city"], y=by_city["revenue"], marker_color=colors))
        fig.update_layout(xaxis_title="City", yaxis_title="Revenue ($)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Sydney highlighted in orange for visual reference across this page.")

        st.divider()
        section_title("Store comparison", "Every store side by side — revenue, AOV, and return rate.")
        st.dataframe(
            store_performance.sort_values("revenue", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    else:
        missing_file_notice("store_performance.csv", ANALYTICS_DIR / "store_performance.csv")

    st.divider()
    if daily_sales is not None:
        partial_note = f" **{PARTIAL_MONTH}** is excluded as a partial month." if PARTIAL_MONTH else ""
        section_title(
            "Sydney anomaly — monthly revenue trend by city",
            "Sydney drawn in orange against every other city in gray, so the drop is "
            f"visually unmistakable rather than buried in a table.{partial_note}",
        )
        daily_sales["date"] = pd.to_datetime(daily_sales["date"])
        monthly_by_city = (
            daily_sales.assign(month=daily_sales["date"].dt.to_period("M").astype(str))
            .groupby(["month", "city"], as_index=False)["revenue"]
            .sum()
        )
        monthly_by_city = exclude_partial_month(monthly_by_city, "month", PARTIAL_MONTH)
        fig = go.Figure()
        for city in sorted(monthly_by_city["city"].unique()):
            sub = monthly_by_city[monthly_by_city["city"] == city]
            is_sydney = city == "Sydney"
            fig.add_scatter(
                x=sub["month"],
                y=sub["revenue"],
                mode="lines+markers",
                name=city,
                line=dict(color="#D85A30" if is_sydney else "#B4B2A9", width=3 if is_sydney else 1.5),
            )
        fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        missing_file_notice("daily_sales.csv", ANALYTICS_DIR / "daily_sales.csv")


# ---------------------------------------------------------------------------
# 3. Product Performance
# ---------------------------------------------------------------------------
elif page == "Product Performance":
    st.title("Product Performance")

    if product_performance is not None:
        section_title("Top 10 products by revenue", "Highest-earning products across the full history.")
        top10 = product_performance.sort_values("revenue", ascending=False).head(10)
        fig = px.bar(top10, x="revenue", y="product_name", orientation="h")
        fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Revenue ($)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        section_title("Category revenue", "Revenue rolled up by product category.")
        by_cat = product_performance.groupby("category", as_index=False)["revenue"].sum().sort_values(
            "revenue", ascending=False
        )
        fig2 = px.pie(by_cat, names="category", values="revenue", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        section_title(
            "Product return rate",
            "The 10 products with the highest return rate — a quality or fit-description signal, "
            "not a revenue one.",
        )
        top_returns = product_performance.sort_values("return_rate", ascending=False).head(10)
        fig3 = px.bar(top_returns, x="return_rate", y="product_name", orientation="h")
        fig3.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Return rate",
            yaxis_title="",
            xaxis_tickformat=".1%",
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        missing_file_notice("product_performance.csv", ANALYTICS_DIR / "product_performance.csv")


# ---------------------------------------------------------------------------
# 4. Inventory Health
# ---------------------------------------------------------------------------
elif page == "Inventory Health":
    st.title("Inventory Health")

    if inventory_health is not None:
        section_title(
            "Inventory risk distribution",
            "Products bucketed by stockout risk level, based on current stock vs recent sales velocity.",
        )
        risk_counts = inventory_health["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        color_map = {"Low": "#639922", "Medium": "#BA7517", "High": "#A32D2D"}
        fig = px.bar(
            risk_counts,
            x="risk_level",
            y="count",
            color="risk_level",
            color_discrete_map=color_map,
        )
        fig.update_layout(xaxis_title="Risk level", yaxis_title="Number of products", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        section_title(
            "Products closest to stockout",
            "Sorted by estimated days remaining at current sales velocity — the products that need "
            "reordering attention soonest.",
        )
        closest = inventory_health.sort_values("estimated_days_to_stockout").head(10)
        st.dataframe(closest, use_container_width=True, hide_index=True)
    else:
        missing_file_notice("inventory_health.csv", ANALYTICS_DIR / "inventory_health.csv")


# ---------------------------------------------------------------------------
# 5. Forecasting
# ---------------------------------------------------------------------------
elif page == "Forecasting":
    st.title("Forecasting")
    st.caption(
        "Comparing three baseline forecasting approaches against actual revenue. "
        "This is intentionally simple — see the explanation below for why."
    )

    if sales_forecast is not None:
        section_title("Actual vs predicted revenue", "One line per model, against the actual outcome.")
        fig = go.Figure()
        fig.add_scatter(
            x=sales_forecast["month"], y=sales_forecast["actual_revenue"],
            mode="lines+markers", name="Actual", line=dict(color="#2C2C2A", width=3),
        )
        model_cols = [c for c in ["naive_pred", "rolling_pred", "linreg_pred"] if c in sales_forecast.columns]
        colors = {"naive_pred": "#378ADD", "rolling_pred": "#1D9E75", "linreg_pred": "#D85A30"}
        labels = {"naive_pred": "Naive (last value)", "rolling_pred": "Rolling mean", "linreg_pred": "Linear regression"}
        for col in model_cols:
            fig.add_scatter(
                x=sales_forecast["month"], y=sales_forecast[col],
                mode="lines+markers", name=labels.get(col, col),
                line=dict(color=colors.get(col), dash="dash"),
            )
        fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        section_title(
            "Baseline model metrics",
            "MAE, RMSE, and MAPE for each model against actual revenue, computed live from the predictions file.",
        )

        def compute_metrics(actual: pd.Series, pred: pd.Series) -> dict:
            err = actual - pred
            mae = err.abs().mean()
            rmse = float(np.sqrt((err ** 2).mean()))
            mape = (err.abs() / actual.replace(0, np.nan)).mean() * 100
            return {"MAE": mae, "RMSE": rmse, "MAPE (%)": mape}

        metrics_rows = []
        for col in model_cols:
            m = compute_metrics(sales_forecast["actual_revenue"], sales_forecast[col])
            metrics_rows.append({"Model": labels.get(col, col), **m})
        metrics_df = pd.DataFrame(metrics_rows).round(2)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### Why does the naive baseline currently perform best?")
        st.markdown(
            "- **Only a handful of months of history are available** in "
            f"`sales_forecast_baseline.csv` ({len(sales_forecast)} rows). Linear regression "
            "needs enough historical points to learn a trend and seasonal pattern reliably — "
            "with this little data it tends to overfit to noise and drift off actual values.\n"
            "- **The naive model (\"next month = this month\") wins when the series is fairly "
            "stable month-to-month**, which is true for most cities most of the time in this "
            "dataset. It has no parameters to overfit, so with limited data it's hard to beat.\n"
            "- **The rolling mean lags behind sudden shifts** like the Sydney anomaly, since it "
            "smooths recent history — a real level shift takes several months to fully show up "
            "in a rolling average, understating the drop right when it matters most.\n"
            "- This is expected and healthy for an MVP: a naive baseline beating more complex "
            "models on a tiny dataset is a signal to **gather more historical data before "
            "trusting a more sophisticated forecaster**, not a sign the pipeline is broken."
        )
    else:
        missing_file_notice("sales_forecast_baseline.csv", PREDICTIONS_DIR / "sales_forecast_baseline.csv")


# ---------------------------------------------------------------------------
# 6. Feature Store Preview
# ---------------------------------------------------------------------------
elif page == "Feature Store Preview":
    st.title("Feature Store Preview")
    st.caption(
        "A read-only look at the feature tables that back the ML milestones — "
        "not analytics output, but the model-ready inputs themselves."
    )

    tab1, tab2, tab3 = st.tabs(["Customer features", "Product features", "Store features"])

    with tab1:
        if customer_features is not None:
            st.caption("One row per customer: RFM-style fields (recency, frequency, monetary) plus tenure.")
            st.dataframe(customer_features.head(20), use_container_width=True, hide_index=True)
        else:
            missing_file_notice("customer_features.csv", FEATURES_DIR / "customer_features.csv")

    with tab2:
        if product_features is not None:
            st.caption("One row per product: recent sales velocity and rolling growth, alongside return rate.")
            st.dataframe(product_features.head(20), use_container_width=True, hide_index=True)
        else:
            missing_file_notice("product_features.csv", FEATURES_DIR / "product_features.csv")

    with tab3:
        if store_features is not None:
            st.caption("One row per store: revenue, growth, and return-rate fields used by the store-level models.")
            st.dataframe(store_features.head(20), use_container_width=True, hide_index=True)
        else:
            missing_file_notice("store_features.csv", FEATURES_DIR / "store_features.csv")


# ---------------------------------------------------------------------------
# Footer — shown on every page, since it's rendered after the if/elif chain.
# ---------------------------------------------------------------------------
st.divider()
st.caption("Built by Sonal Rao | Data Engineering & AI Portfolio Project")
