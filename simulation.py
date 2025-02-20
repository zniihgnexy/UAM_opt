from generate_solution import regenerate_solution
from initialization import initialize_states_with_time
from distance_battery import calculate_distance
from metrics import calculate_coverage_rate, calculate_cost, update_demand_chart
from task_assignment import time_step_path_assignment
from battery_charging import charging_and_battery_update, restore_vehicle_states
import pandas as pd
import argparse
def load_distance_map(distance_file):
    """加载距离矩阵并生成 distance_map"""
    distance_matrix = pd.read_csv(distance_file, index_col=0)
    vertiports = distance_matrix.columns.tolist()
    distance_map = {}
    for i, start in enumerate(vertiports):
        for j, end in enumerate(vertiports):
            if i != j:
                distance_map[(start, end)] = distance_matrix.loc[start, end]
    return distance_map

def load_gurobi_results(file_path: str, time_step: int):
    """Load Gurobi results from a CSV file and convert them to list format."""
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



# Plane Status Initialization and Management
def initialize_plane_status_loc(vehicles, vertiports):
    """Initialize the plane status for all vehicles at the starting location."""
    return {
        vehicle_id: {
            "battery": 100,
            # same number of vehicles at each vertiport
            "location": vertiports[i % len(vertiports)],
            "status": "standby"  # Possible statuses: "standby", "in_service", "charging"
        }
        for i, vehicle_id in enumerate(vehicles)
    }

def reset_plane_status(plane_status):
    """Reset the status of planes after each iteration."""
    for vehicle_id, status in plane_status.items():
        if status["status"] == "in_service":
            status["status"] = "standby"  # Planes become standby after completing service
        elif status["battery"] < 100:
            status["status"] = "charging"  # Planes with low battery are set to charging

