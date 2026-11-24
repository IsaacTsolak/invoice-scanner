import streamlit as st
import pandas as pd
from sheet_utils import connect

st.title("Bar Inventory Dashboard")

sheet, worksheet = connect()
deliveries = pd.DataFrame(sheet.worksheet("Deliveries Log").get_all_records())

st.subheader("All deliveries")
st.dataframe(deliveries)

added = deliveries[deliveries["Status"] == "added"]
by_product = added.groupby("Product")["Qty"].sum().sort_values(ascending=False)

st.subheader("Bottles delivered by product")
st.bar_chart(by_product)

# ---------- Usage ----------

counts = pd.DataFrame(sheet.worksheet("Counts Log").get_all_records())
counts = counts.sort_values(["Product", "Date"])

counts["Start"] = counts.groupby("Product")["Total"].shift(1)

delivered = added.groupby(["Date", "Product"])["Qty"].sum().reset_index(name="Delivered")
usage = counts.merge(delivered, on=["Date", "Product"], how="left")
usage["Delivered"] = usage["Delivered"].fillna(0)

usage["Used"] = usage["Start"] + usage["Delivered"] - usage["Total"]
usage = usage.dropna(subset=["Start"])

st.subheader("Top 10 most used bottles")
top_used = usage.groupby("Product")["Used"].sum().nlargest(10)
st.bar_chart(top_used)

st.subheader("Total bottles used per day")
st.bar_chart(usage.groupby("Date")["Used"].sum())

st.subheader("Usage for one product")
choice = st.selectbox("Pick a product", sorted(usage["Product"].unique()))
st.dataframe(
    usage[usage["Product"] == choice][["Date", "Start", "Delivered", "Total", "Used"]],
    hide_index=True,
)