from generate_solution import regenerate_solution
from initialization import initialize_states_with_time
from distance_battery import calculate_distance
from metrics import calculate_coverage_rate, calculate_cost, update_demand_chart
from task_assignment import time_step_path_assignment
from battery_charging import charging_and_battery_update, restore_vehicle_states

def run_iterations(num_iterations, vehicle_states, vertiport_states, gurobi_results_per_time, charging_rate,
                   discharge_rate, regenerate_solution):
    unmet_demand = []
    flag = 0  # Initialize flag
    stuck_iteration = 0

    for t in range(num_iterations):
        iteration_complete = False

        while not iteration_complete and stuck_iteration < 5:
            print(f"Time Step {t + 1}")

            # Step 0: Ensure vehicle states are consistent
            restore_vehicle_states(vehicle_states)

            # Initialize movement tracking for this timestep
            vehicle_movements = {vehicle_id: None for vehicle_id in vehicle_states.keys()}

            # Step 1: Update total demand
            total_demand = update_demand_chart(unmet_demand, gurobi_results_per_time[t])

            # Step 2: Assign vehicles to tasks
            if flag == 1:
                get_second_best = True
                print("Flag set: Retrieving second-best solution from Gurobi.")
                gurobi_results = regenerate_solution(t, unmet_demand, vehicle_states, vertiport_states, gurobi_results, get_second_best)
                flag = 0  # Reset flag after regenerating solution
            else:
                # Use the original Gurobi results
                get_second_best = False
                gurobi_results = gurobi_results_per_time[t] + [
                    {"start": start, "end": end, "flow": needed, "distance": calculate_distance(start, end)}
                    for start, end, needed in unmet_demand
                ]

            unmet_demand.clear()

            time_step_path_assignment(gurobi_results, vehicle_states, vertiport_states, unmet_demand, discharge_rate,
                                      vehicle_movements)

            # Step 3: Calculate and print coverage rate and cost for the current solution
            actual_met_demand = sum([path["flow"] for path in gurobi_results]) - sum([d[2] for d in unmet_demand])
            coverage_rate = calculate_coverage_rate(actual_met_demand, total_demand)
            print(f"Current Coverage Rate: {coverage_rate:.2f}")

            activated_vertiports = [v for v, state in vertiport_states.items() if state["activated"]]
            total_cost = calculate_cost(activated_vertiports, cost_per_distance=10, distance_map={
                ("P1", "P2"): 50, ("P2", "P3"): 80, ("P3", "P1"): 60, ("P1", "P3"): 30
            })
            print(f"Current Total Cost: {total_cost:.2f}")

            # Check coverage rate and decide whether to re-run the iteration
            if coverage_rate < 0.6:
                print(f"Warning: Coverage rate below threshold ({coverage_rate:.2f}). Setting flag and retrying iteration.")
                flag = 1 
                stuck_iteration += 1
            elif stuck_iteration >= 5:
                iteration_complete = True
            else:
                iteration_complete = True  # Mark iteration as complete if coverage rate is acceptable

        # Step 4: Update battery charging
        charging_and_battery_update(vehicle_states, time_interval=1, charging_rate=charging_rate)

        # Step 5: Restore vehicle states (for both charging and task completion)
        restore_vehicle_states(vehicle_states)

        # Print detailed vehicle states
        print("\nDetailed Vehicle States:")
        for vehicle_id, state in vehicle_states.items():
            print(f"  {vehicle_id}: {state}")

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


# Example usage
if __name__ == "__main__":
    vehicles = ["V1", "V2", "V3"]
    vertiports = ["P1", "P2", "P3"]

    vehicle_states, vertiport_states = initialize_states_with_time(vehicles, vertiports)

    # Activate all vertiports
    for vertiport in vertiports:
        vertiport_states[vertiport]["activated"] = True

    # Define Gurobi results for simulation
    gurobi_results_per_time = [
        [{"start": "P1", "end": "P2", "flow": 3, "distance": 50}],
        [{"start": "P2", "end": "P3", "flow": 4, "distance": 80}],
        [{"start": "P3", "end": "P1", "flow": 1, "distance": 60}],
    ]

    # Run simulation
    run_iterations(
        num_iterations=4,
        vehicle_states=vehicle_states,
        vertiport_states=vertiport_states,
        gurobi_results_per_time=gurobi_results_per_time,
        charging_rate=20,  # Charging rate per time unit
        discharge_rate=0.5,  # Battery consumption rate per unit distance
        regenerate_solution=regenerate_solution  # Pass the regeneration function
    )

