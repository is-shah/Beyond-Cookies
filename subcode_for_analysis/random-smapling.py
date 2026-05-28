import pandas as pd

# Input CSV file
input_file = "common_domains_only_translated.csv"

# Output file
output_file = "random_100.csv"

# Load CSV
df = pd.read_csv(input_file)

# Pick 100 random rows
random_df = df.sample(n=100, random_state=42)

# Save to new CSV
random_df.to_csv(output_file, index=False)

print(f"Saved {len(random_df)} rows to {output_file}")