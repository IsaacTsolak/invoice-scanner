from sheet_utils import connect

sheet, worksheet = connect()
rows = worksheet.get_all_values()

for i, row in enumerate(rows[7:99]):
    print(i + 8, row[0], row[1], "|", row[8:16])