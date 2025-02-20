from gurobipy import Model, GRB

def solve_gurobi(demand_data, banned_solutions=None, get_second_best=False):
    """
    Solves the optimization problem with Gurobi and optionally retrieves the second-best solution.

    :param demand_data: List of demands with start, end, flow, and distance.
    :param banned_solutions: List of solutions to ban, each represented as [(start, end)].
    :param get_second_best: If True, retrieves the second-best solution from the solution pool.
    :return: List of paths representing the Gurobi solution.
    """
    from numpy import isfinite

    # Filter invalid demand data
    valid_demand_data = [
        d for d in demand_data
        if isfinite(d["flow"]) and isfinite(d["distance"]) and d["flow"] > 0 and d["distance"] > 0
    ]
    if len(valid_demand_data) != len(demand_data):
        print("Warning: Invalid demand data removed.")
        print(f"Invalid entries: {[d for d in demand_data if d not in valid_demand_data]}")

    model = Model("UAM_Optimization")

    # Variables: Assign flow for each demand
    flow_vars = {
        (d["start"], d["end"]): model.addVar(vtype=GRB.INTEGER, name=f"flow_{d['start']}_{d['end']}")
        for d in valid_demand_data
    }

    # Objective: Minimize total travel cost
    model.setObjective(
        sum(d["distance"] * flow_vars[(d["start"], d["end"])] for d in valid_demand_data),
        GRB.MINIMIZE
    )

    # Constraints: Add flow capacity constraints
    for d in valid_demand_data:
        model.addConstr(flow_vars[(d["start"], d["end"])] <= d["flow"], f"capacity_{d['start']}_{d['end']}")

    # Add banned solution constraints
    if banned_solutions:
        for banned in banned_solutions:
            # Ensure banned pairs exist in flow_vars
            banned_pairs = [(b[0], b[1]) for b in banned if (b[0], b[1]) in flow_vars]
            if banned_pairs:
                model.addConstr(
                    sum(flow_vars[p] for p in banned_pairs) <= len(banned_pairs) - 1,
                    f"banned_solution_{banned}"
                )

    # Enable the solution pool
    model.setParam("PoolSearchMode", 2)  # Enable the solution pool search
    model.setParam("PoolSolutions", 2)  # Store up to 2 solutions

    # Solve the model
    model.optimize()

    # Extract results
    if model.status == GRB.OPTIMAL:
        solution = []
        if get_second_best and model.SolCount > 1:
            # Retrieve the second-best solution
            model.setParam("SolutionNumber", 1)
            for start, end, d in ((d["start"], d["end"], d) for d in valid_demand_data):
                flow_value = flow_vars[(start, end)].Xn
                if isfinite(flow_value) and flow_value > 0:
                    solution.append({"start": start, "end": end, "flow": flow_value, "distance": d["distance"]})
        else:
            # Retrieve the best solution
            for start, end, d in ((d["start"], d["end"], d) for d in valid_demand_data):
                flow_value = flow_vars[(start, end)].X
                if isfinite(flow_value) and flow_value > 0:
                    solution.append({"start": start, "end": end, "flow": flow_value, "distance": d["distance"]})
        return solution
    else:
        print("No optimal solution found.")
        return []

