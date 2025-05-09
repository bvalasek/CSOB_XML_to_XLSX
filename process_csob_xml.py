import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import re

# ==== SETTINGS ====
input_path = input("Zadaj cestu k XML súboru alebo priečinku: ").strip()
input_path = input_path.replace('\\', '').strip('"\'')
input_file = Path(input_path)

xml_files = []
if input_file.is_file() and input_file.suffix.lower() == ".xml":
    xml_files = [input_file]
elif input_file.is_dir():
    xml_files = list(input_file.glob("*.xml"))
else:
    print("Error: Musíš zadať XML súbor alebo priečinok obsahujúci XML súbory!")
    exit(1)

for xml_file in xml_files:
    output_base = xml_file.parent / f"processed_{xml_file.stem}"
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

        return cz_type

    def categorize_transaction(text):
        text = text.lower()
        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in text for keyword in keywords):
                return category
        return "Other"

    # ==== PROCESS XML ====
    tree = ET.parse(xml_file)
    root = tree.getroot()

    records = []

    for finsta05 in root.findall(".//FINSTA05"):
        transaction_date = finsta05.findtext("DPROCD")
        transaction_value_raw = finsta05.findtext("S61_CASTKA")
        transaction_value = float(transaction_value_raw.replace(",", ".")) if transaction_value_raw else None

        trans_type = "income" if transaction_value and transaction_value > 0 else "outcome"

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
        original_currency_value = float(original_currency_value_raw.replace(",", ".")) if original_currency_value_raw else None

        part_accno = finsta05.findtext("PART_ACCNO")
        part_bank_id = finsta05.findtext("PART_BANK_ID")

        from_account = f"{part_accno}/{part_bank_id}" if trans_type == "income" and part_accno and part_bank_id else ""
        to_account = f"{part_accno}/{part_bank_id}" if trans_type == "outcome" and part_accno and part_bank_id else ""

        payment_type_cz = finsta05.findtext("S61_POST_NAR")
        payment_type_en = translate_payment_type(payment_type_cz)

        parts = []
        place_cleaned = ""
        if place:
            place_cleaned = place.split("Místo: ")[-1].strip() if "Místo: " in place else place.strip()
            parts.append(place_cleaned)
        if message:
            parts.append(message.strip())
        if account:
            parts.append(account.strip())

        transaction_message = " | ".join(parts)

        place_or_location = f"{account} {place_cleaned}" if account and place_cleaned else account or place_cleaned

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

    summary = df.pivot_table(
        index="category",
        columns="type",
        values="transaction value",
        aggfunc="sum",
        fill_value=0
    ).reset_index()
    summary.columns.name = None
    summary["Net total"] = summary.get("income", 0) + summary.get("outcome", 0)

    total_income = summary["income"].sum()
    total_outcome = summary["outcome"].sum()
    net_total = summary["Net total"].sum()

    total_summary = pd.DataFrame({
        "category": ["Total income", "Total outcome", "Net total"],
        "income": [total_income, 0, total_income],
        "outcome": [0, total_outcome, total_outcome],
        "Net total": [total_income, total_outcome, net_total]
    })

    summary = pd.concat([summary, pd.DataFrame([{}]), total_summary], ignore_index=True)

    df_sorted = df.sort_values(by=["category", "transaction date"])

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
        summary.to_excel(writer, index=False, sheet_name="Category Summary")
        df_sorted.to_excel(writer, index=False, sheet_name="Transactions by Category")

    df.to_csv(output_csv, index=False)

    print(f"Exported to {output_excel} and {output_csv}")
