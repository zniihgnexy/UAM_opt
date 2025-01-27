import numpy as np
import pandas as pd
from gurobipy import Model, GRB, quicksum
import math

# === 加载数据 ===
file_path = "hh-odflow.npz"
data = np.load(file_path)
flow_data = data['arr_0']
MAX_TIME_INTERVALS = 5

selected_time_intervals = list(range(min(MAX_TIME_INTERVALS, flow_data.shape[0])))
time_intervals = [f"T{t}" for t in selected_time_intervals]

orders = {
    f"T{t}": [
        (i, j, int(flow_data[t, i, j]))
        for i in range(flow_data.shape[1])
        for j in range(flow_data.shape[2])
        if flow_data[t, i, j] > 0
    ]
    for t in selected_time_intervals
}

vertiport_data = pd.read_csv("adjusted_vertiports_numeric.csv")
vertiports = vertiport_data['Grid_ID'].tolist()
GRID_WIDTH = 52
ground_cost = 5
air_cost = 10
activation_penalty = 100

# 曼哈顿距离函数
def manhattan_distance(id1, id2, grid_width):
    row1, col1 = divmod(id1, grid_width)
    row2, col2 = divmod(id2, grid_width)
    return abs(row1 - row2) + abs(col1 - col2)

# 空中距离函数
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

distance_ground_start = {
    (i, p): manhattan_distance(i, p, GRID_WIDTH) * ground_cost
    for t in time_intervals for (i, j, _) in orders[t] for p in vertiports
}
distance_air = {
    (p, q): haversine(lat_p, lon_p, lat_q, lon_q) * air_cost
    for (p, (lat_p, lon_p)) in zip(vertiports, vertiport_data[['Latitude', 'Longitude']].values)
    for (q, (lat_q, lon_q)) in zip(vertiports, vertiport_data[['Latitude', 'Longitude']].values)
    if p != q
}
distance_ground_end = {
    (j, q): manhattan_distance(j, q, GRID_WIDTH) * ground_cost
    for t in time_intervals for (i, j, _) in orders[t] for q in vertiports
}

model = Model("Urban Air Mobility")
x = model.addVars(
    time_intervals,
    range(max(len(orders[t]) for t in time_intervals)),
    vertiports,
    vertiports,
    vtype=GRB.BINARY,
    name="x"
)
z = model.addVars(vertiports, vtype=GRB.BINARY, name="z")

model.setObjective(
    quicksum(
        x[t, o, p, q] * (
            distance_ground_start.get((orders[t][o][0], p), 0) +
            distance_air.get((p, q), 0) +
            distance_ground_end.get((orders[t][o][1], q), 0)
        )
        for t in time_intervals for o in range(len(orders[t])) for p in vertiports for q in vertiports if p != q
    )
    + quicksum(z[p] * activation_penalty for p in vertiports),
    GRB.MINIMIZE
)

model.addConstrs(
    quicksum(x[t, o, p, q] for p in vertiports for q in vertiports if p != q) == 1
    for t in time_intervals for o in range(len(orders[t]))
)
model.addConstrs(
    x[t, o, p, q] <= z[p]
    for t in time_intervals for o in range(len(orders[t])) for p in vertiports for q in vertiports if p != q
)
model.addConstrs(
    x[t, o, p, q] <= z[q]
    for t in time_intervals for o in range(len(orders[t])) for p in vertiports for q in vertiports if p != q
)

model.optimize()

if model.status == GRB.OPTIMAL:
    print(f"Objective value: {model.objVal}")
    for t in time_intervals:
        for o in range(len(orders[t])):
            for p in vertiports:
                for q in vertiports:
                    if p != q and x[t, o, p, q].x > 0.5:
                        print(f"Time: {t}, Order: {o}, Takeoff: {p}, Landing: {q}, Flow: {orders[t][o][2]}")
    for p in vertiports:
        if z[p].x > 0.5:
            print(f"Vertiport {p} is activated.")
else:
    print("No optimal solution found.")
