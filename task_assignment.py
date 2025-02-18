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
        uam_required = path["UAM"]  # 新增：是否需要 UAM
        assigned = 0

        # Try to assign available planes at the starting location
        available_planes = [
            vehicle_id for vehicle_id, status in plane_status.items()
            if status["location"] == start and status["status"] == "standby"
            and status["battery"] >= battery_consumption_required(distance, discharge_rate)
            and (uam_required == 1)  # 只允许 UAM 车辆接 UAM 订单
        ]

        for vehicle_id in available_planes:
            # Assign the plane to the task
            plane_status[vehicle_id]["status"] = "in_service"
            plane_status[vehicle_id]["location"] = end
            plane_status[vehicle_id]["battery"] -= battery_consumption_required(distance, discharge_rate)
            assigned += 1

            # Record movement
            vehicle_movements[vehicle_id] = (start, end)

            if assigned >= needed:
                break

        # Update unmet demand
        if assigned < needed:
            unmet_demand.append((start, end, needed - assigned))

