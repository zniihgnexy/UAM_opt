from typing import Dict

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
