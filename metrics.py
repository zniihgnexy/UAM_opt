from typing import List, Dict, Tuple

def calculate_coverage_rate(actual_met_demand: int, total_demand: int) -> float:
    """Calculate the coverage rate as the ratio of met demand to total demand."""
    if total_demand == 0:
        return 0  # Avoid division by zero
    return actual_met_demand / total_demand


def calculate_cost(activated_vertiports: List[str], cost_per_distance: float, distance_map: Dict) -> float:
    """Calculate the total cost based on activated vertiports and their distances."""
    total_cost = 0
    for i in range(len(activated_vertiports) - 1):
        loc1, loc2 = activated_vertiports[i], activated_vertiports[i + 1]
        distance = distance_map.get((loc1, loc2), 0)
        total_cost += distance * cost_per_distance
    return total_cost


def update_demand_chart(unmet_demand: List[Tuple[str, str, int]], new_demand: List[Dict]) -> int:
    """
    Updates the demand chart by including the unmet demand from the previous iteration
    and the new demand for the current iteration.
    """
    total_demand = sum([flow for _, _, flow in unmet_demand])  # Previous unmet demand
    total_demand += sum([demand["flow"] for demand in new_demand])  # New demand
    return total_demand
