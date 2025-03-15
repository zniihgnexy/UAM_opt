import pandas as pd

# Read the CSV files.
df_detailed = pd.read_csv("optimized_results_detailed.csv")
df_mapping = pd.read_csv("optimized_results_with_vertiport_mapping.csv")

# Rename the mapping columns to match the detailed file keys.
df_mapping.rename(columns={"Start_Vertiport": "start", "End_Vertiport": "end"}, inplace=True)

# Merge the two dataframes on the key columns.
merged_df = pd.merge(df_detailed, df_mapping, on=["start", "end"], how="outer", suffixes=("", "_mapping"))

# Optionally, inspect the merged dataframe.
print(merged_df.head())

# Save the merged result to a new CSV file.
merged_df.to_csv("merged_chart.csv", index=False)
print("Merged chart saved to merged_chart.csv")
