import pandas as pd
import requests
import time
import cld3
import os

df1 = pd.read_csv("REJECT/750k/banner_details.csv")

# df2 = pd.read_csv(
#     "REJECT/1M/banner_details_2.csv",
#     skiprows=1,
#     names=df1.columns
# )

# df = pd.concat([df1, df2], ignore_index=True)

df = df1.drop_duplicates(subset=["domains"])
df = df[['domains', 'text']]

cache = {}

output_file = "REJECT/750k/common_domains_only_translated.csv"

def translate_text(text,index, source="auto", target="en", retries=3):
    if pd.isna(text) or str(text).strip() == "":
        return ""

    text = str(text)

    if text in cache:
        return cache[text]

    url = "http://localhost:5000/translate"

    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, data=payload, timeout=30)

            if response.status_code == 200:
                translated = response.json().get("translatedText", "")
                cache[text] = translated
                return translated

        except Exception as e:
            print(f"Error on attempt {attempt+1}: {e} - {index}")

        time.sleep(2 * (attempt + 1))

    return ""

def detect_lang(text):
    if not isinstance(text, str) or text.strip() == "":
        return None
    try:
        detected_obj = cld3.get_language(text)
        return detected_obj.language if detected_obj else None
    except:
        return None


count = 0

# Write header once
if not os.path.exists(output_file):
    pd.DataFrame(columns=list(df.columns) + ["translated_text"]).to_csv(
        output_file, index=False
    )

texts = df["text"].tolist()

for i, text in enumerate(texts):
    lang = detect_lang(text)

    print(f"[{i}] Lang: {lang} | Text: {str(text)[:40]}")

    if lang == 'en':
        print("→ Skipping (English)")
        count = count + 1
        translated = text
    else:
        print("→ Translating...")
        translated = translate_text(text, i)
        print(f"→ Result: {translated[:40]}")

    # Save immediately instead of storing in RAM
    row = df.iloc[[i]].copy()
    row["translated_text"] = translated

    row.to_csv(
        output_file,
        mode='a',
        header=False,
        index=False
    )

    time.sleep(1)

print(f"Total English Websites - {count}")
print("Done ✅")