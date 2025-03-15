#!/usr/bin/env python
import pandas as pd
from simulation import (
    load_distance_map,
    load_gurobi_results,
    initialize_states_with_time,
    initialize_plane_status_loc,
    run_iterations,
    calculate_coverage_rate,
    regenerate_solution
)

# ---------------------------
# File paths and basic inputs
# ---------------------------
distance_file = "distance_matrix.csv"
gurobi_results_file = "updated_flow_data_with_corrected_distances.csv"
vertiports_file = "adjusted_vertiports_numeric.csv"

# Load the distance map and full list of vertiports
distance_map = load_distance_map(distance_file)
vertiports_df = pd.read_csv(vertiports_file)
all_vertiports = vertiports_df["Vertiport"].tolist()

# ---------------------------
# Pre-load Gurobi results
# ---------------------------
# For simplicity in the case study, we run a small number of iterations.
total_time_steps = 5  # You can adjust this as needed
gurobi_results_per_time = []
for t in range(total_time_steps):
    gr_results = load_gurobi_results(gurobi_results_file, t)
    gurobi_results_per_time.append(gr_results)

# ---------------------------
# Default simulation parameters
# ---------------------------
default_vehicles_per_vertiport = 10
default_charging_rate = 40   # e.g., in kWh/min or your chosen unit
default_discharge_rate = 0.1

# This list will store our results for further analysis
results = []

# ---------------------------
# Experiment 1: Vary the number of vertiports
# ---------------------------
# Here we use different counts of vertiports (by selecting the first N from the full list)
vertiport_counts = [5, 10, 15]  # Example values; adjust as desired
for count in vertiport_counts:
    # Select a subset of the vertiports
    selected_vertiports = all_vertiports[:count]
    # Make sure that the simulation functions (e.g., run_gurobi_optimization) see the correct list.
    # (This script assumes that the simulation code uses the global variable "vertiports".)
    globals()['vertiports'] = selected_vertiports

    # Create vehicles based on the current number of vertiports
    vehicles = ["V" + str(i) for i in range(1, default_vehicles_per_vertiport * len(selected_vertiports) + 1)]
    vehicle_states, vertiport_states = initialize_states_with_time(vehicles, selected_vertiports, default_vehicles_per_vertiport)
    plane_status = initialize_plane_status_loc(vehicles, selected_vertiports, default_vehicles_per_vertiport)

    # Activate all vertiports
    for vp in selected_vertiports:
        vertiport_states[vp]["activated"] = True

    # Run the simulation
    total_met_demand, total_demand = run_iterations(
        num_iterations=total_time_steps,
        vehicle_states=vehicle_states,
        vertiport_states=vertiport_states,
        gurobi_results_per_time=gurobi_results_per_time,
        charging_rate=default_charging_rate,
        discharge_rate=default_discharge_rate,
        regenerate_solution=regenerate_solution,
        plane_status=plane_status,
        distance_map=distance_map,
        vertiports=selected_vertiports
    )
    coverage_rate = calculate_coverage_rate(total_met_demand, total_demand)
    
    # Save the experiment result (add cost calculation if needed)
    results.append({
        "experiment": "vertiports_count",
        "parameter_value": count,
        "coverage_rate": coverage_rate
    })

# # ---------------------------
# # Experiment 2: Vary the number of vehicles per vertiport
# # ---------------------------
# # Here we keep all vertiports and change the number of vehicles at each vertiport.
# vehicle_counts = [5, 10, 15]  # Example values
# # Use the full list of vertiports
# selected_vertiports = all_vertiports
# globals()['vertiports'] = selected_vertiports

# for vehicles_per in vehicle_counts:
#     vehicles = ["V" + str(i) for i in range(1, vehicles_per * len(selected_vertiports) + 1)]
#     vehicle_states, vertiport_states = initialize_states_with_time(vehicles, selected_vertiports, vehicles_per)
#     plane_status = initialize_plane_status_loc(vehicles, selected_vertiports, vehicles_per)

#     # Activate all vertiports
#     for vp in selected_vertiports:
#         vertiport_states[vp]["activated"] = True

#     total_met_demand, total_demand = run_iterations(
#         num_iterations=total_time_steps,
#         vehicle_states=vehicle_states,
#         vertiport_states=vertiport_states,
#         gurobi_results_per_time=gurobi_results_per_time,
#         charging_rate=default_charging_rate,
#         discharge_rate=default_discharge_rate,
#         regenerate_solution=regenerate_solution,
#         plane_status=plane_status,
#         distance_map=distance_map
#     )
#     coverage_rate = calculate_coverage_rate(total_met_demand, total_demand)
#     results.append({
#         "experiment": "vehicles_per_vertiport",
#         "parameter_value": vehicles_per,
#         "coverage_rate": coverage_rate
#     })

# # ---------------------------
# # Experiment 3: Vary the charging rate
# # ---------------------------
# # Here we keep the full set of vertiports and the default number of vehicles per vertiport, while varying the charging rate.
# charging_rates = [20, 40, 60]  # Example values
# for ch_rate in charging_rates:
#     vehicles = ["V" + str(i) for i in range(1, default_vehicles_per_vertiport * len(selected_vertiports) + 1)]
#     vehicle_states, vertiport_states = initialize_states_with_time(vehicles, selected_vertiports, default_vehicles_per_vertiport)
#     plane_status = initialize_plane_status_loc(vehicles, selected_vertiports, default_vehicles_per_vertiport)

#     # Activate all vertiports
#     for vp in selected_vertiports:
#         vertiport_states[vp]["activated"] = True

#     total_met_demand, total_demand = run_iterations(
#         num_iterations=total_time_steps,
#         vehicle_states=vehicle_states,
#         vertiport_states=vertiport_states,
#         gurobi_results_per_time=gurobi_results_per_time,
#         charging_rate=ch_rate,
#         discharge_rate=default_discharge_rate,
#         regenerate_solution=regenerate_solution,
#         plane_status=plane_status,
#         distance_map=distance_map
#     )
#     coverage_rate = calculate_coverage_rate(total_met_demand, total_demand)
#     results.append({
#         "experiment": "charging_rate",
#         "parameter_value": ch_rate,
#         "coverage_rate": coverage_rate
#     })

# ---------------------------
# Save the case study results to a CSV file
# ---------------------------
results_df = pd.DataFrame(results)
results_df.to_csv("case_study_results.csv", index=False)
print("Case study simulation completed. Results saved to 'case_study_results.csv'.")
