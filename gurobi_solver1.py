import math
from gurobipy import Model, GRB, quicksum

# 参数定义
GRID_WIDTH = 52  # 根据计算的网格列数
ground_cost = 5
air_cost = 10
activation_penalty = 100
def manhattan_distance(id1, id2, grid_width):
    """Calculate Manhattan distance between two grid points"""
    row1, col1 = divmod(id1, grid_width)
    row2, col2 = divmod(id2, grid_width)
    return abs(row1 - row2) + abs(col1 - col2)


def haversine(lat1, lon1, lat2, lon2):
    """Calculate Haversine distance between two geographical points"""
    R = 6371  # Earth's radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def solve_gurobi(batch_orders, vertiports, vertiport_data, ground_cost, air_cost,
                                           activation_penalty, grid_width):
    """
    Optimizes a single time period (no batch processing) and returns the results as a list of dictionaries.

    batch_orders: List of orders for the current time period
    vertiports: List of vertiport indices
    vertiport_data: Data containing latitude and longitude for vertiports
    ground_cost: Cost per unit distance for ground travel
    air_cost: Cost per unit distance for air travel
    activation_penalty: Penalty for activating a vertiport
    grid_width: Grid width to calculate Manhattan distance
    """
    # Initialize the model
    model = Model(f"UAM_Single_Time_Period_Optimization")

    # Decision variables
    x = model.addVars(
        range(len(batch_orders)),  # Orders index for the batch
        vertiports,  # Takeoff vertiports
        vertiports,  # Landing vertiports
        vtype=GRB.BINARY,
        name="x"
    )
    z = model.addVars(
        vertiports,
        vtype=GRB.BINARY,
        name="z"
    )

    # Ground distance calculation
    distance_ground_start = {
        (i, p): manhattan_distance(i, p, grid_width) * ground_cost
        for i in range(len(batch_orders)) for p in vertiports
    }
    distance_ground_end = {
        (j, q): manhattan_distance(j, q, grid_width) * ground_cost
        for j in range(len(batch_orders)) for q in vertiports
    }

    # Air distance calculation
    distance_air = {
        (p, q): haversine(lat_p, lon_p, lat_q, lon_q) * air_cost
        for (p, (lat_p, lon_p)) in zip(vertiports, vertiport_data[['Latitude', 'Longitude']].values)
        for (q, (lat_q, lon_q)) in zip(vertiports, vertiport_data[['Latitude', 'Longitude']].values)
        if p != q
    }

    # Objective function: minimize the total cost
    model.setObjective(
        quicksum(
            x[o, p, q] * (
                    distance_ground_start.get((o, p), 0) +  # Ground distance to takeoff vertiport
                    distance_air.get((p, q), 0) +  # Air distance between vertiports
                    distance_ground_end.get((o, q), 0)  # Ground distance to landing vertiport
            )
            for o in range(len(batch_orders))
            for p in vertiports
            for q in vertiports if p != q
        )
        + quicksum(
            z[p] * activation_penalty
            for p in vertiports
        ),
        GRB.MINIMIZE
    )

    # Constraints: each order should be assigned exactly once
    model.addConstrs(
        quicksum(x[o, p, q] for p in vertiports for q in vertiports if p != q) == 1
        for o in range(len(batch_orders))
    )
    model.addConstrs(
        x[o, p, q] <= z[p]
        for o in range(len(batch_orders)) for p in vertiports for q in vertiports if p != q
    )
    model.addConstrs(
        x[o, p, q] <= z[q]
        for o in range(len(batch_orders)) for p in vertiports for q in vertiports if p != q
    )

    # Solve the model
    model.optimize()

    # Process the results and return in required format
    all_results = []
    if model.status == GRB.OPTIMAL:
        for o in range(len(batch_orders)):
            for p in vertiports:
                for q in vertiports:
                    if p != q and x[o, p, q].x > 0.5:
                        start = p  # Use vertiport index as start
                        end = q  # Use vertiport index as end
                        flow = batch_orders[o][2]  # The flow of the order
                        distance = distance_ground_start.get((o, p), 0) + distance_air.get((p, q),
                                                                                           0) + distance_ground_end.get(
                            (o, q), 0)
                        all_results.append({
                            "start": start,
                            "end": end,
                            "flow": flow,
                            "distance": distance
                        })
        for p in vertiports:
            if z[p].x > 0.5:
                print(f"Vertiport {p} is activated.")
    else:
        print("No optimal solution found.")

    return all_results
