import os
import time

SYSTEM_PROMPT = """ You are an expert in web tracking techniques and privacy-policy analysis.
                    ### TASK — Extract Tracking Details
                    Carefully analyze the provided cookie-banner text and extract the following fields :
                    1. **"tracking technique"**
                      - List all tracking mechanisms or categories explicitly mentioned.
                      - Normalize all terms to lowercase.
                      - Include a term only if it meets ALL conditions:
                          1. It appears explicitly in the text.
                          2. It is described as being used or potentially used.
                          3. It is *not* mentioned only in a negated/denial context.
                      - Allowed technique groups (include only when explicitly named):
                          • **Stateful Tracking(Targeting Cookies):** "cookies", "local storage", "session storage"
                          • **Fingerprinting(Stateless Method):** "device scanning", "device identifiers","precise geolocation", "ip address"
                          • **Vague terms:** "tracking technologies", "similar technologies",
                            "technologies", "trackers", "tracers", "personal data", "browsing data"
                    2. **"vague"**
                      - `true` if any vague/generalized terms appear in the `"tracking technique"` list.
                      - `false` otherwise.
                    3. **"cookies"**
                      - `true` if the term **"cookies"** appears explicitly and affirmatively.
                      - `false` otherwise.
                    4. **"Fingerprinting"**
                      - `true` if at least one stateless technique is present in the `"tracking technique"` list.
                      - `false` otherwise.
                    5. **"explanation"**
                      - Provide one short sentence explaining why the categories above were selected.
                    ### OUTPUT FORMAT
                    Return a JSON object with this structure:
                    { 
                      "tracking_technique": ["string"],
                      "vague": boolean,
                      "cookies": boolean,
                      "Fingerprinting": boolean,
                      "explanation": "One short sentence."
                    }
                """


import pandas as pd
import os
import json
from openai import OpenAI

# Load CSV
df = pd.read_csv('common_domains_only_translated.csv')

# Initialize OpenAI client
client = OpenAI(api_key="KEY")

# Target output file
output_file = "old_total.jsonl"


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


