from datetime import date
from sheet_utils import connect, load_products, get_or_create_tab


# ---------- Connect and load products ----------

sheet, worksheet = connect()
products = load_products(worksheet)
print(f"Loaded {len(products)} products")


# ---------- Read the invoice ----------

invoice_items = []

with open("sample_invoice.txt") as f:
    for line in f:
        line = line.strip()
        if line == "":
            continue
        name, qty = line.split(",")
        invoice_items.append({"name": name.strip(), "qty": float(qty)})

print(f"Loaded {len(invoice_items)} invoice items")


# ---------- Match invoice to sheet ----------

product_lookup = {p["name"].lower(): p for p in products}

matched = []
unmatched = []

for item in invoice_items:
    key = item["name"].lower()
    if key in product_lookup:
        matched.append({"item": item, "product": product_lookup[key]})
    else:
        unmatched.append(item)

print(f"\nMatched: {len(matched)}")
for m in matched:
    p = m["product"]
    print(f"  {m['item']['name']} -> row {p['row']}, back {p['back']} + {m['item']['qty']}")

print(f"\nUnmatched (needs review): {len(unmatched)}")
for item in unmatched:
    print(f"  {item['name']} x{item['qty']}")


# ---------- Deliveries log ----------

log = get_or_create_tab(sheet, "Deliveries Log", ["Date", "Invoice #", "Product", "Qty", "Status"])

invoice_id = input("\nInvoice number: ").strip()

if invoice_id in log.col_values(2):
    print(f"Invoice {invoice_id} was already added. Stopping so nothing gets counted twice.")
    exit()


# ---------- Apply updates ----------

answer = input("\nApply these updates to the sheet? (y/n): ")

if answer.lower() == "y":
    today = date.today().isoformat()

    updates = []
    log_rows = []

    for m in matched:
        p = m["product"]
        new_back = p["back"] + m["item"]["qty"]
        updates.append({"range": f"D{p['row']}", "values": [[new_back]]})
        log_rows.append([today, invoice_id, p["name"], m["item"]["qty"], "added"])

    for item in unmatched:
        log_rows.append([today, invoice_id, item["name"], item["qty"], "needs review"])

    worksheet.batch_update(updates)
    log.append_rows(log_rows)
    print(f"Updated {len(updates)} products and logged {len(log_rows)} lines.")
else:
    print("No changes made.")