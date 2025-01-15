from gurobipy import Model, GRB, quicksum

# === 数据初始化 ===
time_intervals = ["T1", "T2"]  # 时间区间
orders = {
    "T1": [(0, 5, 10), (2, 8, 15), (3, 7, 20)],  # (起点, 终点, 订单需求)
    "T2": [(1, 6, 10), (4, 9, 15), (2, 5, 20)]
}
vertiports = list(range(10))  # 停机坪编号

# === 定义距离矩阵 ===
ground_cost = 5  # 地面运输成本
air_cost = 10  # 空中运输成本
activation_penalty = 100  # 激活惩罚

# 起点到停机坪的地面距离
distance_ground_start = {
    (i, p): abs(p - i) * ground_cost
    for t in time_intervals for (i, j, _) in orders[t] for p in vertiports
}

# 停机坪间空中距离
distance_air = {
    (p, q): abs(p - q) * air_cost
    for p in vertiports for q in vertiports if p != q
}

# 停机坪到终点的地面距离
distance_ground_end = {
    (j, q): abs(j - q) * ground_cost
    for t in time_intervals for (i, j, _) in orders[t] for q in vertiports
}

# === 初始化模型 ===
model = Model("Urban Air Mobility")

# === 决策变量 ===
x = model.addVars(
    time_intervals,  # 时间区间
    vertiports,  # 停机坪编号（开始）
    vertiports,  # 停机坪编号（结束）
    vtype=GRB.BINARY,
    name="x"
)

y = model.addVars(
    time_intervals,
    vertiports,  # 停机坪编号（开始）
    vertiports,  # 停机坪编号（结束）
    vtype=GRB.BINARY,
    name="y"
)

w = model.addVars(
    time_intervals,
    vertiports,
    vertiports,
    vertiports,
    vtype=GRB.BINARY,
    name="w"
)

z = model.addVars(
    vertiports,
    vtype=GRB.BINARY,
    name="z"
)

# === 目标函数 ===
model.setObjective(
    quicksum(
        x[t, p, q] * distance_ground_start[(i, p)]
        for t in time_intervals for i, j, _ in orders[t] for p in vertiports for q in vertiports
    )
    + quicksum(
        w[t, p, q, r] * distance_air[(p, q)]
        for t in time_intervals for p in vertiports for q in vertiports for r in vertiports if p != q
    )
    + quicksum(
        y[t, p, q] * distance_ground_end[(j, q)]
        for t in time_intervals for i, j, _ in orders[t] for p in vertiports for q in vertiports
    )
    + quicksum(
        z[p] * activation_penalty
        for p in vertiports
    ),
    GRB.MINIMIZE
)

# === 约束条件 ===

# 起点分配约束
for t in time_intervals:
    for i, j, _ in orders[t]:
        model.addConstr(
            quicksum(x[t, p, q] for p in vertiports for q in vertiports) == 1,
            name=f"start_assignment_{t}_{i}_{j}"
        )

# 停机坪到终点的分配约束
for t in time_intervals:
    for i, j, _ in orders[t]:
        model.addConstr(
            quicksum(y[t, p, q] for p in vertiports for q in vertiports) == 1,
            name=f"end_assignment_{t}_{i}_{j}"
        )

# 激活约束
for p in vertiports:
    model.addConstr(
        quicksum(x[t, p, q] for t in time_intervals for q in vertiports) <= z[p] * len(time_intervals),
        name=f"activation_{p}"
    )

# === 求解模型 ===
model.optimize()

# === 输出结果 ===
if model.status == GRB.OPTIMAL:
    print(f"Objective value: {model.objVal}")
    for var in model.getVars():
        if var.x > 0.5:  # 打印被激活的变量及其值
            print(f"{var.varName}: {var.x}")
else:
    print("No optimal solution found.")
