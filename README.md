# CSOB XML Bank Statement Processor

This is a simple Python script that processes bank statements exported from ČSOB (Czech Republic) in XML format.

## Features

- Parses XML export files from ČSOB.
- Extracts key transaction data such as:
  - Transaction Date
  - Real Transaction Date
  - Transaction Value
  - Transaction Message
  - Place or Location
  - Type (income/outcome)
  - Original Currency and Value
  - From Account and To Account
- Exports a clean `.xlsx` file ready for further analysis.

## How to Use

1. Run the script with Python 3.
2. When prompted, drag and drop the input XML file or type its path.
3. The processed output will be saved in the same folder with a `processed_` prefix.

## Requirements

- Python 3.9+
- pandas
- openpyxl

Install dependencies:

```bash
pip install pandas openpyxl
