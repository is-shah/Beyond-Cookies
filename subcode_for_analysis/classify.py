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

# ---------------------------------------------------------
# PARSE MODEL OUTPUTS AND CLASSIFY
# ---------------------------------------------------------
import json
with open("REJECT/1M/output.json") as f:
    data = json.load(f)

results = []

for item in data:
    domain = item["domain"]

    parsed_raw = item["model_output"]

    parsed = parsed_raw
    V = parsed["vague"]
    C = parsed["cookies"]
    F = parsed["Fingerprinting"]
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
        "explanation" : explanation
    })

# ---------------------------------------------------------
# SAVE FINAL CLASSIFIED OUTPUT
# ---------------------------------------------------------
with open("REJECT/1M/total_classified.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ Classification saved to classified_output.json")
