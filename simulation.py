from initialization import initialize_states_with_time
from distance_battery import calculate_distance
from task_assignment import time_step_path_assignment
from battery_charging import charging_and_battery_update, restore_vehicle_states

def run_iterations(num_iterations, vehicle_states, vertiport_states, gurobi_results_per_time, charging_rate,
                   discharge_rate):
    """Run the simulation for the given number of time steps."""
    unmet_demand = []
    for t in range(num_iterations):
        print(f"Time Step {t + 1}")

        # Step 0: Ensure vehicle states are consistent
        restore_vehicle_states(vehicle_states)

        # Initialize movement tracking for this timestep
        vehicle_movements = {vehicle_id: None for vehicle_id in vehicle_states.keys()}

        # Step 1: Assign vehicles to tasks
        gurobi_results = gurobi_results_per_time[t] + [
            {"start": start, "end": end, "flow": needed, "distance": calculate_distance(start, end)}
            for start, end, needed in unmet_demand
        ]
        unmet_demand.clear()

        time_step_path_assignment(gurobi_results, vehicle_states, vertiport_states, unmet_demand, discharge_rate,
                                  vehicle_movements)

        # Step 2: Update battery charging
        charging_and_battery_update(vehicle_states, time_interval=1, charging_rate=charging_rate)

        # Step 3: Restore vehicle states (for both charging and task completion)
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
        num_iterations=3,
        vehicle_states=vehicle_states,
        vertiport_states=vertiport_states,
        gurobi_results_per_time=gurobi_results_per_time,
        charging_rate=20,  # Charging rate per time unit
        discharge_rate=0.5  # Battery consumption rate per unit distance
    )
