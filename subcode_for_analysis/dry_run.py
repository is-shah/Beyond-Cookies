import pandas as pd 
df = pd.read_csv('/home/subcode/REJECT/1M/common_domains_only_translated.csv')
print(df['domains'].nunique())
# import pandas as pd

# # ==========================
# # FILE PATHS
# # ==========================

# csv_file = "common_domains_only_translated.csv"
# txt_file = "Accessible_domains.txt"

# # Output file
# output_file = "missing_domains.txt"

# # ==========================
# # READ CSV DOMAINS
# # ==========================

# df = pd.read_csv(csv_file)

# csv_domains = set(
#     df["domains"]
#     .dropna()
#     .astype(str)
#     .str.strip()
# )

# print(f"Domains in CSV: {len(csv_domains)}")

# # ==========================
# # READ TXT DOMAINS
# # ==========================

# with open(txt_file, "r", encoding="utf-8") as f:

#     txt_domains = set(
#         line.strip()
#         for line in f
#         if line.strip()
#     )

# print(f"Domains in TXT: {len(txt_domains)}")

# # ==========================
# # FIND DOMAINS IN TXT
# # BUT NOT IN CSV
# # ==========================

# missing_domains = sorted(
#     txt_domains - csv_domains
# )

# print(
#     f"Domains in TXT not in CSV: {len(missing_domains)}"
# )

# for d in missing_domains:
#     print(d)

# # ==========================
# # SAVE RESULT
# # ==========================

# with open(
#     output_file,
#     "w",
#     encoding="utf-8"
# ) as f:

#     for d in missing_domains:
#         f.write(d + "\n")

# print(
#     f"Saved to {output_file}"
# )