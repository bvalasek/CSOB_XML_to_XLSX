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

    trans_type = ""
    if transaction_value is not None:
        trans_type = "income" if transaction_value > 0 else "outcome"

    message = finsta05.findtext("PART_ID1_2")
    real_transaction_date = None
    if message:
        match = re.search(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b", message)
        if match:
            day, month, year = match.group(0).split(".")
            real_transaction_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    place = finsta05.findtext("PART_ID1_1")
    account = finsta05.findtext("PART_ACC_ID")

    original_currency = finsta05.findtext("ORIG_CURR")
    original_currency_value_raw = finsta05.findtext("ORIG_AMOUNT")
    original_currency_value = None
    if original_currency_value_raw:
        original_currency_value = float(original_currency_value_raw.replace(",", "."))

    part_accno = finsta05.findtext("PART_ACCNO")
    part_bank_id = finsta05.findtext("PART_BANK_ID")

    from_account = ""
    to_account = ""
    if trans_type == "income" and part_accno and part_bank_id:
        from_account = f"{part_accno}/{part_bank_id}"
    elif trans_type == "outcome" and part_accno and part_bank_id:
        to_account = f"{part_accno}/{part_bank_id}"

    parts = []
    place_cleaned = ""
    if place:
        if "Místo: " in place:
            place_cleaned = place.split("Místo: ")[-1].strip()
        else:
            place_cleaned = place.strip()
        parts.append(place_cleaned)
    if message:
        parts.append(message.strip())
    if account:
        parts.append(account.strip())

    transaction_message = " | ".join(parts)

    place_or_location = ""
    if account and place_cleaned:
        place_or_location = f"{account} {place_cleaned}"
    elif account:
        place_or_location = account
    elif place_cleaned:
        place_or_location = place_cleaned

    record = {
        "transaction date": transaction_date,
        "transaction value": transaction_value,
        "real transaction date": real_transaction_date,
        "transaction message": transaction_message,
        "place or location": place_or_location,
        "type": trans_type,
        "original currency": original_currency,
        "original currency value": original_currency_value,
        "from_account": from_account,
        "to_account": to_account,
    }
    records.append(record)

# ==== EXPORT ====
df = pd.DataFrame(records)
df.to_excel(output_file, index=False)

print(f"Exported to {output_file}")
