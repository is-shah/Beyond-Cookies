import pandas as pd

# CSV files
file1 = "/home/isshah/Access/ShadowMap/subcode_for_analysis/Accept/js.csv"
file2 = "/home/isshah/Access/ShadowMap/subcode_for_analysis/Reject/js.csv"

# Read files
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Merge by appending rows
merged_df = pd.concat(
    [df1, df2],
    ignore_index=True
)

# Save merged file
merged_df.to_csv(
    "merged_js.csv",
    index=False
)

print("✓ Merged successfully")
print(f"Total rows: {len(merged_df)}")

