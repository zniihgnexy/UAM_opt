from typing import List, Dict

def initialize_states_with_time(vehicles: List[str], vertiports: List[str],vertiport_numbers:int):
    """Initialize states for vehicles and vertiports."""
    num_vertiports = len(vertiports)
    vehicle_states = {
        k: {"activated": True, "avail": 1, "charging": 0, "in_service": 0, "battery": 100, "loc":vertiports[i // 2]}
        for i, k in enumerate(vehicles)
    }
    vertiport_states = {
        v: {"activated": False, "loc": None, "avail": 30, "in_service": 0}
        for v in vertiports
    }
    return vehicle_states, vertiport_states
