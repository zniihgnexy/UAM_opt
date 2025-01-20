def battery_consumption_required(distance: float, discharge_rate: float) -> float:
    """Calculates the battery percentage required to travel a given distance."""
    return distance * discharge_rate


def calculate_distance(loc1: str, loc2: str) -> float:
    """Mock function: Returns distance between two vertiports."""
    distance_map = {("P1", "P2"): 50, ("P2", "P3"): 80, ("P3", "P1"): 60, ("P1", "P3"): 30}
    return distance_map.get((loc1, loc2), float("inf"))
