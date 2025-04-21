import xml.etree.ElementTree as ET
import pandas as pd

# Hardcoded file paths
input_file = "path_to_your_xml_file.xml"
output_file = "output.xlsx"

# Parse XML
tree = ET.parse(input_file)
root = tree.getroot()

# Empty DataFrame for now
df = pd.DataFrame()

# Save empty Excel
df.to_excel(output_file, index=False)

print(f"Exported to {output_file}")
