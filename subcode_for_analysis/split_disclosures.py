# split_disclosure.py

import json
import csv
import os
from collections import defaultdict

# ---------------------------------------------------------
# LOAD CLASSIFIED DATA
# ---------------------------------------------------------

INPUT_FILE = "REJECT/1M/total_classified.json"

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

# ---------------------------------------------------------
# CREATE OUTPUT DIRECTORY
# ---------------------------------------------------------

OUTPUT_DIR = "REJECT/1M"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# GROUP BY CLASS ID
# ---------------------------------------------------------

class_groups = defaultdict(list)

for entry in data:
    class_id = entry.get("class")
    domain = entry.get("domain")

    if domain:
        class_groups[class_id].append(domain)

# ---------------------------------------------------------
# SAVE CLASS-WISE CSV FILES
# ---------------------------------------------------------

for class_id in range(1, 9):

    domains = class_groups.get(class_id, [])

    if not domains:
        continue

    output_file = os.path.join(
        OUTPUT_DIR,
        f"class_{class_id}.csv"
    )

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow(["domain"])

        for domain in domains:
            writer.writerow([domain])

    print(f"✅ Saved: {output_file}")

# ---------------------------------------------------------
# PARENT CLASS MAPPING
# ---------------------------------------------------------

PARENT_CLASS_MAPPING = {
    "Transparent": [1, 2, 3],
    "Partially_Ambiguous": [4, 5, 6],
    "Completely_Ambiguous": [7],
    "No_Disclosure": [8]
}

# ---------------------------------------------------------
# SAVE PARENT-CLASS CSV FILES
# ---------------------------------------------------------

for parent_name, class_ids in PARENT_CLASS_MAPPING.items():

    combined_domains = []

    for cid in class_ids:
        combined_domains.extend(class_groups.get(cid, []))

    if not combined_domains:
        continue

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{parent_name}.csv"
    )

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow(["domain"])

        for domain in combined_domains:
            writer.writerow([domain])

    print(f"✅ Saved: {output_file}")

print("\n🎯 All disclosure splits created successfully.")