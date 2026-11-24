import gspread

client = gspread.service_account(filename="credentials.json")
print("connected to Google")

sheet = client.open("test_invoice_tracker")
print("opened", sheet.title)

worksheet = sheet.sheet1
rows = worksheet.get_all_values()

products = []

for i, row in enumerate(rows):
    sheet_row = i + 1
    brand = row[0].strip()
    variant = row[1].strip()
    back_stock = row[3].strip()

    if sheet_row < 6:
        continue
    if brand == "" or back_stock == "":
        continue

    name = (brand + " " + variant).strip()
    products.append({"name": name, "row": sheet_row, "back": back_stock})

for p in products:
    print(p)


def add_to_back_stock(product_name, qty):
    for p in products:
        if p["name"] == product_name:
            new_back = float(p["back"]) + qty
            worksheet.update_cell(p["row"], 4, new_back)
            print(f"{product_name}: back stock {p['back']} -> {new_back}")
            return
    print(f"Not found: {product_name}")

add_to_back_stock("Titos", 6)