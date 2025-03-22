import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the new detail CSV file
# df = pd.read_csv('detail.csv')

# read files from folder
import glob
import os
for file in glob.glob("detail_csv/*.csv"):
    print(file)
    df = pd.read_csv(file)

    # If assignment_ratio is missing, compute it as met_demand / (met_demand + unmet_demand)
    if 'assignment_ratio' not in df.columns:
        df['assignment_ratio'] = df.apply(lambda row: row['met_demand'] / (row['met_demand'] + row['unmet_demand'])
                                        if (row['met_demand'] + row['unmet_demand']) != 0 else 0, axis=1)

    # If big_picture_assignment_ratio is missing and real_flow exists, compute it similarly
    if 'big_picture_assignment_ratio' not in df.columns and 'real_flow' in df.columns:
        df['big_picture_assignment_ratio'] = df.apply(lambda row: row['met_demand'] / row['real_flow']
                                                    if row['real_flow'] != 0 else 0, axis=1)
    elif 'big_picture_assignment_ratio' not in df.columns:
        # Otherwise, default to assignment_ratio if real_flow is not present
        df['big_picture_assignment_ratio'] = df['assignment_ratio']

    # Display a preview of the data
    print("Data Preview:")
    print(df.head())

    # Construct a summary paragraph describing key parameters
    # summary = (
    #     f"The dataset spans {df['time_step'].nunique()} time steps and includes several key performance indicators. "
    #     f"It tracks the cumulative cost incurred at each time step as well as the cost added per iteration (iteration_cost). "
    #     f"Operational performance is captured by the met_demand (fulfilled orders) and unmet_demand (orders left unfulfilled). "
    #     f"Assignment performance is recorded by the assignment_ratio and big_picture_assignment_ratio. "
    #     f"Additional parameters include a constant charging rate of {df['charging_rate'].iloc[0]} and a discharge rate of {df['discharge_rate'].iloc[0]}, "
    #     f"with the fleet comprising {df['vehicle_count'].iloc[0]} vehicles."
    # )
    # print("\nSummary of the Dataset:")
    # print(summary)

    # Create directory for figures if it doesn't exist
    file_name = os.path.basename(file)
    file_name = file_name.split('.')[0]
    folder_path = 'figure' + file_name
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Set plot style
    plt.style.use('seaborn-v0_8-paper')

    # 1. Line Plot: Cumulative Cost, Iteration Cost, Met Demand, and Unmet Demand Over Time
    plt.figure(figsize=(12, 8))
    plt.plot(df['time_step'], df['cumulative_cost'], marker='o', label='Cumulative Cost')
    plt.plot(df['time_step'], df['iteration_cost'], marker='s', label='Iteration Cost')
    plt.plot(df['time_step'], df['met_demand'], marker='^', label='Met Demand')
    plt.plot(df['time_step'], df['unmet_demand'], marker='d', label='Unmet Demand')
    plt.title('Operational Metrics Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Cost / Demand')
    plt.legend()
    plt.tight_layout()
    plt.savefig(folder_path + '/line_plot_operational_metrics.png')
    # plt.show()

    # 2. Scatter Plot: Time vs Assignment Ratio
    plt.figure(figsize=(10, 6))
    plt.scatter(df['time_step'], df['assignment_ratio'], c='blue', edgecolor='k', alpha=0.7)
    plt.title('Assignment Ratio Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Assignment Ratio')
    plt.tight_layout()
    plt.savefig(folder_path  + '/scatter_assignment_ratio.png')
    # plt.show()

    # 3. Bar Plot: Charging Rate and Discharge Rate
    # rates = {'Charging Rate': df['charging_rate'].iloc[0], 'Discharge Rate': df['discharge_rate'].iloc[0]}
    # plt.figure(figsize=(6, 6))
    # plt.bar(list(rates.keys()), list(rates.values()), color=['skyblue', 'salmon'], edgecolor='black')
    # plt.title('Charging vs Discharge Rate')
    # plt.ylabel('Rate')
    # plt.tight_layout()
    # plt.savefig('figure/bar_rates.png')
    # plt.show()

    # 4. Histogram: Distribution of Cumulative Cost and Iteration Cost
    plt.figure(figsize=(12, 6))
    plt.hist(df['cumulative_cost'], bins=10, edgecolor='black', alpha=0.7, label='Cumulative Cost')
    plt.hist(df['iteration_cost'], bins=10, edgecolor='black', alpha=0.7, label='Iteration Cost')
    plt.title('Distribution of Cumulative and Iteration Costs')
    plt.xlabel('Cost')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.savefig(folder_path + '/hist_costs.png')
    # plt.show()

    # 5. Box Plot: Cumulative Cost by Time Step
    plt.figure(figsize=(12, 6))
    sns.boxplot(x=df['time_step'], y=df['cumulative_cost'])
    plt.title('Box Plot of Cumulative Cost by Time Step')
    plt.xlabel('Time Step')
    plt.ylabel('Cumulative Cost')
    plt.tight_layout()
    plt.savefig(folder_path + '/boxplot_cumulative_cost.png')
    # plt.show()

    # 6. Line Plot: Demand Trends Over Time (Real Flow, Met Demand, Unmet Demand)
    plt.figure(figsize=(12, 8))
    if 'real_flow' in df.columns:
        plt.plot(df['time_step'], df['real_flow'], marker='o', label='Real Flow (Total Demand)')
    plt.plot(df['time_step'], df['met_demand'], marker='s', label='Met Demand')
    plt.plot(df['time_step'], df['unmet_demand'], marker='^', label='Unmet Demand')
    plt.title('Demand Trends Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Demand')
    plt.legend()
    plt.tight_layout()
    plt.savefig(folder_path + '/line_plot_demand_trends.png')
    # plt.show()

    # 7. Line Plot: Assignment Ratios Over Time
    plt.figure(figsize=(12, 8))
    plt.plot(df['time_step'], df['assignment_ratio'], marker='o', label='Assignment Ratio')
    plt.plot(df['time_step'], df['big_picture_assignment_ratio'], marker='s', label='Big Picture Assignment Ratio')
    plt.title('Assignment Ratios Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Ratio')
    plt.legend()
    plt.tight_layout()
    plt.savefig(folder_path + '/line_plot_assignment_ratios.png')
    # plt.show()

    # 8. Correlation Heatmap: Key Numeric Metrics
    numeric_cols = ['cumulative_cost', 'iteration_cost', 'met_demand', 'unmet_demand', 'assignment_ratio', 'big_picture_assignment_ratio']
    if 'real_flow' in df.columns:
        numeric_cols.append('real_flow')
    corr = df[numeric_cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Heatmap of Key Metrics')
    plt.tight_layout()
    plt.savefig(folder_path + '/heatmap_metrics.png')
    # plt.show()

    # 9. Pair Plot: Explore Relationships Between Key Metrics
    try:
        sns.pairplot(df[numeric_cols])
        plt.suptitle('Pair Plot of Key Metrics', y=1.02)
        plt.tight_layout()
        plt.savefig(folder_path + '/pairplot_metrics.png')
        # plt.show()
    except Exception as e:
        print("Pair plot could not be generated:", e)
