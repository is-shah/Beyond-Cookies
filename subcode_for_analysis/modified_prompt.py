import time
import os

SYSTEM_PROMPT = """
You are an expert in web tracking techniques and privacy-policy analysis.

### TASK — Extract Tracking Details
Carefully analyze the provided cookie-banner text and extract the following fields:

---

## 1. "tracking_technique"

- List all tracking mechanisms or categories explicitly mentioned.
- Normalize all terms to lowercase.
- Include a term only if it meets ALL conditions:
    1. It appears explicitly in the text.
    2. It is described as being used or potentially used.
    3. It is *not* mentioned only in a negated/denial context.

### Allowed Technique Categories  
(Include only when explicitly named)

- Stateful Tracking (Targeting Cookies):"cookies", "local storage", "session storage"

- Fingerprinting (Stateless Method):"device scanning", "device identifiers", "precise geolocation", "ip address"

- Vague Terms:"tracking technologies", "similar technologies", "technologies", "trackers", "tracers", "personal data", "browsing data"

---

### IMPORTANT NOTE FOR VAGUE TERMS

- Contextual Evidence has STRICT priority over lexical vagueness.
- The model MUST evaluate the surrounding context BEFORE deciding whether a vague term is actually vague.
- The model MUST NOT rely on isolated keywords.
- Contextual grounding MUST be evaluated independently for EACH vague term.
- The presence of concrete examples for one vague term does NOT automatically resolve other vague terms appearing in the text.

A vague term is considered contextually grounded ONLY IF:
- After full contextual inspection, the nearby text contains CLEAR and SPECIFIC examples of collected data, identifiers, tracking signals, or device-related data.

The examples MUST be:
- Concrete and technical (e.g., IP address, cookie ID, precise geolocation, device identifier)

If the examples are:
- Vague, abstract, or high-level (e.g., "user data", "personal information", "various data", "online activity")

→ They DO NOT count as grounding evidence.

The examples section is illustrative and not exhaustive.
All grounding decisions MUST still satisfy the strict criteria above.

In such cases (when concrete and specific examples exist):
- the term MUST be treated as contextually grounded (NOT vague),
- even if the term itself is linguistically broad.

ONLY AFTER full contextual inspection,
AND only if NO concrete and specific grounding evidence exists,
MUST the term be classified as vague.

---

## 2. "vague_terms"

- List of all terms in "tracking_technique"
  which belong to the vague terms category
  and remain undefined after verifying contextual evidence.

---

## 3. "vague"

- `true` ONLY IF at least one term exists in "vague_terms"
- `false` otherwise

---

## 4. "cookies"

- `true` if the term "cookies" appears explicitly and affirmatively
- `false` otherwise

---

## 5. "Fingerprinting"

- `true` if at least one stateless technique is present in "tracking_technique"
- `false` otherwise

---

## 6. "explanation"

- Provide one short sentence explaining why the groups above were selected.

---

## OUTPUT FORMAT

Return a JSON object with this structure:

{
  "tracking_technique": ["string"],
  "vague_terms": ["string"],
  "vague": boolean,
  "cookies": boolean,
  "Fingerprinting": boolean,
  "explanation": "One short sentence."
}
"""

import pandas as pd

import json
from openai import OpenAI

# Load CSV
df = pd.read_csv('REJECT/250k/common_domains_only_translated.csv')

# Initialize OpenAI client
client = OpenAI(api_key="KEY")

# Target output file
output_file = "REJECT/250k/output.jsonl"


import time

for i, row in df.iterrows():

    website_name = str(row["domains"])
    banner_text = str(row["translated_text"])

    for attempt in range(5):
        try:
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": banner_text}
                ]
            )
            model_output = response.output_text
            break

        except Exception as e:
            print(f"Retry {attempt} at row {i}: {e}")
            time.sleep(3 * (attempt + 1))  # exponential backoff

    else:
        print(f"❌ Skipping row {i}")
        with open("track.txt", "a") as f:
            f.write(website_name + "\n")
        continue
    # Extract model text output safely
    try:
        model_output = response.output_text
    except:
        model_output = ""

    # Create record
    record = {
        "domain": website_name,
        "model_output": model_output
    }

    # Append to existing JSON file
    with open(output_file, "a") as f:
        f.write(json.dumps(record) + "\n")


