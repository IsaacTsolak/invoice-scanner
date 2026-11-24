from datetime import datetime, timedelta
from sheet_utils import connect, load_products, get_or_create_tab


# ---------- Figure out the business date ----------

business_date = (datetime.now() - timedelta(hours=6)).date().isoformat()


# ---------- Load tonight's counts ----------

sheet, worksheet = connect()
products = load_products(worksheet)

counts_log = get_or_create_tab(
    sheet, "Counts Log", ["Date", "Product", "Front", "Back", "Total"]
)


# ---------- Don't save the same night twice ----------

if business_date in counts_log.col_values(1):
    print(f"Counts for {business_date} are already saved. Nothing to do.")
    exit()


# ---------- Save the snapshot ----------

rows = []
for p in products:
    rows.append([business_date, p["name"], p["front"], p["back"], p["total"]])

answer = input(f"Save counts for {business_date} ({len(rows)} products)? (y/n): ")

if answer.lower() == "y":
    counts_log.append_rows(rows)
    print(f"Saved {len(rows)} counts for {business_date}.")
else:
    print("No changes made.")