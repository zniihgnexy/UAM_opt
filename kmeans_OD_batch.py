import numpy as np
import pandas as pd
from gurobipy import Model, GRB, quicksum
import math

# === 加载数据 ===
file_path = "hh-odflow.npz"
data = np.load(file_path)
flow_data = data['arr_0']
# 加载停机坪数据
vertiport_data = pd.read_csv("adjusted_vertiports_numeric.csv")

# 创建一个从 Grid_ID 到停机坪名称（Vertiport）的字典
grid_to_vertiport = dict(zip(vertiport_data['Grid_ID'], vertiport_data['Vertiport']))

# 限制的时间区间数量和批次大小
MAX_TIME_INTERVALS = 500
BATCH_SIZE = 50

# 构造时间区间
time_intervals = [f"T{t}" for t in range(min(MAX_TIME_INTERVALS, flow_data.shape[0]))]

# 构造订单数据
orders = {
    f"T{t}": [
        (i, j, int(flow_data[t, i, j]))
        for i in range(flow_data.shape[1])
        for j in range(flow_data.shape[2])
        if flow_data[t, i, j] > 0
    ]
    for t in range(min(MAX_TIME_INTERVALS, flow_data.shape[0]))
}

# 加载停机坪数据
vertiport_data = pd.read_csv("adjusted_vertiports_numeric.csv")
vertiports = vertiport_data['Grid_ID'].tolist()

# 参数定义
GRID_WIDTH = 52  # 根据计算的网格列数
ground_cost = 5
air_cost = 10
activation_penalty = 100

# 曼哈顿距离计算函数
def manhattan_distance(id1, id2, grid_width):
    row1, col1 = divmod(id1, grid_width)
    row2, col2 = divmod(id2, grid_width)
    return abs(row1 - row2) + abs(col1 - col2)

# 空中距离计算函数
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半径
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 停机坪之间的空中距离矩阵
distance_air = {
    (p, q): haversine(lat_p, lon_p, lat_q, lon_q) * air_cost
    for (p, (lat_p, lon_p)) in zip(vertiports, vertiport_data[['Latitude', 'Longitude']].values)
    for (q, (lat_q, lon_q)) in zip(vertiports, vertiport_data[['Latitude', 'Longitude']].values)
    if p != q
}

# 分批处理时间片段
batches = [time_intervals[i:i + BATCH_SIZE] for i in range(0, len(time_intervals), BATCH_SIZE)]

# 保存每批次结果
all_results = []

for batch_idx, batch in enumerate(batches):
    print(f"正在优化第 {batch_idx + 1}/{len(batches)} 批时间片段...")

    # 构建当前批次的订单数据
    batch_orders = {t: orders[t] for t in batch}

    # 起点到停机坪的地面距离
    distance_ground_start = {
        (i, p): manhattan_distance(i, p, GRID_WIDTH) * ground_cost
        for t in batch for (i, j, _) in batch_orders[t] for p in vertiports
    }

    # 停机坪到终点的地面距离
    distance_ground_end = {
        (j, q): manhattan_distance(j, q, GRID_WIDTH) * ground_cost
        for t in batch for (i, j, _) in batch_orders[t] for q in vertiports
    }

    # === 初始化模型 ===
    model = Model(f"UAM_Batch_{batch_idx + 1}")

    # 决策变量
    x = model.addVars(
        batch,  # 时间区间
        range(max(len(batch_orders[t]) for t in batch)),  # 最大订单编号
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

    # 目标函数
    model.setObjective(
        quicksum(
            x[t, o, p, q] * (
                distance_ground_start.get((batch_orders[t][o][0], p), 0) +  # 确保键存在
                distance_air.get((p, q), 0) +
                distance_ground_end.get((batch_orders[t][o][1], q), 0)
            )
            for t in batch
            for o in range(len(batch_orders[t]))
            for p in vertiports
            for q in vertiports if p != q
        )
        + quicksum(
            z[p] * activation_penalty
            for p in vertiports
        ),
        GRB.MINIMIZE
    )

    # 约束条件
    model.addConstrs(
        quicksum(x[t, o, p, q] for p in vertiports for q in vertiports if p != q) == 1
        for t in batch for o in range(len(batch_orders[t]))
    )
    model.addConstrs(
        x[t, o, p, q] <= z[p]
        for t in batch for o in range(len(batch_orders[t])) for p in vertiports for q in vertiports if p != q
    )
    model.addConstrs(
        x[t, o, p, q] <= z[q]
        for t in batch for o in range(len(batch_orders[t])) for p in vertiports for q in vertiports if p != q
    )

    # 求解模型
    model.optimize()

    # 处理结果
    if model.status == GRB.OPTIMAL:
        print(f"Batch {batch_idx + 1} Objective value: {model.objVal}")
        for t in batch:
            for o in range(len(batch_orders[t])):
                for p in vertiports:
                    for q in vertiports:
                        if p != q and x[t, o, p, q].x > 0.5:
                            start_vertiport = grid_to_vertiport.get(batch_orders[t][o][0], "Unknown")
                            end_vertiport = grid_to_vertiport.get(batch_orders[t][o][1], "Unknown")
                            all_results.append((t, o, p, q, batch_orders[t][o][2]))
        for p in vertiports:
            if z[p].x > 0.5:
                print(f"Vertiport {p} is activated in batch {batch_idx + 1}.")
    else:
        print(f"Batch {batch_idx + 1} did not find an optimal solution.")

# 保存最终结果
results_df = pd.DataFrame(all_results, columns=["Time", "Order", "Start_Vertiport", "End_Vertiport", "Flow"])
results_df.to_csv("optimized_results_with_vertiport_mapping.csv", index=False)
print("优化结果已保存至 'optimized_results_with_vertiport_mapping.csv'")