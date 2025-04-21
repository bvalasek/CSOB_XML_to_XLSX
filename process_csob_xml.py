import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

# ==== SETTINGS ====
input_path = input("Zadaj cestu k XML súboru (pretiahni súbor alebo zadaj cestu): ").strip()
input_path = input_path.replace('\\', '')
input_file = Path(input_path)
output_file = input_file.parent / f"processed_{input_file.stem}.xlsx"

# ==== PROCESS XML ====
tree = ET.parse(input_file)
root = tree.getroot()

# For now, create an empty DataFrame
records = []

# ==== EXPORT ====
df = pd.DataFrame(records)
df.to_excel(output_file, index=False)

print(f"Exported to {output_file}")
