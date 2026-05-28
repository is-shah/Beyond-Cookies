import json

input_file = "REJECT/1M/output.jsonl"
output_file = "REJECT/1M/output.json"

def clean_json_string(s):
    if not s:
        return ""

    s = s.strip()

    # Remove markdown code fences like ```json ... ```
    if s.startswith("```"):
        parts = s.split("```")
        if len(parts) >= 2:
            s = parts[1]  # content inside first ```
        if s.startswith("json"):
            s = s[len("json"):].strip()

    # Remove any trailing ```
    if "```" in s:
        s = s.split("```")[0]

    return s.strip()

data = []
skipped_empty = 0
skipped_bad = 0

with open(input_file, "r") as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSONL line at {i}")
            continue

        raw_output = obj.get("model_output", "")

        # 🔴 Skip empty outputs
        if not raw_output or str(raw_output).strip() == "":
            print(f"⚠️ Skipping empty model_output at line {i}")
            skipped_empty += 1
            continue

        cleaned = clean_json_string(raw_output)

        try:
            model_output = json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"❌ Bad JSON at line {i}: {cleaned[:120]}")
            skipped_bad += 1
            continue

        data.append({
            "domain": obj.get("domain"),
            "model_output": model_output
        })

# Write final JSON array
with open(output_file, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Done")
print(f"✔️ Total valid: {len(data)}")
print(f"⚠️ Skipped empty: {skipped_empty}")
print(f"❌ Skipped bad JSON: {skipped_bad}")
