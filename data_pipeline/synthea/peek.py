import pandas as pd

# Load the raw synthetic data
df = pd.read_csv("output/csv/conditions.csv")

# Print the top 10 most common codes so we know what to map
print("--- Top 10 Codes found in your synthetic data ---")
print(df['CODE'].value_counts().head(10))