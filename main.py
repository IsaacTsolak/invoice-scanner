import gspread
from datetime import date

# ---------- Helper functions ----------

def to_number(value):
    if value.strip() == "-":
        return 0.0
    cleaned = value.strip().replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


# ---------- Connect to the sheet ----------

client = gspread.service_account(filename="credentials.json")
sheet = client.open("test_invoice_tracker")
worksheet = sheet.sheet1
rows = worksheet.get_all_values()


# ---------- Build the product list ----------

products = []

for i, row in enumerate(rows):
    sheet_row = i + 1
    brand = row[0].strip()
    variant = row[1].strip()
    back_stock = row[3].strip()

    name = (brand + " " + variant).strip()
    back = to_number(back_stock)

    if sheet_row < 6:
        continue
    if name == "":
        continue
    if back is None:
        if back_stock not in ("", "STOCK LEVEL"):
            print(f"Warning: row {sheet_row} ({name}) has unreadable back stock: '{back_stock}'")
        continue

    products.append({"name": name, "row": sheet_row, "back": back})

print(f"Loaded {len(products)} products")


# ---------- Update function ----------

def add_to_back_stock(product_name, qty):
    for p in products:
        if p["name"] == product_name:
            new_back = p["back"] + qty
            worksheet.update_cell(p["row"], 4, new_back)
            print(f"{product_name}: back stock {p['back']} -> {new_back}")
            return
    print(f"Not found: {product_name}")


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
for item in invoice_items:
    print(item)

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

try:
    log = sheet.worksheet("Deliveries Log")
except gspread.WorksheetNotFound:
    log = sheet.add_worksheet(title="Deliveries Log", rows=1000, cols=5)
    log.append_row(["Date", "Invoice #", "Product", "Qty", "Status"])
    print("Created Deliveries Log tab")

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