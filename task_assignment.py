from typing import List, Dict
from distance_battery import battery_consumption_required, calculate_distance

def time_step_path_assignment(gurobi_results: List[Dict], vehicle_states: Dict, vertiport_states: Dict,
                              unmet_demand: List, discharge_rate: float, vehicle_movements: Dict,
                              plane_status: Dict) -> (str, List, int, int):
    """
    Assign vehicles to paths based on gurobi results and then assign return-to-origin tasks.
    
    For each gurobi result, vehicles available at the starting location are assigned to the task.
    If an order isn’t fully assigned, the unmet portion is appended to a new unmet list.
    
    IMPORTANT:
      - The orders carried over from previous iterations (passed in via unmet_demand) are attempted for assignment,
        and any leftover from them is passed to the next iteration's gurobi call—but their unfulfill is not counted
        in the current iteration’s unfulfill.
      - Only orders from the current gurobi orders contribute to the current iteration’s unfulfill.
    
    Returns:
      A tuple containing:
        - most_needed_destination: The destination (end) with the highest total unmet demand.
        - new_unmet: The updated list of unmet demand orders (each as a tuple (start, end, leftover flow)).
        - fulfill: Total number of tasks fulfilled in the iteration.
        - unfulfill: Total number of tasks unfulfilled in the iteration (only from new orders).
    """
    iteration_fulfill = 0
    iteration_unfulfill = 0
    new_unmet_total = []   # Fresh unmet list for next iteration

    # Process previous unmet demand (carry-over orders).
    old_unmet = unmet_demand.copy()
    for path in old_unmet:
        start, end, needed = path
        distance = calculate_distance(start, end)
        assigned = 0

        # Find available vehicles at the starting location.
        available_planes = [
            vehicle_id for vehicle_id, status in plane_status.items()
            if status["location"] == start 
               and status["status"] == "standby"
               and status["battery"] >= battery_consumption_required(distance, discharge_rate)
               and vehicle_states[vehicle_id]["loc"] == start
               and not status.get("in_service", False)
        ]

        for vehicle_id in available_planes:
            # Assign the vehicle.
            plane_status[vehicle_id]["status"] = "in_service"
            plane_status[vehicle_id]["location"] = end
            battery_needed = battery_consumption_required(distance, discharge_rate)
            plane_status[vehicle_id]["battery"] -= battery_needed

            assigned += 1

            vehicle_states[vehicle_id]["loc"] = end
            vehicle_states[vehicle_id]["battery"] -= battery_needed
            vehicle_states[vehicle_id]["in_service"] = 1
            vehicle_movements[vehicle_id] = (start, end)
            plane_status[vehicle_id]["idle_count"] = 0

            # Update vertiport states.
            vertiport_states[start]["avail"] -= 1
            vertiport_states[start]["in_service"] += 1
            if vertiport_states[end]["in_service"] > 0:
                vertiport_states[end]["in_service"] -= 1
            vertiport_states[end]["avail"] += 1

            if assigned >= needed:
                break

        iteration_fulfill += assigned
        # For old unmet orders, record the leftover for gurobi call only.
        if assigned < needed:
            new_unmet_total.append((start, end, needed - assigned))

    # Process each new gurobi order.
    for path in gurobi_results:
        start, end = path["start"], path["end"]
        needed = path["flow"]
        distance = path["distance"]

        assigned = 0

        # Find available vehicles at the starting location.
        available_planes = [
            vehicle_id for vehicle_id, status in plane_status.items()
            if status["location"] == start 
               and status["status"] == "standby"
               and status["battery"] >= battery_consumption_required(distance, discharge_rate)
               and vehicle_states[vehicle_id]["loc"] == start
               and not status.get("in_service", False)
        ]

        for vehicle_id in available_planes:
            # Assign the vehicle.
            plane_status[vehicle_id]["status"] = "in_service"
            plane_status[vehicle_id]["location"] = end
            battery_needed = battery_consumption_required(distance, discharge_rate)
            plane_status[vehicle_id]["battery"] -= battery_needed

            assigned += 1

            vehicle_states[vehicle_id]["loc"] = end
            vehicle_states[vehicle_id]["battery"] -= battery_needed
            vehicle_states[vehicle_id]["in_service"] = 1
            vehicle_movements[vehicle_id] = (start, end)
            plane_status[vehicle_id]["idle_count"] = 0

            # Update vertiport states.
            vertiport_states[start]["avail"] -= 1
            vertiport_states[start]["in_service"] += 1
            if vertiport_states[end]["in_service"] > 0:
                vertiport_states[end]["in_service"] -= 1
            vertiport_states[end]["avail"] += 1

            if assigned >= needed:
                break

        iteration_fulfill += assigned
        # For new gurobi orders, add leftover to both iteration_unfulfill and new unmet list.
        if assigned < needed:
            unfulfilled = needed - assigned
            iteration_unfulfill += unfulfilled
            new_unmet_total.append((start, end, unfulfilled))

    # Adjust new_unmet_total based on actual assignments.
    updated_fulfillments = {}
    for vehicle_id, movement in vehicle_movements.items():
        if movement is not None:
            key = movement  # (start, end)
            updated_fulfillments[key] = updated_fulfillments.get(key, 0) + 1

    new_unmet = []
    for (s, e, demand) in new_unmet_total:
        key = (s, e)
        fulfilled = updated_fulfillments.get(key, 0)
        remaining = demand - fulfilled
        if remaining > 0:
            new_unmet.append((s, e, remaining))

    # # Determine the most needed destination.
    # unmet_by_destination = {}
    # for (s, e, demand) in new_unmet:
    #     unmet_by_destination[e] = unmet_by_destination.get(e, 0) + demand
    # if unmet_by_destination:
    #     most_needed_destination = max(unmet_by_destination, key=unmet_by_destination.get)
    # else:
    #     most_needed_destination = None

    return new_unmet, iteration_fulfill, iteration_unfulfill
