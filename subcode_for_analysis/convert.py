import os
import json


# ============================================================
# CLEAN JSON STRING
# ============================================================
def clean_json_string(s):
    if not s:
        return ""

    s = s.strip()

    if s.startswith("```"):
        parts = s.split("```")
        if len(parts) >= 2:
            s = parts[1]
        if s.startswith("json"):
            s = s[len("json"):].strip()

    if "```" in s:
        s = s.split("```")[0]

    return s.strip()


# ============================================================
# STEP 1: JSONL -> JSON
# ============================================================
def convert_jsonl_to_json(input_file, output_file):
    data = []
    skipped_empty = 0
    skipped_bad = 0

    with open(input_file, "r") as f:
        for i, line in enumerate(f):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                print(f"❌ Invalid JSONL line {i}")
                continue

            raw_output = obj.get("model_output", "")

            if not raw_output or str(raw_output).strip() == "":
                skipped_empty += 1
                continue

            cleaned = clean_json_string(raw_output)

            try:
                model_output = json.loads(cleaned)
            except json.JSONDecodeError:
                skipped_bad += 1
                continue

            data.append({
                "domain": obj.get("domain"),
                "model_output": model_output
            })

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✔ Converted: {input_file}")
    print(f"✔ Valid: {len(data)} | Empty: {skipped_empty} | Bad: {skipped_bad}")

    return output_file


# ============================================================
# STEP 2: CLASSIFICATION
# ============================================================
def classify(V, C, S):
    if not V and C and S: return 1
    if not V and C and not S: return 2
    if not V and not C and S: return 3
    if V and C and S: return 4
    if V and C and not S: return 5
    if V and not C and S: return 6
    if V and not C and not S: return 7
    if not V and not C and not S: return 8


def parent_class(class_id):
    if class_id in [1, 2, 3]:
        return "Transparent"
    if class_id in [4, 5, 6]:
        return "Partially Ambiguous"
    if class_id == 7:
        return "Completely Ambiguous"
    if class_id == 8:
        return "No Disclosure"
    return "Unknown"


def classify_file(input_json, output_json):
    with open(input_json) as f:
        data = json.load(f)

    results = []

    for item in data:
        domain = item["domain"]
        parsed = item["model_output"]

        V = parsed.get("vague", False)
        C = parsed.get("cookies", False)
        F = parsed.get("Fingerprinting", False)

        explanation = parsed.get("explanation")
        techniques = parsed.get("tracking_technique", [])

        class_id = classify(V, C, F)
        pclass = parent_class(class_id)

        results.append({
            "domain": domain,
            "tracking_techniques": techniques,
            "V": V,
            "C": C,
            "F": F,
            "parent_class": pclass,
            "class": class_id,
            "explanation": explanation
        })

    with open(output_json, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✔ Classified saved: {output_json}")


# ============================================================
# STEP 3: RUN FOR ALL LOCATIONS
# ============================================================
def run_pipeline(base_mode="REJECT", countries=None):

    if countries is None:
        countries = ["GER", "BRZ", "SA", "SWD", "US_E", "US_W", "AUS"]

    for country in countries:
        loc = f"{base_mode}/{country}"

        input_jsonl = f"{loc}/output.jsonl"
        intermediate_json = f"{loc}/total.json"
        final_json = f"{loc}/total_classified.json"

        print("\n" + "=" * 60)
        print(f"Processing: {loc}")

        if not os.path.exists(input_jsonl):
            print(f"❌ Missing file: {input_jsonl}")
            continue

        # Step 1
        convert_jsonl_to_json(input_jsonl, intermediate_json)

        # Step 2
        classify_file(intermediate_json, final_json)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    run_pipeline()