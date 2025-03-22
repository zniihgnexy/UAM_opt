import argparse
import os
import pandas as pd
from generate_solution import regenerate_solution
from gurobi_optimization import run_gurobi_optimization
from initialization import initialize_states_with_time
from distance_battery import calculate_distance, battery_consumption_required
from metrics import calculate_coverage_rate, calculate_cost, update_demand_chart
from task_assignment import time_step_path_assignment
from battery_charging import charging_and_battery_update, restore_vehicle_states

# Global variable for unmet demand (list of tuples: (start, end, flow))
unmet_demand = []

def compute_most_needed(unmet_demand_local):
    if not unmet_demand_local:
        return ("", 0)
    need_dict = {}
    for s, e, flow in unmet_demand_local:
        need_dict[e] = need_dict.get(e, 0) + flow
    target = max(need_dict, key=need_dict.get)
    shortage = need_dict[target]
    return (target, shortage)

def redistribute_vehicles(target, shortage, vertiport_states, plane_status, vehicle_states, vehicle_movements,
                          discharge_rate, cost_per_distance):
    from math import inf
    repositioned = 0
    total_added_cost = 0

    candidates = []
    for vehicle_id, status in plane_status.items():
        if status["status"] == "standby" and status["location"] != target:
            source = status["location"]
            if vehicle_states[vehicle_id]["loc"] == source:
                d = calculate_distance(source, target)
                candidates.append((vehicle_id, source, d))
    candidates.sort(key=lambda x: x[2])

    for vehicle_id, source, distance in candidates:
        if shortage <= 0:
            break
        required_battery = battery_consumption_required(distance, discharge_rate)
        if plane_status[vehicle_id]["battery"] >= required_battery:
            prev_location = plane_status[vehicle_id]["location"]
            plane_status[vehicle_id]["status"] = "in_service"
            plane_status[vehicle_id]["location"] = target
            plane_status[vehicle_id]["battery"] -= required_battery
            vehicle_states[vehicle_id]["loc"] = target
            vehicle_states[vehicle_id]["battery"] -= required_battery
            vehicle_states[vehicle_id]["in_service"] = 1
            vehicle_movements[vehicle_id] = (prev_location, target)

            # Update vertiport counts: departure from source and arrival at target
            vertiport_states[source]["avail"] = max(0, vertiport_states[source]["avail"] - 1)
            vertiport_states[source]["in_service"] += 1
            if vertiport_states[target]["in_service"] > 0:
                vertiport_states[target]["in_service"] -= 1
            vertiport_states[target]["avail"] += 1

            repositioned += 1
            shortage -= 1
            reposition_cost = distance * cost_per_distance
            total_added_cost += reposition_cost
    return repositioned, total_added_cost

def load_distance_map(distance_file):
    distance_matrix = pd.read_csv(distance_file, index_col=0)
    vertiports = distance_matrix.columns.tolist()
    distance_map = {}
    for i, start in enumerate(vertiports):
        for j, end in enumerate(vertiports):
            if i != j:
                distance_map[(start, end)] = distance_matrix.loc[start, end]
    return distance_map

def load_gurobi_results(file_path: str, time_step: int):
    data = pd.read_csv(file_path)
    grouped = data.groupby('Time')
    for time, group in grouped:
        if time == f"T{time_step}":
            time_step_results = []
            for _, row in group.iterrows():
                time_step_results.append({
                    "start": row["start"],
                    "end": row["end"],
                    "flow": int(row["flow"]),
                    "distance": float(row["distance"])
                })
            return time_step_results
    return []

def initialize_plane_status_loc(vehicles, vertiports, vehicles_number_each):
    plane_status = {}
    num_vertiports = len(vertiports)
    for i, vertiport in enumerate(vertiports):
        assigned_vehicles = vehicles[i * vehicles_number_each: (i + 1) * vehicles_number_each]
        for vehicle_id in assigned_vehicles:
            plane_status[vehicle_id] = {
                "battery": 100,
                "location": vertiport,
                "origin": vertiport,    # Save the initial location as origin
                "status": "standby",
                "idle_count": 0
            }
    return plane_status

def reset_plane_status(plane_status, vehicle_states, vertiport_states):
    """
    For vehicles that were in service last iteration, return them to their origin.
    Once they complete service (or repositioning), mark them as standby.
    """
    for vehicle_id, status in plane_status.items():
        if status["status"] == "in_service":
            origin = status.get("origin", status["location"])
            status["location"] = origin
            vehicle_states[vehicle_id]["loc"] = origin
            # Once in_service is complete, mark as standby.
            status["status"] = "standby"
            vehicle_states[vehicle_id]["in_service"] = 0
            if origin in vertiport_states:
                if vertiport_states[origin]["in_service"] > 0:
                    vertiport_states[origin]["in_service"] -= 1
                vertiport_states[origin]["avail"] += 1

def calculate_demand_met(gurobi_results, vehicle_movements, current_unmet):
    met_demand = sum(path["flow"] for path in gurobi_results)
    # current_unmet reflects only this iteration's carried unmet demand (before assignment)
    unmet_demand_amount = sum(flow for (_, _, flow) in current_unmet)
    return met_demand, unmet_demand_amount

