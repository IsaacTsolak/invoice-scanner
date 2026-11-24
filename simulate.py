import math
import random
from datetime import date, timedelta
from sheet_utils import connect, load_products, get_or_create_tab

random.seed(42)
DAYS = 2


# ---------- Safety checks ----------

sheet, worksheet = connect()

if "test" not in sheet.title.lower():
    print("Refusing to run: this only works on a test sheet.")
    exit()

answer = input(f"This resets '{sheet.title}' to par and clears both logs. Continue? (y/n): ")
if answer.lower() != "y":
    print("No changes made.")
    exit()


# ---------- Reset everything to par ----------

products = [p for p in load_products(worksheet) if p["par"]]
for p in products:
    p["front"] = p["par"]
    p["back"] = 0.0

delivery_log = get_or_create_tab(sheet, "Deliveries Log", ["Date", "Invoice #", "Product", "Qty", "Status"])
counts_log = get_or_create_tab(sheet, "Counts Log", ["Date", "Product", "Front", "Back", "Total"])
delivery_log.clear()
delivery_log.append_row(["Date", "Invoice #", "Product", "Qty", "Status"])
counts_log.clear()
counts_log.append_row(["Date", "Product", "Front", "Back", "Total"])


# ---------- Simulate the days ----------

delivery_rows = []
count_rows = []


def save_counts(day):
    for p in products:
        total = round(p["front"] + p["back"], 2)
        count_rows.append([day.isoformat(), p["name"], round(p["front"], 2), round(p["back"], 2), total])


start = date.today() - timedelta(days=DAYS)
save_counts(start)

for d in range(1, DAYS + 1):
    day = start + timedelta(days=d)

    # Morning: delivery tops up anything below par
    for p in products:
        total = p["front"] + p["back"]
        if total < p["par"]:
            qty = math.ceil(p["par"] - total)
            p["back"] += qty
            delivery_rows.append([day.isoformat(), f"SIM-{d}", p["name"], qty, "added"])

    # Service: random sales, poured from front first, then back
    for p in products:
        total = p["front"] + p["back"]
        used = round(random.uniform(0, p["par"] * 0.3) * 4) / 4
        used = min(used, total)
        from_front = min(used, p["front"])
        p["front"] -= from_front
        p["back"] -= used - from_front

    # Night: count
    save_counts(day)


# ---------- Write it all to the sheet ----------

updates = [
    {"range": f"C{p['row']}:D{p['row']}", "values": [[round(p["front"], 2), round(p["back"], 2)]]}
    for p in products
]
worksheet.batch_update(updates)

if delivery_rows:
    delivery_log.append_rows(delivery_rows)
counts_log.append_rows(count_rows)

print(f"Simulated {DAYS} days for {len(products)} products.")
print(f"Logged {len(delivery_rows)} delivery lines and {len(count_rows)} count rows.")