from typing import List, Dict

def initialize_states_with_time(vehicles: List[str], vertiports: List[str]):
    """Initialize states for vehicles and vertiports."""
    vehicle_states = {
        k: {"activated": True, "avail": 1, "charging": 0, "in_service": 0, "battery": 100, "loc": vertiports[0]}
        for k in vehicles
    }
    vertiport_states = {
        v: {"activated": False, "loc": None, "avail": 30, "in_service": 0}
        for v in vertiports
    }
    return vehicle_states, vertiport_states


def battery_consumption_required(distance: float, discharge_rate: float) -> float:
    """Calculates the battery percentage required to travel a given distance."""
    return distance * discharge_rate


def calculate_distance(loc1: str, loc2: str) -> float:
    """Mock function: Returns distance between two vertiports."""
    distance_map = {("P1", "P2"): 50, ("P2", "P3"): 80, ("P3", "P1"): 60, ("P1", "P3"): 30}
    return distance_map.get((loc1, loc2), float("inf"))


def time_step_path_assignment(gurobi_results: List[Dict], vehicle_states: Dict, vertiport_states: Dict,
                              unmet_demand: List, discharge_rate: float, vehicle_movements: Dict):
    """Assigns vehicles to paths based on Gurobi results and records their movements."""
    for path in gurobi_results:
        start, end = path["start"], path["end"]
        needed = path["flow"]  # Number of vehicles needed at the destination
        distance = path["distance"]

        assigned = 0

        # Try to assign available vehicles at 'start'
        vehicles_at_start = [
            (vehicle_id, state)
            for vehicle_id, state in vehicle_states.items()
            if state["loc"] == start and state["avail"] == 1 and state["activated"] and state["charging"] == 0
        ]

        for vehicle_id, state in vehicles_at_start:
            required_battery = battery_consumption_required(distance, discharge_rate)
            if state["battery"] >= required_battery:
                # Assign vehicle to task
                state["avail"] = 0  # Mark as unavailable
                state["in_service"] = 1  # Mark as in-service
                state["loc"] = end
                state["battery"] -= required_battery
                assigned += 1

                # Update vertiport states
                vertiport_states[start]["avail"] -= 1
                vertiport_states[end]["in_service"] += 1

                # Record movement
                vehicle_movements[vehicle_id] = (start, end)

                if assigned >= needed:
                    break

        # Record unmet demand if needed vehicles could not be fully assigned
        if assigned < needed:
            unmet_demand.append((start, end, needed - assigned))


def charging_and_battery_update(vehicle_states: Dict, time_interval: int, charging_rate: float):
    """
    Simulate charging and update vehicle states.
    Vehicles are only available again after full charge (battery = 100%).
    """
    for vehicle_id, state in vehicle_states.items():
        loc = state["loc"]

        # Check if vehicle is charging
        if state["charging"] == 1:
            state["battery"] += charging_rate * time_interval
            state["battery"] = min(100, state["battery"])  # Cap battery at 100%

            # If fully charged, make vehicle available
            if state["battery"] == 100:
                state["charging"] = 0  # Reset charging status
                state["avail"] = 1  # Vehicle is now available


def restore_vehicle_states(vehicle_states: Dict):
    """
    Ensure vehicle states are consistent:
    - Vehicles with completed tasks are reset to idle.
    - Charging vehicles are marked available after charging completes.
    """
    for vehicle_id, state in vehicle_states.items():
        # Handle vehicles that finished tasks
        if state["in_service"] == 1:
            state["in_service"] = 0  # Mark as no longer in service
            state["avail"] = 1  # Mark as available


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
