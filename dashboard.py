import streamlit as st
import pandas as pd
from datetime import date, timedelta
from sheet_utils import connect, load_products

st.set_page_config(page_title="Bar Inventory", layout="wide")

DELIVERY_COLS = ["Date", "Invoice #", "Product", "Qty", "Status"]
COUNT_COLS = ["Date", "Product", "Front", "Back", "Total"]


# ---------- Load data (cached for 60 seconds) ----------

@st.cache_data(ttl=60)
def load_data():
    sheet, worksheet = connect()
    products = pd.DataFrame(load_products(worksheet))
    deliveries = pd.DataFrame(sheet.worksheet("Deliveries Log").get_all_records(), columns=DELIVERY_COLS)
    counts = pd.DataFrame(sheet.worksheet("Counts Log").get_all_records(), columns=COUNT_COLS)
    return products, deliveries, counts


products, deliveries, counts = load_data()

deliveries["Qty"] = pd.to_numeric(deliveries["Qty"], errors="coerce")
counts["Total"] = pd.to_numeric(counts["Total"], errors="coerce")


# ---------- Calculations on ALL data ----------

stock = products.dropna(subset=["total", "par"])

below = stock[stock["total"] < stock["par"]].copy()
below["need"] = below["par"] - below["total"]
below = below.sort_values("need", ascending=False)

added = deliveries[deliveries["Status"] == "added"]
needs_review = deliveries[deliveries["Status"] == "needs review"]

counts = counts.sort_values(["Product", "Date"])
counts["Start"] = counts.groupby("Product")["Total"].shift(1)
delivered = added.groupby(["Date", "Product"])["Qty"].sum().reset_index(name="Delivered")
usage = counts.merge(delivered, on=["Date", "Product"], how="left")
usage["Delivered"] = usage["Delivered"].fillna(0)
usage["Used"] = usage["Start"] + usage["Delivered"] - usage["Total"]
usage = usage.dropna(subset=["Start", "Used"])


# ---------- Time period filter ----------

period = st.sidebar.radio(
    "Time period", ["Last 7 days", "Last 30 days", "All time", "Custom range"]
)
today = date.today()

if period == "Last 7 days":
    start_d, end_d = today - timedelta(days=6), today
elif period == "Last 30 days":
    start_d, end_d = today - timedelta(days=29), today
elif period == "All time":
    start_d, end_d = date(2000, 1, 1), date(2100, 1, 1)
else:
    picked = st.sidebar.date_input(
        "Pick a start and end date",
        value=(today - timedelta(days=6), today),
    )
    if len(picked) == 2:
        start_d, end_d = picked
    else:
        start_d = end_d = picked[0]
        st.sidebar.caption("Now pick an end date.")

start_s, end_s = start_d.isoformat(), end_d.isoformat()

usage_view = usage[(usage["Date"] >= start_s) & (usage["Date"] <= end_s)]
added_view = added[(added["Date"] >= start_s) & (added["Date"] <= end_s)]


# ---------- Calculations on the selected period ----------

avg_used = usage_view.groupby("Product")["Used"].mean().round(2).reset_index(name="Avg used per day")
runway = stock.merge(avg_used, left_on="name", right_on="Product")
runway = runway[runway["Avg used per day"] > 0].copy()
runway["Days left"] = (runway["total"] / runway["Avg used per day"]).round(1)
runway = runway.sort_values("Days left")
running_out = runway[runway["Days left"] <= 3]

if usage.empty:
    last_day, used_last_day = "n/a", 0
else:
    last_day = usage["Date"].max()
    used_last_day = usage.loc[usage["Date"] == last_day, "Used"].sum()


# ---------- Header ----------

st.title("Bar Inventory Dashboard")
if period == "All time":
    st.caption("Showing: all time")
else:
    st.caption(f"Showing: {start_s} to {end_s}")

if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Items below par", len(below))
c2.metric("Running out within 3 days", len(running_out))
c3.metric(f"Bottles used on {last_day}", round(used_last_day, 1))
c4.metric("Invoice lines to review", len(needs_review))


# ---------- Tabs ----------

tab_order, tab_usage, tab_deliveries = st.tabs(["Ordering", "Usage", "Deliveries"])

with tab_order:
    left, right = st.columns(2)
    with left:
        st.subheader("Below par")
        st.dataframe(
            below[["name", "total", "par", "need"]].rename(
                columns={"name": "Product", "total": "On hand", "par": "Par", "need": "Need"}
            ),
            hide_index=True,
        )
    with right:
        st.subheader("Days of stock left")
        st.dataframe(
            runway[["name", "total", "Avg used per day", "Days left"]].rename(
                columns={"name": "Product", "total": "On hand"}
            ),
            hide_index=True,
        )

with tab_usage:
    if usage_view.empty:
        st.info("No usage in this period yet.")
    else:
        left, right = st.columns(2)
        with left:
            st.subheader("Top 10 most used")
            st.bar_chart(usage_view.groupby("Product")["Used"].sum().nlargest(10))
        with right:
            st.subheader("Bottles used per day")
            st.bar_chart(usage_view.groupby("Date")["Used"].sum())

        st.subheader("Usage for one product")
        choice = st.selectbox("Pick a product", sorted(usage_view["Product"].unique()))
        st.dataframe(
            usage_view[usage_view["Product"] == choice][["Date", "Start", "Delivered", "Total", "Used"]],
            hide_index=True,
        )

with tab_deliveries:
    if not needs_review.empty:
        st.warning(f"{len(needs_review)} invoice lines didn't match a product and need review.")
        st.dataframe(needs_review, hide_index=True)

    st.subheader("Bottles delivered by product")
    if added_view.empty:
        st.info("No deliveries in this period.")
    else:
        st.bar_chart(added_view.groupby("Product")["Qty"].sum())

    with st.expander("All delivery lines"):
        st.dataframe(deliveries, hide_index=True)