def mandatory_return_assignment(plane_status, vehicle_states, vertiport_states, discharge_rate):
    """
    For each vehicle that is idle (standby) and not at its origin,
    if it has been away for one round, force a return.
    """
    for vehicle_id, status in plane_status.items():
        if status["status"] == "standby" and status["location"] != status["origin"]:
            status["idle_count"] += 1
            if status["idle_count"] >= 1:  # Force return after one round away
                origin = status["origin"]
                current_loc = status["location"]
                dist = calculate_distance(current_loc, origin)
                battery_needed = battery_consumption_required(dist, discharge_rate)
                if status["battery"] >= battery_needed:
                    status["status"] = "in_service"
                    status["location"] = origin
                    status["battery"] -= battery_needed
                    vehicle_states[vehicle_id]["loc"] = origin
                    vehicle_states[vehicle_id]["battery"] -= battery_needed
                    vehicle_states[vehicle_id]["in_service"] = 1
                    if current_loc in vertiport_states:
                        vertiport_states[current_loc]["avail"] = max(0, vertiport_states[current_loc]["avail"] - 1)
                        vertiport_states[current_loc]["in_service"] += 1
                    if origin in vertiport_states:
                        if vertiport_states[origin]["in_service"] > 0:
                            vertiport_states[origin]["in_service"] -= 1
                        vertiport_states[origin]["avail"] += 1
                    status["idle_count"] = 0

def save_vehicle_states(vehicle_states, plane_status, iteration):
    """
    Save the full state of each vehicle (location, battery, status, etc.)
    into a CSV file inside the folder 'vehicle_states'.
    """
    folder = "vehicle_states"
    if not os.path.exists(folder):
        os.makedirs(folder)
    data = []
    for vehicle_id in vehicle_states:
        state = vehicle_states[vehicle_id]
        p_status = plane_status.get(vehicle_id, {})
        record = {
            "vehicle_id": vehicle_id,
            "location": state.get("loc", ""),
            "battery": state.get("battery", ""),
            "in_service": state.get("in_service", 0),
            "charging": state.get("charging", 0),
            "avail": state.get("avail", 0),
            "status": p_status.get("status", ""),
            "origin": p_status.get("origin", ""),
            "idle_count": p_status.get("idle_count", 0)
        }
        data.append(record)
    df = pd.DataFrame(data)
    df.to_csv(f"{folder}/iteration_{iteration}.csv", index=False)

