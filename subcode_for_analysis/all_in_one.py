import json
import pandas as pd

import json

with open("M_random_900_classified.json", "r") as f:
    data = json.load(f)

websites_df = pd.read_csv("random900_translated.csv")

websites_df = websites_df[["domains", "translated_text"]]

websites_df["domains"] = websites_df["domains"].str.strip().str.lower()

rows = []

for entry in data:
    domain = entry.get("domain", "").strip().lower()

    # Find matching row in websites.csv
    match = websites_df[websites_df["domains"] == domain]

    if match.empty:
        continue 

    translated_text = match.iloc[0]["translated_text"]

    rows.append({
        "domain": domain,
        "translated_text": translated_text,
        "Cookies": entry.get("C", ""),
        "Fingerprinting": entry.get("F", ""),
        "Vague": entry.get("V", ""),
        "parent_class": entry.get("parent_class", ""),
        "class_id": entry.get("class", ""),
        "explanation": entry.get("explanation", "")
    })

final_df = pd.DataFrame(rows)

final_df.to_csv("M_Inter_Evaluation_900.csv", index=False)

