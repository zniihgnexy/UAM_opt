from gurobipy import Model, GRB, quicksum

# === 数据初始化 ===
time_intervals = ["T1", "T2"]  # 时间区间
orders = {
    "T1": [(0, 5, 10), (2, 8, 15), (3, 7, 20)],  # (起点, 终点, 订单需求)
    "T2": [(1, 6, 10), (4, 9, 15), (2, 5, 20)]
}
vertiports = list(range(10))  # 停机坪编号
capacity = 20  # 运输工具的最大容量
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
    range(len(orders["T1"])),  # 订单编号
    vertiports,  # 起飞停机坪
    vertiports,  # 降落停机坪
    vtype=GRB.BINARY,
    name="x"
)

z = model.addVars(
    vertiports,
    vtype=GRB.BINARY,
    name="z"
)

# === 目标函数 ===
model.setObjective(
    quicksum(
        x[t, o, p, q] * (
            distance_ground_start[(orders[t][o][0], p)] +
            distance_air[(p, q)] +
            distance_ground_end[(orders[t][o][1], q)]
        )
        for t in time_intervals
        for o in range(len(orders[t]))
        for p in vertiports
        for q in vertiports if p != q
    )
    + quicksum(
        z[p] * activation_penalty
        for p in vertiports
    ),
    GRB.MINIMIZE
)

# === 约束条件 ===

# 路径唯一性约束
for t in time_intervals:
    for o in range(len(orders[t])):
        model.addConstr(
            quicksum(x[t, o, p, q] for p in vertiports for q in vertiports if p != q) == 1,
            name=f"path_uniqueness_{t}_{o}"
        )

# 容量限制约束
for t in time_intervals:
    for p in vertiports:
        for q in vertiports:
            if p != q:
                model.addConstr(
                    quicksum(x[t, o, p, q] * orders[t][o][2] for o in range(len(orders[t]))) <= capacity,
                    name=f"capacity_limit_{t}_{p}_{q}"
                )

# 启用逻辑约束
for t in time_intervals:
    for o in range(len(orders[t])):
        for p in vertiports:
            for q in vertiports:
                if p != q:
                    model.addConstr(x[t, o, p, q] <= z[p], name=f"path_activation_start_{t}_{o}_{p}_{q}")
                    model.addConstr(x[t, o, p, q] <= z[q], name=f"path_activation_end_{t}_{o}_{p}_{q}")

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
