import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

# ==== SETTINGS ====
input_file = "path_to_your_xml_file.xml"
output_file = "output.xlsx"

# ==== PROCESS XML ====
tree = ET.parse(input_file)
root = tree.getroot()

# For now, create an empty DataFrame
records = []

# ==== EXPORT ====
df = pd.DataFrame(records)
df.to_excel(output_file, index=False)

print(f"Exported to {output_file}")