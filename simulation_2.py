import argparse
import json
import pandas as pd
from generate_solution import regenerate_solution
from gurobi_optimization import run_gurobi_optimization
from initialization import initialize_states_with_time
from distance_battery import calculate_distance, battery_consumption_required
from metrics import calculate_coverage_rate, calculate_cost, update_demand_chart
from task_assignment import time_step_path_assignment
from battery_charging import charging_and_battery_update, restore_vehicle_states

# Global variable for unmet demand
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
    for vehicle_id, status in plane_status.items():
        origin = status.get("origin", status["location"])
        status["location"] = origin
        vehicle_states[vehicle_id]["loc"] = origin
        if status["status"] == "in_service":
            status["status"] = "standby" if status["battery"] >= 20 else "charging"
            vehicle_states[vehicle_id]["in_service"] = 0
            if origin in vertiport_states:
                vertiport_states[origin]["in_service"] = max(0, vertiport_states[origin]["in_service"] - 1)
                if status["status"] == "standby":
                    vertiport_states[origin]["avail"] = max(0, vertiport_states[origin]["avail"] + 1)

def calculate_demand_met(gurobi_results, vehicle_movements, unmet_demand_local):
    total_met_demand = 0
    total_demand = 0
    current_demand = [
        {"start": start, "end": end, "flow": flow}
        for start, end, flow in unmet_demand_local
    ] + gurobi_results
    for route in current_demand:
        start, end, required_demand = route["start"], route["end"], route["flow"]
        total_demand += required_demand
        vehicles_on_route = sum(
            1 for vehicle_id, movement in vehicle_movements.items()
            if movement == (start, end)
        )
        met_demand = min(required_demand, vehicles_on_route)
        total_met_demand += met_demand
    return total_met_demand, total_demand

def mandatory_return_assignment(plane_status, vehicle_states, vertiport_states, discharge_rate):
    """
    For each vehicle that is idle (standby) and is not at its origin,
    increment its idle_count. If the idle_count reaches 2 (i.e. the vehicle has stayed away
    for two consecutive iterations), assign it to return to its origin immediately.
    This assignment bypasses gurobi and is mandatory.
    """
    for vehicle_id, status in plane_status.items():
        if status["status"] == "standby" and status["location"] != status["origin"]:
            status["idle_count"] += 1
            if status["idle_count"] >= 2:
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
                    vertiport_states[current_loc]["avail"] = max(0, vertiport_states[current_loc]["avail"] - 1)
                    vertiport_states[current_loc]["in_service"] += 1
                    if vertiport_states[origin]["in_service"] > 0:
                        vertiport_states[origin]["in_service"] -= 1
                    vertiport_states[origin]["avail"] += 1
                    status["idle_count"] = 0