def run_iterations(num_iterations, vehicle_states, vertiport_states, gurobi_results_per_time, charging_rate,
                   discharge_rate, regenerate_solution, plane_status, distance_map, vertiports):
    global unmet_demand

    all_iteration_records = []
    time_step_summary_records = []
    cumulative_cost = 0  # cumulative overall cost

    for t in range(num_iterations):
        # Start with unmet_demand from previous iteration (carryover) and then clear the "current" values after logging
        current_unmet = unmet_demand.copy()  # this holds the unmet demand carried from previous round
        unmet_demand = []  # clear for the new iteration

        print(f"Time Step {t + 1}")
        restore_vehicle_states(vehicle_states)
        reset_plane_status(plane_status, vehicle_states, vertiport_states)
        vehicle_movements = {vehicle_id: None for vehicle_id in vehicle_states.keys()}

        # First, assign vehicles based on previous unmet demand
        unmet_after_assignment = time_step_path_assignment(
            gurobi_results_per_time[t], vehicle_states, vertiport_states, current_unmet, discharge_rate,
            vehicle_movements, plane_status
        )
        # Calculate met/unmet for this assignment step
        met_demand_assignment, unmet_demand_assignment = calculate_demand_met(gurobi_results_per_time[t], vehicle_movements, current_unmet)

        # Next, run Gurobi optimization to handle new demand and any remaining unmet demand
        gurobi_results, unmet_from_optimization = run_gurobi_optimization(t, unmet_after_assignment, gurobi_results_per_time[t], vertiports)
        # The Gurobi results here are additional assignments for this iteration.
        # Calculate met/unmet for Gurobi part
        met_demand_optimization, unmet_demand_optimization = calculate_demand_met(gurobi_results, vehicle_movements, unmet_after_assignment)

        # The met demand for this iteration is the sum from both assignment steps.
        met_demand_iter = met_demand_assignment + met_demand_optimization
        # The unmet demand for this iteration is ONLY what remains from the optimization
        unmet_demand_iter = unmet_demand_optimization

        # Ensure unmet_demand_iter remains for the next iteration (carried over)
        unmet_demand = unmet_from_optimization

        # Compute iteration cost and update cumulative cost
        iteration_cost = calculate_cost(
            flow_data=gurobi_results,
            cost_per_distance=4,
            distance_map=distance_map
        )
        cumulative_cost += iteration_cost

        # Recalculate vertiport vehicle counts based on current vehicle states
        for v in vertiports:
            standby = sum(1 for vs in vehicle_states.values() if vs["loc"] == v and vs["in_service"] == 0)
            in_service = sum(1 for vs in vehicle_states.values() if vs["loc"] == v and vs["in_service"] == 1)
            vertiport_states[v]["avail"] = standby
            vertiport_states[v]["in_service"] = in_service

        vertiport_tracking = {
            v: (vertiport_states[v].get("avail", 0) + vertiport_states[v].get("in_service", 0))
            for v in vertiports if v in vertiport_states
        }

        # Record metrics for the current iteration (only for this iteration's met and unmet)
        record = {
            "time_step": t + 1,
            "met_demand": met_demand_iter,
            "unmet_demand": unmet_demand_iter,
            "iteration_cost": iteration_cost,
            "cumulative_cost": cumulative_cost,
            "vertiport_counts": vertiport_tracking
        }
        all_iteration_records.append(record)
        time_step_summary_records.append(record)

        # Optionally, reposition vehicles if there is a shortage (not affecting met/unmet metrics)
        target, shortage = compute_most_needed(unmet_demand)
        if target and shortage > 0:
            repositioned, added_cost = redistribute_vehicles(target, shortage, vertiport_states, plane_status,
                                                              vehicle_states, vehicle_movements,
                                                              discharge_rate, cost_per_distance=4)
            iteration_cost += added_cost
            cumulative_cost += added_cost

        # Update vehicle charging; fully charged vehicles become standby for the next iteration
        charging_and_battery_update(vehicle_states, time_interval=1, charging_rate=charging_rate)

        # Save current vehicle state snapshot
        save_vehicle_states(vehicle_states, plane_status, t + 1)

    # Save detailed iteration metrics to CSV file "detail.csv"
    detail_df = pd.DataFrame(time_step_summary_records)
    detail_df.to_csv("detail.csv", index=False)
    print("All iteration records saved to detail.csv")

    return all_iteration_records, time_step_summary_records, cumulative_cost

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vertiports_file", default="adjusted_vertiports_numeric.csv")
    parser.add_argument("--distance_file", default="distance_matrix.csv")
    parser.add_argument("--gurobi_results_file", default="updated_flow_data_with_corrected_distances.csv")
    args = parser.parse_args()

    vertiports_df = pd.read_csv(args.vertiports_file)
    vertiports = vertiports_df["Vertiport"].tolist()
    distance_map = load_distance_map(args.distance_file)
    gurobi_results_per_time = []
    total_time_steps = 500  # Set number of iterations as needed
    for t in range(total_time_steps):
        gurobi_results = load_gurobi_results(args.gurobi_results_file, t)
        gurobi_results_per_time.append(gurobi_results)

    global_time_step_records = []
    results = []

    charging_rates = [30, 35, 40]
    discharge_rates = [1, 3, 5]
    vehicle_counts = [10, 15, 20]

    for charging_rate in charging_rates:
        for discharge_rate in discharge_rates:
            for vehicles_number_each in vehicle_counts:
                vehicles = ["V" + str(i) for i in range(1, vehicles_number_each * len(vertiports) + 1)]
                vehicle_states, vertiport_states = initialize_states_with_time(vehicles, vertiports, vehicles_number_each)
                plane_status = initialize_plane_status_loc(vehicles, vertiports, vehicles_number_each)
                for vertiport in vertiports:
                    vertiport_states[vertiport]["activated"] = True

                unmet_demand = []
                all_iteration_records, time_step_summary_records, cumulative_cost = run_iterations(
                    num_iterations=500,
                    vehicle_states=vehicle_states,
                    vertiport_states=vertiport_states,
                    gurobi_results_per_time=gurobi_results_per_time,
                    charging_rate=charging_rate,
                    discharge_rate=discharge_rate,
                    regenerate_solution=regenerate_solution,
                    plane_status=plane_status,
                    distance_map=distance_map,
                    vertiports=vertiports
                )

                coverage_rate = (sum(rec["met_demand"] for rec in time_step_summary_records) /
                                 sum(rec["met_demand"] + rec["unmet_demand"] for rec in time_step_summary_records)) if time_step_summary_records else 0
                total_cost = cumulative_cost

                results.append({
                    "charging_rate": charging_rate,
                    "discharge_rate": discharge_rate,
                    "vehicle_count": vehicles_number_each,
                    "coverage_rate": coverage_rate,
                    "cumulative_cost": total_cost
                })

                details_df = pd.DataFrame(all_iteration_records)
                details_filename = f"experiment_details_charging{charging_rate}_discharge{discharge_rate}_vehicles{vehicles_number_each}.csv"
                details_filepath = os.path.join("detail_csv", details_filename)
                details_df.to_csv(details_filepath, index=False)

                for record in time_step_summary_records:
                    record["charging_rate"] = charging_rate
                    record["discharge_rate"] = discharge_rate
                    record["vehicle_count"] = vehicles_number_each
                    global_time_step_records.append(record)

    df = pd.DataFrame(results)
    df.to_csv("sensitivity_analysis_results.csv", index=False)
    print("Overall experiment results saved to sensitivity_analysis_results.csv")

    detail_df = pd.DataFrame(global_time_step_records)
    detail_df.to_csv("detail.csv", index=False)
    print("All iteration records saved to detail.csv")

# run the draw.py file afterwards to visualize the results
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
