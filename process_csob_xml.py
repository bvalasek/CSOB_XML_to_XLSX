import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

# ==== SETTINGS ====
input_path = input("Zadaj cestu k XML súboru (pretiahni súbor alebo zadaj cestu): ").strip()
input_path = input_path.replace('\\', '')
input_file = Path(input_path)

# Kontrola prípony súboru
if input_file.suffix.lower() != ".xml":
    print("Error: Musíš zadať XML súbor!")
    exit(1)

output_file = input_file.parent / f"processed_{input_file.stem}.xlsx"
