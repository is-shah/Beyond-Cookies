import os
import json
import pandas as pd


# ============================================================
# CONFIG
# ============================================================
base_mode = "REJECT"
countries = ["GER", "BRZ", "SA", "SWD", "US_E", "US_W", "AUS"]

output_map = {
    "Transparent": "Transparent.csv",
    "Partially Ambiguous": "Partially_Ambiguous.csv",
    "Completely Ambiguous": "Completely_Ambiguous.csv",
    "No Disclosure": "No_Disclosure.csv"
}


# ============================================================
# MAIN PIPELINE
# ============================================================
def split_per_location():
    for country in countries:
        loc = f"{base_mode}/{country}"
        input_file = f"{loc}/total_classified.json"

        print("\n" + "=" * 60)
        print(f"Processing: {loc}")

        if not os.path.exists(input_file):
            print(f"❌ Missing: {input_file}")
            continue

        # load classified output
        with open(input_file, "r") as f:
            data = json.load(f)

        # create buckets
        buckets = {
            "Transparent": [],
            "Partially Ambiguous": [],
            "Completely Ambiguous": [],
            "No Disclosure": []
        }

        # split domains
        for item in data:
            domain = item.get("domain")
            label = item.get("parent_class", "Unknown")

            if label in buckets:
                buckets[label].append(domain)

        # save CSVs
        for label, filename in output_map.items():
            out_path = os.path.join(loc, filename)

            df = pd.DataFrame(buckets[label], columns=["domain"])
            df.to_csv(out_path, index=False)

            print(f"✔ Saved {out_path} ({len(df)})")


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    split_per_location()