# Main Simulation Functions
def calculate_demand_met(gurobi_results, vehicle_movements, unmet_demand):
    """Calculate the met demand for the current iteration."""
    total_met_demand = 0
    total_demand = 0

    current_demand = [
        {"start": start, "end": end, "flow": flow}
        for start, end, flow in unmet_demand
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

# def run_iterations(num_iterations, vehicle_states, vertiport_states, gurobi_results_per_time, charging_rate,
#                    discharge_rate, regenerate_solution, plane_status):
#     unmet_demand = []
#     flag = 0  # Initialize flag
#     stuck_iteration = 0
#
#     for t in range(num_iterations):
#         iteration_complete = False
#
#         while not iteration_complete and stuck_iteration < 5:
#             print(f"Time Step {t + 1}")
#
#             # Step 0: Restore vehicle states and reset plane statuses
#             restore_vehicle_states(vehicle_states)
#             reset_plane_status(plane_status)
#
#             # Initialize movement tracking for this timestep
#             vehicle_movements = {vehicle_id: None for vehicle_id in vehicle_states.keys()}
#
#             # Step 1: Update total demand
#             # Step 1: Update total demand
#
#
#
#             if isinstance(gurobi_results_per_time[t], dict):
#                 gurobi_results_per_time[t] = [gurobi_results_per_time[t]]
#
#
#             total_demand = update_demand_chart(unmet_demand, gurobi_results_per_time[t])
#
#             # Step 2: Assign vehicles to tasks
#             if flag == 1:
#                 print("Flag set: Retrieving second-best solution from Gurobi.")
#                 gurobi_results = regenerate_solution(t, unmet_demand, vehicle_states, vertiport_states, gurobi_results, True)
#                 flag = 0
#             else:
#                 gurobi_results = gurobi_results_per_time[t] + [
#                     {"start": start, "end": end, "flow": needed, "distance": calculate_distance(start, end)}
#                     for start, end, needed in unmet_demand
#                 ]
#
#             unmet_demand.clear()
#
#             time_step_path_assignment(
#                 gurobi_results, vehicle_states, vertiport_states, unmet_demand, discharge_rate,
#                 vehicle_movements, plane_status
#             )
#
#             # Step 3: Calculate demand metrics
#             total_met_demand, total_demand = calculate_demand_met(gurobi_results, vehicle_movements, unmet_demand)
#             coverage_rate = calculate_coverage_rate(total_met_demand, total_demand)
#             print(f"Current Coverage Rate: {coverage_rate:.2f}")
#
#             activated_vertiports = [v for v, state in vertiport_states.items() if state["activated"]]
#             total_cost = calculate_cost(activated_vertiports, cost_per_distance=10, distance_map={
#                 ("P1", "P2"): 50, ("P2", "P3"): 80, ("P3", "P1"): 60, ("P1", "P3"): 30
#             })
#             print(f"Current Total Cost: {total_cost:.2f}")
#
#             # Print detailed vehicle states
#             print("\nDetailed Vehicle States:")
#             for vehicle_id, state in vehicle_states.items():
#                 print(f"  {vehicle_id}: {state}")
#
#             # Print plane statuses
#             print("\nPlane Statuses:")
#             for plane_id, status in plane_status.items():
#                 print(f"  {plane_id}: {status}")
#
#             # Print movement and other states
#             print("\nVehicle Movements:")
#             for vehicle_id, movement in vehicle_movements.items():
#                 if movement:
#                     print(f"  {vehicle_id} moved from {movement[0]} to {movement[1]}")
#                 else:
#                     print(f"  {vehicle_id} did not move")
#
#             print("\nVertiport States:")
#             for vertiport, state in vertiport_states.items():
#                 print(f"  {vertiport}: {state}")
#
#             print("\nUnmet Demand:")
#             for demand in unmet_demand:
#                 print(f"  {demand}")
#
#             print("-" * 50)
#
#             # Check iteration success
#             if coverage_rate < 0.6:
#                 print(f"Coverage rate below threshold ({coverage_rate:.2f}). Setting flag.")
#                 flag = 1
#                 stuck_iteration += 1
#             else:
#                 iteration_complete = True
#
#         # Step 4: Update battery charging
#         charging_and_battery_update(vehicle_states, time_interval=1, charging_rate=charging_rate)
#
#         print("-" * 50)
#
#         # print out car status of each point
#         print("Car status of each point:")
#         for vehicle_id, state in vehicle_states.items():
#             print(f"  {vehicle_id}: {state}")
#             print("location of the car: ", plane_status[vehicle_id]["location"])
#
#         print("-" * 50)



# Example usage





def run_iterations(num_iterations, vehicle_states, vertiport_states, gurobi_results_per_time, charging_rate,
                   discharge_rate, regenerate_solution, plane_status, distance_map):
    unmet_demand = []
    flag = 0  # Initialize flag
    stuck_iteration = 0

    for t in range(num_iterations):
        iteration_complete = False

        while not iteration_complete and stuck_iteration < 5:
            print(f"Time Step {t + 1}")


            # Step 0: Restore vehicle states and reset plane statuses
            restore_vehicle_states(vehicle_states)
            reset_plane_status(plane_status)

            # Initialize movement tracking for this timestep
            vehicle_movements = {vehicle_id: None for vehicle_id in vehicle_states.keys()}

            # Step 1: Update total demand
            if isinstance(gurobi_results_per_time[t], dict):
                gurobi_results_per_time[t] = [gurobi_results_per_time[t]]

            total_demand = update_demand_chart(unmet_demand, gurobi_results_per_time[t])

            # Step 2: Assign vehicles to tasks
            if flag == 1:
                print("Flag set: Retrieving second-best solution from Gurobi.")
                gurobi_results = regenerate_solution(t, unmet_demand, vehicle_states, vertiport_states, gurobi_results, get_second_best=False)
                flag = 0
            else:
                gurobi_results = gurobi_results_per_time[t] + [
                    {"start": start, "end": end, "flow": needed, "distance": calculate_distance(start, end)}
                    for start, end, needed in unmet_demand
                ]

            unmet_demand.clear()

            time_step_path_assignment(
                gurobi_results, vehicle_states, vertiport_states, unmet_demand, discharge_rate,
                vehicle_movements, plane_status
            )

            # Step 3: Calculate demand metrics
            total_met_demand, total_demand = calculate_demand_met(gurobi_results, vehicle_movements, unmet_demand)
            coverage_rate = calculate_coverage_rate(total_met_demand, total_demand)
            print(f"Current Coverage Rate: {coverage_rate:.2f}")

            activated_vertiports = [v for v, state in vertiport_states.items() if state["activated"]]
            total_cost = calculate_cost(activated_vertiports, cost_per_distance=10, distance_map=distance_map)
            print(f"Current Total Cost: {total_cost:.2f}")

            # Print detailed vehicle states
            # print("\nDetailed Vehicle States:")
            # for vehicle_id, state in vehicle_states.items():
            #     print(f"  {vehicle_id}: {state}")
            #
            # # Print plane statuses
            # print("\nPlane Statuses:")
            # for plane_id, status in plane_status.items():
            #     print(f"  {plane_id}: {status}")

            # Print movement and other states
            print("\nVehicle Movements:")
            for vehicle_id, movement in vehicle_movements.items():
                if movement:
                    print(f"  {vehicle_id} moved from {movement[0]} to {movement[1]}")
                else:
                    print(f"  {vehicle_id} did not move")

            print("\nVertiport States:")
            for vertiport, state in vertiport_states.items():
                print(f"  {vertiport}: {state}")

            print("\nUnmet Demand:")
            for demand in unmet_demand:
                print(f"  {demand}")

            print("-" * 50)

            # Check iteration success
            if coverage_rate < 0.6:
                print(f"Coverage rate below threshold ({coverage_rate:.2f}). Setting flag.")
                flag = 1
                stuck_iteration += 1
            else:
                iteration_complete = True

        # Step 4: Update battery charging
        charging_and_battery_update(vehicle_states, time_interval=1, charging_rate=charging_rate)

        print("-" * 50)

        # print out car status of each point
        print("Car status of each point:")
        for vehicle_id, state in vehicle_states.items():
            print(f"  {vehicle_id}: {state}")
            print("location of the car: ", plane_status[vehicle_id]["location"])

        print("-" * 50)
if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--vertiports_file", default="adjusted_vertiports_numeric.csv")
    parser.add_argument("--distance_file", default="distance_matrix.csv")
    parser.add_argument("--gurobi_results_file", default="updated_flow_data_with_vertiports.csv")
    args = parser.parse_args()

    # 加载数据
    vertiports_df = pd.read_csv(args.vertiports_file)
    vertiports = vertiports_df["Vertiport"].tolist()
    distance_map = load_distance_map(args.distance_file)
    # 获取所有时间步的数据
    gurobi_results_per_time = []
    total_time_steps = 500  # 假设一共500个时间步

    for t in range(total_time_steps):
        # 加载当前时间步的 Gurobi 结果
        gurobi_results = load_gurobi_results(args.gurobi_results_file, t)

        # 将每个时间步的数据添加到 gurobi_results_per_time
        gurobi_results_per_time.append(gurobi_results)

    # Debug: 打印第一步加载的 gurobi_results_per_time
    # print("Loaded Gurobi results:")
    # for t, results in enumerate(gurobi_results_per_time):
    #     print(f"Time step {t}: {results}")

    # vehicles = ["V1", "V2", "V3"]
    vehicles_number_each = 2
    vertiport_number = len(vertiports)
    vehicles = ["V" + str(i) for i in range(1, vehicles_number_each * vertiport_number + 1)]



    vehicle_states, vertiport_states = initialize_states_with_time(vehicles, vertiports,vertiport_number)
    plane_status = initialize_plane_status_loc(vehicles, vertiports)

    # Activate all vertiports
    for vertiport in vertiports:
        vertiport_states[vertiport]["activated"] = True

        # 加载距离映射
    distance_map = load_distance_map("distance_matrix.csv")





    # Run simulation
    run_iterations(
        num_iterations=2,
        vehicle_states=vehicle_states,
        vertiport_states=vertiport_states,
        gurobi_results_per_time=gurobi_results_per_time,
        charging_rate=20,
        discharge_rate=0.5,
        regenerate_solution=regenerate_solution,
        plane_status=plane_status,
        distance_map = distance_map
    )