def run_iterations(num_iterations, vehicle_states, vertiport_states, gurobi_results_per_time, charging_rate,
                   discharge_rate, regenerate_solution, plane_status, distance_map, vertiports):
    global unmet_demand

    gurobi_results = []
    all_iteration_records = []
    time_step_summary_records = []

    for t in range(num_iterations):
        unmet_for_calc = unmet_demand.copy()
        unmet_demand = []
        print(f"Time Step {t + 1}")
        restore_vehicle_states(vehicle_states)
        reset_plane_status(plane_status, vehicle_states, vertiport_states)
        vehicle_movements = {vehicle_id: None for vehicle_id in vehicle_states.keys()}

        new_unmet, fulfill, _ = time_step_path_assignment(
            gurobi_results, vehicle_states, vertiport_states, unmet_for_calc, discharge_rate,
            vehicle_movements, plane_status
        )
        unmet_demand = new_unmet

        total_unmet = sum(flow for (_, _, flow) in new_unmet)

        real_flow = update_demand_chart([], gurobi_results_per_time[t])
        gurobi_results, unmet_from_optimization = run_gurobi_optimization(t, unmet_demand, gurobi_results_per_time[t], vertiports)
        unmet_demand = unmet_from_optimization

        assignment_ratio = fulfill / (fulfill + total_unmet) if (fulfill + total_unmet) > 0 else 0
        big_picture_assignment_ratio = fulfill / real_flow if real_flow > 0 else 0

        total_met_demand, _ = calculate_demand_met(gurobi_results, vehicle_movements, unmet_demand)
        total_cost = calculate_cost(
            flow_data=gurobi_results,
            cost_per_distance=4,
            distance_map=distance_map
        )
        print(f"Time Step {t+1}: Assignment Ratio: {assignment_ratio:.2f}, Big Picture Ratio: {big_picture_assignment_ratio:.2f}, Total Cost: {total_cost:.2f}")

        mandatory_return_assignment(plane_status, vehicle_states, vertiport_states, discharge_rate)
        
        for v in vertiports:
            standby = sum(1 for vs in vehicle_states.values() if vs["loc"] == v and vs["in_service"] == 0)
            in_service = sum(1 for vs in vehicle_states.values() if vs["loc"] == v and vs["in_service"] == 1)
            vertiport_states[v]["avail"] = standby
            vertiport_states[v]["in_service"] = in_service

        vertiport_tracking = {
            v: (vertiport_states[v].get("avail", 0) + vertiport_states[v].get("in_service", 0))
            for v in vertiports if v in vertiport_states
        }

        record = {
            "time_step": t + 1,
            "total_cost": total_cost,
            "fulfill": fulfill,
            "unfulfill": total_unmet,
            "real_flow": real_flow,
            "assignment_ratio": assignment_ratio,
            "big_picture_assignment_ratio": big_picture_assignment_ratio,
            "income_flow": total_met_demand,
            "vertiport_counts": vertiport_tracking
        }
        all_iteration_records.append(record)
        time_step_summary_records.append(record)

        target, shortage = compute_most_needed(unmet_demand)
        if target:
            current_target_count = vertiport_states[target]["avail"] + vertiport_states[target]["in_service"]
            if shortage > 0:
                repositioned, added_cost = redistribute_vehicles(target, shortage, vertiport_states, plane_status,
                                                                  vehicle_states, vehicle_movements,
                                                                  discharge_rate, cost_per_distance=4)

        charging_and_battery_update(vehicle_states, time_interval=1, charging_rate=charging_rate)

    return total_met_demand, real_flow, all_iteration_records, time_step_summary_records

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
    total_time_steps = 500
    for t in range(total_time_steps):
        gurobi_results = load_gurobi_results(args.gurobi_results_file, t)
        gurobi_results_per_time.append(gurobi_results)

    global_time_step_records = []
    results = []

    charging_rates = [40]
    discharge_rates = [1]
    vehicle_counts = [15]

    for charging_rate in charging_rates:
        for discharge_rate in discharge_rates:
            for vehicles_number_each in vehicle_counts:
                vehicles = ["V" + str(i) for i in range(1, vehicles_number_each * len(vertiports) + 1)]
                vehicle_states, vertiport_states = initialize_states_with_time(vehicles, vertiports, vehicles_number_each)
                plane_status = initialize_plane_status_loc(vehicles, vertiports, vehicles_number_each)
                for vertiport in vertiports:
                    vertiport_states[vertiport]["activated"] = True

                unmet_demand = []
                total_met_demand, real_flow, iteration_records, time_step_summary_records = run_iterations(
                    num_iterations=20,
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

                coverage_rate = calculate_coverage_rate(total_met_demand, real_flow)
                total_cost = calculate_cost(gurobi_results, cost_per_distance=2, distance_map=distance_map)

                results.append({
                    "charging_rate": charging_rate,
                    "discharge_rate": discharge_rate,
                    "vehicle_count": vehicles_number_each,
                    "coverage_rate": coverage_rate,
                    "total_cost": total_cost
                })

                details_df = pd.DataFrame(iteration_records)
                details_filename = f"experiment_details_charging{charging_rate}_discharge{discharge_rate}_vehicles{vehicles_number_each}.csv"
                details_df.to_csv(details_filename, index=False)

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
    print("All time step records saved to detail.csv")
