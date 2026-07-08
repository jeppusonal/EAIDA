"""EAIDA — Executive Dashboard (Milestone 7).

Data now comes from the FastAPI backend, not local CSVs. Every page calls
`fetch(endpoint)`, which handles connection failures, timeouts, and
unavailable datasets, and returns parsed JSON (or None on failure).

Run with (FastAPI backend must already be running):
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="EAIDA — Executive Dashboard", layout="wide")

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 5


# ---------------------------------------------------------------------------
# fetch() — the one reusable helper every page uses to talk to the backend.
# Never raises. Always returns parsed JSON on success, None on any failure,
# after showing a friendly warning explaining what went wrong.
# ---------------------------------------------------------------------------
def fetch(endpoint: str) -> dict | list | None:
    base_url = st.session_state.get("backend_url", DEFAULT_BACKEND_URL).rstrip("/")
    url = f"{base_url}{endpoint}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError:
        st.warning(
            f"Can't reach the backend at `{base_url}`. Is FastAPI running? "
            "Check the Backend URL in the sidebar."
        )
        return None
    except requests.exceptions.Timeout:
        st.warning(f"Request to `{endpoint}` timed out after {REQUEST_TIMEOUT_SECONDS}s.")
        return None
    except requests.exceptions.RequestException as exc:
        st.warning(f"Request to `{endpoint}` failed: {exc}")
        return None

    if response.status_code == 404:
        st.warning(f"`{endpoint}` not found on the backend (404). Dataset may not be available yet.")
        return None
    if response.status_code == 503:
        st.warning(f"`{endpoint}` reports the dataset is unavailable (503).")
        return None
    if not response.ok:
        st.warning(f"`{endpoint}` returned HTTP {response.status_code}.")
        return None

    try:
        return response.json()
    except ValueError:
        st.warning(f"`{endpoint}` did not return valid JSON.")
        return None


def to_df(payload: dict | list | None, key: str | None = None) -> pd.DataFrame | None:
    """Turn a fetch() payload into a DataFrame. If key is given, pull that
    field out of a dict payload first (endpoints return multiple named
    tables per call)."""
    if payload is None:
        return None
    data = payload.get(key) if key and isinstance(payload, dict) else payload
    if data is None:
        return None
    try:
        return pd.DataFrame(data)
    except Exception as exc:  # noqa: BLE001 — UI guard, same spirit as before
        st.warning(f"Could not parse `{key or ''}` response: {exc}")
        return None


def missing_data_notice(name: str) -> None:
    st.warning(f"**{name}** is not available right now. This section will populate once the backend can serve it.")


def section_title(title: str, explanation: str) -> None:
    st.subheader(title)
    st.caption(explanation)


# ---------------------------------------------------------------------------
# Sidebar navigation + backend configuration
# ---------------------------------------------------------------------------
st.sidebar.title("EAIDA")
st.sidebar.caption("Enterprise AI Data Assistant — MVP dashboard")

if "backend_url" not in st.session_state:
    st.session_state["backend_url"] = DEFAULT_BACKEND_URL

st.session_state["backend_url"] = st.sidebar.text_input(
    "Backend URL", value=st.session_state["backend_url"]
)

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
    "Data source: FastAPI backend at the URL above "
    "(`/api/overview`, `/api/revenue`, `/api/forecast`, `/api/products`, "
    "`/api/stores`, `/api/inventory`, `/api/customers`)."
)


# ---------------------------------------------------------------------------
# 1. Executive Overview
# ---------------------------------------------------------------------------
if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption(
        "Top-line business health across the full history in the dataset. "
        "Figures come from `/api/overview` (monthly sales) and `/api/customers` (customer summary)."
    )

    overview_payload = fetch("/api/overview")
    monthly_sales = to_df(overview_payload, "monthly_sales")

    customers_payload = fetch("/api/customers")
    customer_summary = to_df(customers_payload, "customer_summary")

    if monthly_sales is not None:
        total_revenue = monthly_sales["revenue"].sum()
        total_orders = monthly_sales["orders"].sum()
        avg_order_value = total_revenue / total_orders if total_orders else float("nan")
    else:
        total_revenue = total_orders = avg_order_value = None

    total_customers = len(customer_summary) if customer_summary is not None else None

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total revenue", f"${total_revenue:,.0f}" if total_revenue is not None else "—")
    col2.metric("Total orders", f"{total_orders:,.0f}" if total_orders is not None else "—")
    col3.metric("Total customers", f"{total_customers:,}" if total_customers is not None else "—")
    col4.metric(
        "Average order value",
        f"${avg_order_value:,.2f}" if avg_order_value is not None and not np.isnan(avg_order_value) else "—",
    )

    st.divider()

    if monthly_sales is not None:
        section_title(
            "Revenue trend",
            "Total revenue by month across all stores and cities.",
        )
        fig = px.line(monthly_sales, x="month", y="revenue", markers=True)
        fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Month")
        st.plotly_chart(fig, use_container_width=True)

        section_title(
            "Monthly sales volume",
            "Orders and units sold by month — useful for separating a revenue "
            "drop caused by fewer orders from one caused by smaller baskets.",
        )
        fig2 = go.Figure()
        fig2.add_bar(x=monthly_sales["month"], y=monthly_sales["orders"], name="Orders")
        if "units_sold" in monthly_sales.columns:
            fig2.add_bar(x=monthly_sales["month"], y=monthly_sales["units_sold"], name="Units sold")
        fig2.update_layout(barmode="group", xaxis_title="Month", yaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        missing_data_notice("Monthly sales")


# ---------------------------------------------------------------------------
# 2. Store Performance
# ---------------------------------------------------------------------------
elif page == "Store Performance":
    st.title("Store Performance")
    st.caption("Revenue and health by store and city, with the Sydney anomaly called out explicitly.")

    stores_payload = fetch("/api/stores")
    store_performance = to_df(stores_payload, "store_performance")

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
        missing_data_notice("Store performance")

    st.divider()
    revenue_payload = fetch("/api/revenue")
    daily_sales = to_df(revenue_payload, "daily_sales")

    if daily_sales is not None:
        section_title(
            "Sydney anomaly — monthly revenue trend by city",
            "Sydney drawn in orange against every other city in gray, so the drop is "
            "visually unmistakable rather than buried in a table.",
        )
        daily_sales["date"] = pd.to_datetime(daily_sales["date"])
        monthly_by_city = (
            daily_sales.assign(month=daily_sales["date"].dt.to_period("M").astype(str))
            .groupby(["month", "city"], as_index=False)["revenue"]
            .sum()
        )
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
        missing_data_notice("Daily sales")


# ---------------------------------------------------------------------------
# 3. Product Performance
# ---------------------------------------------------------------------------
elif page == "Product Performance":
    st.title("Product Performance")

    products_payload = fetch("/api/products")
    product_performance = to_df(products_payload, "product_performance")

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
        missing_data_notice("Product performance")


# ---------------------------------------------------------------------------
# 4. Inventory Health
# ---------------------------------------------------------------------------
elif page == "Inventory Health":
    st.title("Inventory Health")

    inventory_payload = fetch("/api/inventory")
    inventory_health = to_df(inventory_payload, "inventory_health")

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
        missing_data_notice("Inventory health")


# ---------------------------------------------------------------------------
# 5. Forecasting
# ---------------------------------------------------------------------------
elif page == "Forecasting":
    st.title("Forecasting")
    st.caption(
        "Comparing three baseline forecasting approaches against actual revenue. "
        "This is intentionally simple — see the explanation below for why."
    )

    forecast_payload = fetch("/api/forecast")
    sales_forecast = to_df(forecast_payload, "sales_forecast")

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
            "MAE, RMSE, and MAPE for each model against actual revenue, computed live from the forecast response.",
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
            f"the forecast response ({len(sales_forecast)} rows). Linear regression "
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
        missing_data_notice("Sales forecast")


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
        customers_payload = fetch("/api/customers")
        customer_features = to_df(customers_payload, "customer_features")
        if customer_features is not None:
            st.caption("One row per customer: RFM-style fields (recency, frequency, monetary) plus tenure.")
            st.dataframe(customer_features.head(20), use_container_width=True, hide_index=True)
        else:
            missing_data_notice("Customer features")

    with tab2:
        products_payload = fetch("/api/products")
        product_features = to_df(products_payload, "product_features")
        if product_features is not None:
            st.caption("One row per product: recent sales velocity and rolling growth, alongside return rate.")
            st.dataframe(product_features.head(20), use_container_width=True, hide_index=True)
        else:
            missing_data_notice("Product features")

    with tab3:
        stores_payload = fetch("/api/stores")
        store_features = to_df(stores_payload, "store_features")
        if store_features is not None:
            st.caption("One row per store: revenue, growth, and return-rate fields used by the store-level models.")
            st.dataframe(store_features.head(20), use_container_width=True, hide_index=True)
        else:
            missing_data_notice("Store features")
