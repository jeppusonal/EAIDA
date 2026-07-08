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

st.set_page_config(page_title="EAIDA — Executive Dashboard", layout="wide")


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
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("EAIDA")
st.sidebar.caption("Enterprise AI Data Assistant — MVP dashboard")
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
st.sidebar.caption(f"Backend: `{API_BASE_URL}` — every page calls `/api/*` only.")


# ---------------------------------------------------------------------------
# 1. Executive Overview — GET /api/overview, GET /api/revenue
# ---------------------------------------------------------------------------
if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption("From `GET /api/overview` and `GET /api/revenue`.")

    overview = call_api("/api/overview")

    if overview.get("available"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "Total revenue",
            f"${overview['total_revenue']:,.0f}" if overview.get("total_revenue") is not None else "—",
        )
        col2.metric(
            "Total orders",
            f"{overview['total_orders']:,.0f}" if overview.get("total_orders") is not None else "—",
        )
        col3.metric(
            "Total customers",
            f"{overview['total_customers']:,}" if overview.get("total_customers") is not None else "—",
        )
        col4.metric(
            "Average order value",
            f"${overview['average_order_value']:,.2f}" if overview.get("average_order_value") is not None else "—",
        )
    else:
        unavailable_notice("/api/overview", overview)

    st.divider()

    revenue = call_api("/api/revenue")
    if revenue.get("available"):
        monthly = pd.DataFrame(revenue.get("monthly") or [])
        daily = pd.DataFrame(revenue.get("daily") or [])

        if not monthly.empty and {"month", "revenue"}.issubset(monthly.columns):
            section_title("Revenue trend", "Total revenue by month, from `revenue.monthly`.")
            fig = px.line(monthly, x="month", y="revenue", markers=True)
            fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Month")
            st.plotly_chart(fig, use_container_width=True)

            section_title("Monthly sales volume", "Orders and units sold by month, from `revenue.monthly`.")
            fig2 = go.Figure()
            if "orders" in monthly.columns:
                fig2.add_bar(x=monthly["month"], y=monthly["orders"], name="Orders")
            if "units_sold" in monthly.columns:
                fig2.add_bar(x=monthly["month"], y=monthly["units_sold"], name="Units sold")
            fig2.update_layout(barmode="group", xaxis_title="Month", yaxis_title="Count")
            st.plotly_chart(fig2, use_container_width=True)
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
            colors = ["#D85A30" if c == "Sydney" else "#378ADD" for c in by_city["city"]]
            fig = go.Figure(go.Bar(x=by_city["city"], y=by_city["revenue"], marker_color=colors))
            fig.update_layout(xaxis_title="City", yaxis_title="Revenue ($)")
            st.plotly_chart(fig, use_container_width=True)
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
                "From `revenue.daily`, aggregated to monthly. Sydney in orange, others in gray.",
            )
            daily["date"] = pd.to_datetime(daily["date"])
            monthly_by_city = (
                daily.assign(month=daily["date"].dt.to_period("M").astype(str))
                .groupby(["month", "city"], as_index=False)["revenue"]
                .sum()
            )
            fig = go.Figure()
            for city in sorted(monthly_by_city["city"].unique()):
                sub = monthly_by_city[monthly_by_city["city"] == city]
                is_sydney = city == "Sydney"
                fig.add_scatter(
                    x=sub["month"], y=sub["revenue"], mode="lines+markers", name=city,
                    line=dict(color="#D85A30" if is_sydney else "#B4B2A9", width=3 if is_sydney else 1.5),
                )
            fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
            st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(fig, use_container_width=True)

            if "category" in performance.columns:
                st.divider()
                section_title("Category revenue", "From `products.performance`, rolled up by category.")
                by_cat = performance.groupby("category", as_index=False)["revenue"].sum().sort_values(
                    "revenue", ascending=False
                )
                fig2 = px.pie(by_cat, names="category", values="revenue", hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)

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
                st.plotly_chart(fig3, use_container_width=True)
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
            color_map = {"Low": "#639922", "Medium": "#BA7517", "High": "#A32D2D"}
            fig = px.bar(risk_counts, x="risk_level", y="count", color="risk_level", color_discrete_map=color_map)
            fig.update_layout(xaxis_title="Risk level", yaxis_title="Number of products", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

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
                line=dict(color="#2C2C2A", width=3),
            )
            colors = {"naive_pred": "#378ADD", "rolling_pred": "#1D9E75", "linreg_pred": "#D85A30"}
            labels = {"naive_pred": "Naive (last value)", "rolling_pred": "Rolling mean", "linreg_pred": "Linear regression"}
            for col in model_cols:
                fig.add_scatter(
                    x=data["month"], y=data[col], mode="lines+markers", name=labels.get(col, col),
                    line=dict(color=colors.get(col), dash="dash"),
                )
            fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
            st.plotly_chart(fig, use_container_width=True)

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
