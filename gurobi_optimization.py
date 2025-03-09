import numpy as np
import pandas as pd
from gurobipy import Model, GRB, quicksum
import math

# **空中距离矩阵**
distance_matrix = pd.read_csv("distance_matrix.csv", index_col=0)

# **空中距离矩阵**
distance_air = {
    (p, q): distance_matrix.loc[p, q] * 10  # 这里的 `10` 代表空中运输成本
    for p in distance_matrix.index
    for q in distance_matrix.columns
    if p != q
}

# **Gurobi 计算优化**
def run_gurobi_optimization(time_step, unmet_demand, gurobi_results_per_time, vertiports):
    """
    运行 Gurobi 进行航线优化，考虑 `unmet_demand` + `gurobi_results_per_time[t]` 的最新需求。

    输入：
    - `time_step`：当前时间步
    - `unmet_demand`：上一轮未满足的需求 [(start, end, flow), ...]
    - `gurobi_results_per_time`：当前时间步的 Gurobi 需求
    - `vertiports`：停机坪列表

    输出：
    - `gurobi_results`：优化后的结果 [{"start": x, "end": y, "flow": f, "distance": d}, ...]
    """
    print(f"🚀 运行 Gurobi 优化, 时间步: T{time_step}")

    # **合并上一轮未满足的需求 + 这一时间步的新需求**
    total_orders = unmet_demand + [
        (row["start"], row["end"], int(row["flow"]))
        for row in gurobi_results_per_time  #
    ]

    # === 初始化模型 ===
    model = Model(f"UAM_T{time_step}")

    # **决策变量**
    x = model.addVars(
        range(len(total_orders)),  # 订单编号
        vertiports,  # 起飞停机坪
        vertiports,  # 降落停机坪
        vtype=GRB.INTEGER,  # 离散变量，表示分配的流量是整数
        name="x"
    )

    # **目标函数**
    model.setObjective(
        quicksum(
            x[o, p, q] * (
                distance_air.get((p, q), 0)  # 空中运输的距离
            )
            for o in range(len(total_orders))
            for p in vertiports
            for q in vertiports if p != q  # 目标：起飞停机坪和降落停机坪不能是同一个
        ),
        GRB.MINIMIZE
    )

    # **约束条件**
    # 每个订单的流量应该完全分配，且分配到一个起飞停机坪到一个降落停机坪之间，且不能是同一个停机坪
    model.addConstrs(
        quicksum(x[o, p, q] for p in vertiports for q in vertiports if p != q) == total_orders[o][2]
        for o in range(len(total_orders))  # 每个订单的流量要完全分配
    )

    # **求解模型**
    model.optimize()

    # **处理结果**
    gurobi_results = []
    if model.status == GRB.OPTIMAL:
        print(f"T{time_step} 优化目标值: {model.objVal}")
        total_assigned_flow = 0
        for o in range(len(total_orders)):
            for p in vertiports:
                for q in vertiports:
                    if p != q and x[o, p, q].x > 0.5:
                        flow_assigned = total_orders[o][2]
                        gurobi_results.append({
                            "start": total_orders[o][0],
                            "end": total_orders[o][1],
                            "flow": x[o, p, q].x,
                            "distance": distance_air.get((p, q), 0)
                        })
                        total_assigned_flow += flow_assigned
        print(f"Total assigned flow: {total_assigned_flow}")
    return gurobi_results
