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

output_base = input_file.parent / f"processed_{input_file.stem}"
output_excel = output_base.with_suffix(".xlsx")
output_csv = output_base.with_suffix(".csv")

# ==== CATEGORY RULES ====
CATEGORY_RULES = {
    "Personal Loans": ["lesia dmytrenko"],
    "Gifts": ["manufaktura", "dar", "donio"],
    "Subscriptions": ["apple.com", "youtubepremium", "spotify", "budgetbakers", "chatgpt"],
    "Income": ["dulovic michal", "infor"],
    "Internal transfers": ["258867701/0300", "296660584/0300", "1522916037/3030", "revolut"],
    "Groceries": ["tesco", "lidl", "albert", "billa", "rohlik", "košík", "kaufland", "spar", "penny", "coop", "potraviny", "paul"],
    "Transport": ["čd", "pmdp", "bolt", "uber"],
    "Dining": ["bbdomu", "mcdonald", "restaurace", "bistro", "kfc", "nesnezeno", "toogoodtogo", "pizza", "kebab", "jidelna", "beas", "dhaba", "pivstro", "fior di", "country life", "loving hut", "obederie"],
    "Cafe (Study)": ["barcelounoc", "skautský", "cafe neustadt", "camp"],
    "Cafe (Drinks)": ["friends bar", "lod riverside", "elpicko", "qcafe"],
    "Bills": ["nájom", "elektrina", "plyn", "voda", "čez", "e.on", "pre", "yello", "mnd", "ppas"],
    "Personal Care": ["dm", "rossmann", "teta", "drogerie", "kaderníctvo", "barber"],
    "Medical bills": ["lekáreň", "doktor", "fyzioterapia", "dr. max"],
    "Housing": ["ikea", "jysk", "bauhaus", "alza", "obi", "datart", "temu"],
    "Clothing": ["hm", "lindex", "reserved", "new yorker", "3someconcept"],
    "Insurance": ["pojišťovna", "životní pojištění"],
    "Sport and Culture": ["vstupenky", "goout", "decathlon", "kino", "divadlo", "závody", "cinema city"],
    "Telecommunication": ["o2", "vodafone", "upc"],
    "ATM Withdrawals": ["atm", "ac01", "csas", "kb atm"],
    "Investments": ["čsob drobné", "edward", "bohatství"]
}

# ==== HELPER FUNCTIONS ====
def translate_payment_type(cz_type):
    if not cz_type:
        return ""

    cz_type = cz_type.strip()

    partial_translations = [
        ("Odchozí úhrada SEPA", "SEPA outgoing payment"),
        ("Odchozí úhrada okamžitá", "Instant outgoing payment"),
        ("Odchozí úhrada", "Outgoing payment"),
        ("Příchozí úhrada kartou", "Card incoming payment"),
        ("Příchozí úhrada", "Incoming payment"),
        ("Trvalý příkaz", "Standing order"),
        ("Inkaso", "Direct debit"),
        ("Platba kartou", "Card payment"),
        ("Transakce platební kartou", "Card transaction"),
        ("Výběr z bankomatu", "ATM withdrawal"),
        ("ČSOB Drobné", "ČSOB micro rounding"),
        ("Nákup podílových listů", "Mutual fund purchase"),
        ("Nezpoplatněný trvalý převod", "Internal transfer (non-charged)"),
    ]

    for cz_pattern, en_translation in partial_translations:
        if cz_pattern in cz_type:
            return en_translation

    return cz_type  # fallback

def categorize_transaction(text):
    text = text.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"

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

    payment_type_cz = finsta05.findtext("S61_POST_NAR")
    payment_type_en = translate_payment_type(payment_type_cz)

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

    category = categorize_transaction(transaction_message)

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
        "payment type": payment_type_en,
        "category": category,
    }
    records.append(record)

# ==== EXPORT ====
df = pd.DataFrame(records)
df.to_excel(output_excel, index=False)
df.to_csv(output_csv, index=False)

print(f"Exported to {output_excel} and {output_csv}")
