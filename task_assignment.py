from typing import List, Dict
from distance_battery import battery_consumption_required

def time_step_path_assignment(gurobi_results: List[Dict], vehicle_states: Dict, vertiport_states: Dict,
                              unmet_demand: List, discharge_rate: float, vehicle_movements: Dict,
                              plane_status: Dict):
    """
    Assign vehicles to paths based on the provided Gurobi results and update their statuses.
    For each route (start -> end with required 'flow'), assign as many vehicles as possible (only limited by availability and battery).
    Returns a list of unmet demand tuples (start, end, remaining flow) for this iteration.
    """
    new_unmet_demand = []  # For unmet demand in this iteration

    for path in gurobi_results:
        start, end = path["start"], path["end"]
        needed = path["flow"]
        distance = path["distance"]
        assigned = 0

        # Find eligible vehicles: at the start location, standby, have enough battery, and not already in service
        available_planes = [
            vehicle_id for vehicle_id, status in plane_status.items()
            if status["location"] == start and status["status"] == "standby" and
               status["battery"] >= battery_consumption_required(distance, discharge_rate)
               and vehicle_states[vehicle_id]["loc"] == start
        ]

        for vehicle_id in available_planes:
            if plane_status[vehicle_id]["status"] == "in_service":
                continue

            # Assign the vehicle
            plane_status[vehicle_id]["status"] = "in_service"
            plane_status[vehicle_id]["location"] = end
            plane_status[vehicle_id]["battery"] -= battery_consumption_required(distance, discharge_rate)
            assigned += 1

            vehicle_states[vehicle_id]["loc"] = end
            vehicle_states[vehicle_id]["battery"] -= battery_consumption_required(distance, discharge_rate)
            vehicle_states[vehicle_id]["in_service"] = 1
            vehicle_movements[vehicle_id] = (start, end)

            # Update vertiport counts
            vertiport_states[start]["avail"] -= 1
            vertiport_states[start]["in_service"] += 1
            if vertiport_states[end]["in_service"] > 0:
                vertiport_states[end]["in_service"] -= 1
            vertiport_states[end]["avail"] += 1

            if assigned >= needed:
                break

        # Record unmet demand for this route (only for this iteration)
        if assigned < needed:
            new_unmet_demand.append((start, end, needed - assigned))
    
    # print(f"Updated unmet demand for iteration: {new_unmet_demand}")
    # Return the unmet demand for the current iteration
    return new_unmet_demand
