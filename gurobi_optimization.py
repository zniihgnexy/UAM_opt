import numpy as np
import pandas as pd
from gurobipy import Model, GRB, quicksum
import math

# Load the distance matrix and compute the air transportation cost
distance_matrix = pd.read_csv("distance_matrix.csv", index_col=0)
distance_air = {
    (p, q): distance_matrix.loc[p, q] * 10  # Here, 10 represents the air transport cost factor
    for p in distance_matrix.index
    for q in distance_matrix.columns
    if p != q
}

def run_gurobi_optimization(time_step, unmet_demand, gurobi_results_per_time, vertiports):
    """
    Run Gurobi optimization for route assignment while prioritizing coverage.
    
    Parameters:
      - time_step: Current time step.
      - unmet_demand: List of tuples (start, end, flow) from previous iterations.
      - gurobi_results_per_time: List of dictionaries (with keys "start", "end", "flow") for the current time step.
      - vertiports: List of vertiport identifiers.
      
    Returns:
      - gurobi_results: List of dictionaries with keys "start", "end", "flow", and "distance".
      - unmet_demand_next: List of tuples (start, end, remaining flow) for any unfulfilled orders.
    """
    print(f"🚀 Running Gurobi optimization, Time Step: T{time_step}")
    
    # Combine previous unmet demand with new demand for the current time step.
    total_orders = unmet_demand + [
        (row["start"], row["end"], int(row["flow"]))
        for row in gurobi_results_per_time
    ]
    
    if not total_orders:
        print("No orders to optimize.")
        return [], []
    
    model = Model(f"UAM_T{time_step}")
    
    # Decision variables: x[o, p, q] represents the flow assigned for order o using takeoff p and landing q.
    x = model.addVars(
        range(len(total_orders)),
        vertiports,
        vertiports,
        vtype=GRB.INTEGER,
        name="x"
    )
    
    # Constraint: For each order, the sum of assigned flows must not exceed the order’s total demand.
    model.addConstrs(
        quicksum(x[o, p, q] for p in vertiports for q in vertiports if p != q) <= total_orders[o][2]
        for o in range(len(total_orders))
    )
    
    # Set a large constant (bigM) to prioritize coverage over cost.
    bigM = 1e6

    # Objective: Maximize total assigned flow (weighted by bigM) minus the cost.
    model.setObjective(
        quicksum(
            x[o, p, q] * (bigM - distance_air.get((p, q), 0))
            for o in range(len(total_orders))
            for p in vertiports
            for q in vertiports if p != q
        ),
        GRB.MAXIMIZE
    )
    
    model.optimize()
    
    gurobi_results = []
    unmet_demand_next = []
    
    if model.status in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
        for o in range(len(total_orders)):
            # Sum the flow assigned to order o across all (p,q) pairs.
            assigned_flow = sum(x[o, p, q].x for p in vertiports for q in vertiports if p != q)
            # For reporting, select a representative (p,q) pair (the one with the largest assignment).
            best_p, best_q, best_flow = None, None, 0
            for p in vertiports:
                for q in vertiports:
                    if p != q and x[o, p, q].x > best_flow:
                        best_flow = x[o, p, q].x
                        best_p, best_q = p, q
            gurobi_results.append({
                "start": total_orders[o][0],
                "end": total_orders[o][1],
                "flow": assigned_flow,
                "distance": distance_air.get((best_p, best_q), 0) if best_p is not None and best_q is not None else 0
            })
            
            # Calculate any remaining unfulfilled demand.
            unfulfilled = total_orders[o][2] - assigned_flow
            if unfulfilled > 0:
                unmet_demand_next.append((total_orders[o][0], total_orders[o][1], unfulfilled))
    else:
        print("No optimal solution found.")
    
    return gurobi_results, unmet_demand_next
