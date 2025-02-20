def battery_consumption_required(distance: float, discharge_rate: float) -> float:
    """Calculates the battery percentage required to travel a given distance."""
    return distance * discharge_rate


# def calculate_distance(loc1: str, loc2: str) -> float:
#     """Mock function: Returns distance between two vertiports."""
#     distance_map = {("P1", "P2"): 50, ("P2", "P3"): 80, ("P3", "P1"): 60, ("P1", "P3"): 30}
#     return distance_map.get((loc1, loc2), float("inf"))
import pandas as pd

# Load the distance matrix from the file
distance_data = pd.read_csv('distance_matrix.csv', index_col=0)

def calculate_distance(loc1: str, loc2: str) -> float:
    """Returns the distance between two points from the distance matrix."""
    if loc1 in distance_data.index and loc2 in distance_data.columns:
        return distance_data.loc[loc1, loc2]
    else:
        raise ValueError(f"Distance between {loc1} and {loc2} not found.")
