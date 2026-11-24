import gspread


def to_number(value):
    if value.strip() == "-":
        return 0.0
    cleaned = value.strip().replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def connect(sheet_name="test_invoice_tracker"):
    client = gspread.service_account(filename="credentials.json")
    sheet = client.open(sheet_name)
    return sheet, sheet.sheet1


def load_products(worksheet):
    rows = worksheet.get_all_values()
    products = []

    for i, row in enumerate(rows):
        sheet_row = i + 1
        name = (row[0].strip() + " " + row[1].strip()).strip()
        back_stock = row[3].strip()
        back = to_number(back_stock)

        if sheet_row < 6 or name == "":
            continue
        if back is None:
            if back_stock not in ("", "STOCK LEVEL"):
                print(f"Warning: row {sheet_row} ({name}) has unreadable back stock: '{back_stock}'")
            continue

        products.append({
            "name": name,
            "row": sheet_row,
            "front": to_number(row[2]),
            "back": back,
            "total": to_number(row[4]),
            "par": to_number(row[5])
        })

    return products


def get_or_create_tab(sheet, title, headers):
    try:
        return sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        tab = sheet.add_worksheet(title=title, rows=1000, cols=len(headers))
        tab.append_row(headers)
        print(f"Created {title} tab")
        return tab

def read_invoice(path):
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line == "":
                continue
            name, qty = line.split(",")
            items.append({"name": name.strip(), "qty": float(qty)})
    return items