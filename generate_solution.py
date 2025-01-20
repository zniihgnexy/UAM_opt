from typing import List, Dict
from distance_battery import calculate_distance
from gurobi_solver import solve_gurobi

def regenerate_solution(t: int, unmet_demand: List, vehicle_states: Dict, vertiport_states: Dict,
                        original_solution: List[Dict], get_second_best) -> List[Dict]:
    """
    Regenerate a new Gurobi solution, optionally retrieving the second-best solution.

    :param t: Current time step.
    :param unmet_demand: Unmet demand from the previous iteration (tuples of (start, end, flow)).
    :param vehicle_states: Current states of vehicles.
    :param vertiport_states: Current states of vertiports.
    :param original_solution: The original solution to ban.
    :return: A new solution that excludes the banned solution.
    """
    print(f"Regenerating solution for iteration {t + 1}...")

    # Combine unmet demand (tuples) with new demand (dictionaries) for this iteration
    combined_demand = [
        {"start": d[0], "end": d[1], "flow": d[2], "distance": calculate_distance(d[0], d[1])}
        for d in unmet_demand
    ]

    # Call the Gurobi solver and request the second-best solution
    new_solution = solve_gurobi(combined_demand, get_second_best=get_second_best)

    return new_solution
