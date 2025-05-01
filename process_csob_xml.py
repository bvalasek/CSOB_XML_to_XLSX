import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import re

# ==== SETTINGS ====
input_path = input("Zadaj cestu k XML súboru (pretiahni súbor alebo zadaj cestu): ").strip()
input_path = input_path.replace('\\', '').strip('"\'')
input_file = Path(input_path)

# Kontrola prípony súboru
if input_file.suffix.lower() != ".xml":
    print("Error: Musíš zadať XML súbor!")
    exit(1)

output_file = input_file.parent / f"processed_{input_file.stem}.xlsx"

# ==== PROCESS XML ====
tree = ET.parse(input_file)
root = tree.getroot()

records = []

for finsta05 in root.findall(".//FINSTA05"):
    transaction_date = finsta05.findtext("DPROCD")
    transaction_value_raw = finsta05.findtext("S61_CASTKA")
    transaction_value = None
    if transaction_value_raw:
        transaction_value = float(transaction_value_raw.replace(",", "."))

    message = finsta05.findtext("PART_ID1_2")
    real_transaction_date = None
    if message:
        match = re.search(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b", message)
        if match:
            day, month, year = match.group(0).split(".")
            real_transaction_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    record = {
        "transaction date": transaction_date,
        "transaction value": transaction_value,
        "real transaction date": real_transaction_date,
    }
    records.append(record)

# ==== EXPORT ====
df = pd.DataFrame(records)
df.to_excel(output_file, index=False)

print(f"Exported to {output_file}")
