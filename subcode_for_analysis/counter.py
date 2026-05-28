import json
from collections import defaultdict

# ---- INPUT FILE ----
INPUT_FILE = "total_classified.json"   # change this to your filename

# ---- INIT COUNTERS ----
class_counts = {i: 0 for i in range(1, 9)}

parent_class_counts = {
    "Partially Ambiguous": 0,
    "Completely Ambiguous": 0,
    "Transparent": 0,
    "No Disclosure": 0
}

total_entries = 0

# ---- LOAD JSON ----
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---- PROCESS ----
for item in data:
    total_entries += 1

    cls = item.get("class", None)
    if cls in class_counts:
        class_counts[cls] += 1

    parent = item.get("parent_class", None)
    if parent in parent_class_counts:
        parent_class_counts[parent] += 1

# ---- PRINT RESULTS ----
print("\n===== CLASS DISTRIBUTION (1–8) =====")
for k in range(1, 9):
    print(f"Class {k}: {class_counts[k]}")

print("\n===== PARENT CLASS DISTRIBUTION =====")
for k, v in parent_class_counts.items():
    print(f"{k}: {v}")

print("\nTotal entries:", total_entries)