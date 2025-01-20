from typing import List, Dict

from distance_battery import battery_consumption_required

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
