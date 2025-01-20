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
