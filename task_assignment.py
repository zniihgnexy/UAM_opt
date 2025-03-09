from typing import List, Dict

from distance_battery import battery_consumption_required

def time_step_path_assignment(gurobi_results: List[Dict], vehicle_states: Dict, vertiport_states: Dict,
                              unmet_demand: List, discharge_rate: float, vehicle_movements: Dict,
                              plane_status: Dict):
    """Assigns vehicles to paths based on Gurobi results and updates their statuses."""
    for path in gurobi_results:
        start, end = path["start"], path["end"]
        needed = path["flow"]
        distance = path["distance"]

        assigned = 0

        # Try to assign available planes at the starting location
        available_planes = [
            vehicle_id for vehicle_id, status in plane_status.items()
            if status["location"] == start and status["status"] == "standby" and status["battery"] >=
            battery_consumption_required(distance, discharge_rate)
            and vehicle_states[vehicle_id]["loc"] == start  # Ensure the vehicle is actually at the start location
            and plane_status[vehicle_id].get("in_service", False) is False
            # Ensure the plane is not already assigned
        ]
        print(f"Available planes for path {start} -> {end}: {available_planes}")

        for vehicle_id in available_planes:
            # Assign the plane to the task
            if plane_status[vehicle_id]["status"] == "in_service":
                continue
            plane_status[vehicle_id]["status"] = "in_service"
            plane_status[vehicle_id]["location"] = end
            plane_status[vehicle_id]["battery"] -= battery_consumption_required(distance, discharge_rate)
            assigned += 1

            # Update vehicle state, for example, updating the vehicle's location and battery
            vehicle_states[vehicle_id]["loc"] = end  # Update vehicle location to the end vertiport
            vehicle_states[vehicle_id]["battery"] -= battery_consumption_required(distance,
                                                                                  discharge_rate)  # Update battery
            vehicle_states[vehicle_id]["in_service"] = 1  # Update in_service status
            # Record movement
            vehicle_movements[vehicle_id] = (start, end)
            # Update avail values
            # Vehicle departs from `start` vertiport (becomes in_service)
            print(
                f"🚀 Before assignment: {start} -> {end}, avail={vertiport_states[start]['avail']}, in_service={vertiport_states[start]['in_service']}")

            vertiport_states[start]["avail"] -= 1  # 出发点少一辆可用飞机
            vertiport_states[start]["in_service"] += 1  # 出发点多一辆在任务中的飞机
            print(
                f"✅ After assignment: {start} -> {end}, avail={vertiport_states[start]['avail']}, in_service={vertiport_states[start]['in_service']}")

            # Vehicle arrives at `end` vertiport
            # 假设任务完成后车辆会变为可用状态（standby），那么 `end` 的 in_service 应该减少
            if vertiport_states[end]["in_service"] > 0:
                vertiport_states[end]["in_service"] -= 1  # 终点停机坪的 in_service 车辆数减少
            vertiport_states[end]["avail"] += 1  # 终点停机坪可用飞机增加

            if assigned >= needed:
                break

        print(f"Assigning planes for {start} -> {end}: Needed: {needed}, Assigned: {assigned}")

        # Update unmet demand
        if assigned < needed:
            unmet_demand.append((start, end, needed - assigned))


    # Debug: print unmet demand
    print(f"Updated unmet demand: {unmet_demand}")
