import numpy as np
import pandas as pd
from gurobipy import Model, GRB, quicksum
import math
import json
# **空中距离矩阵**
distance_matrix = pd.read_csv("distance_matrix.csv", index_col=0)

# **空中距离矩阵**
distance_air = {
    (p, q): distance_matrix.loc[p, q] # 这里的 `10` 代表空中运输成本
    for p in distance_matrix.index
    for q in distance_matrix.columns
    if p != q
}

# **Gurobi 计算优化**
# def run_gurobi_optimization(time_step, unmet_demand, gurobi_results_per_time, vertiports):
#     """
#     运行 Gurobi 进行航线优化，考虑 `unmet_demand` + `gurobi_results_per_time[t]` 的最新需求。
#
#     输入：
#     - `time_step`：当前时间步
#     - `unmet_demand`：上一轮未满足的需求 [(start, end, flow), ...]
#     - `gurobi_results_per_time`：当前时间步的 Gurobi 需求
#     - `vertiports`：停机坪列表
#
#     输出：
#     - `gurobi_results`：优化后的结果 [{"start": x, "end": y, "flow": f, "distance": d}, ...]
#     """
#     print(f"🚀 运行 Gurobi 优化, 时间步: T{time_step}")
#
#     # **合并上一轮未满足的需求 + 这一时间步的新需求**
#     total_orders = unmet_demand + [
#         (row["start"], row["end"], int(row["flow"]))
#         for row in gurobi_results_per_time  #
#     ]
#     # 🚀 计算 Gurobi 输入前的总流量
#     total_flow_before = sum(order[2] for order in total_orders)
#     print(f"📊 Gurobi 输入前总流量: {total_flow_before}")
#
#     # === 初始化模型 ===
#     model = Model(f"UAM_T{time_step}")
#
#     # **决策变量**
#     x = model.addVars(
#         range(len(total_orders)),  # 订单编号
#         vertiports,  # 起飞停机坪
#         vertiports,  # 降落停机坪
#         vtype=GRB.INTEGER,  # 离散变量，表示分配的流量是整数
#         name="x"
#     )
#
#     # **目标函数**
#     model.setObjective(
#         quicksum(
#             x[o, p, q] * (
#                 distance_air.get((p, q), 0)  # 空中运输的距离
#             )
#             for o in range(len(total_orders))
#             for p in vertiports
#             for q in vertiports if p != q  # 目标：起飞停机坪和降落停机坪不能是同一个
#         ),
#         GRB.MINIMIZE
#     )
#
#     # **约束条件**
#     # 每个订单的流量应该完全分配，且分配到一个起飞停机坪到一个降落停机坪之间，且不能是同一个停机坪
#     model.addConstrs(
#         quicksum(x[o, p, q] for p in vertiports for q in vertiports if p != q) == total_orders[o][2]
#         for o in range(len(total_orders))  # 每个订单的流量要完全分配
#     )
#
#     # **求解模型**
#     model.optimize()
#
#     # **处理结果**
#     gurobi_results = []
#     if model.status == GRB.OPTIMAL:
#         print(f"T{time_step} 优化目标值: {model.objVal}")
#         total_assigned_flow = 0
#         for o in range(len(total_orders)):
#             for p in vertiports:
#                 for q in vertiports:
#                     if p != q and x[o, p, q].x > 0.5:
#                         flow_assigned = total_orders[o][2]
#                         gurobi_results.append({
#                             "start": total_orders[o][0],
#                             "end": total_orders[o][1],
#                             "flow": x[o, p, q].x,
#                             "distance": distance_air.get((p, q), 0)
#                         })
#                         total_assigned_flow += flow_assigned
#
#         print(f"Total assigned flow: {total_assigned_flow}")
#         # 🚀 计算 Gurobi 分配后的总流量
#         total_flow_after = sum(res["flow"] for res in gurobi_results)
#         print(f"📊 Gurobi 分配后总流量: {total_flow_after}")
#
#         # 🚨 流量一致性检查
#         if total_flow_before != total_flow_after:
#             print(f"⚠️ 流量不匹配! 输入: {total_flow_before}, 分配后: {total_flow_after}")
#         else:
#             print(f"✅ 流量一致! 输入: {total_flow_before}, 分配后: {total_flow_after}")
#
#     return gurobi_results



# **Gurobi 计算优化**
from gurobipy import Model, GRB, quicksum

def run_gurobi_optimization(time_step, unmet_demand, gurobi_results_per_time,
                            vertiports, vertiport_states):
    print(f"🚀 运行 Gurobi 优化, 时间步: T{time_step}")
    # print("\n🔍 [DEBUG] vertiport_states 数据结构（前5项）：")
    # try:
    #     print(json.dumps(dict(list(vertiport_states.items())[:5]), indent=2))  # 只打印前5项，避免太长
    # except Exception as e:
    #     print(f"❌ 发生错误，无法打印 vertiport_states: {e}")
    #
    # print("\n🔍 [DEBUG] vertiports 列表:", vertiports)

    # **合并未满足需求 + 这一时间步的新需求**
    total_orders = unmet_demand + [
        (row["start"], row["end"], int(row["flow"]))
        for row in gurobi_results_per_time
    ]
    total_flow_before = sum(order[2] for order in total_orders)
    print(f"📊 Gurobi 输入前总流量: {total_flow_before}")

    # === 初始化 Gurobi 模型 ===
    model = Model(f"UAM_T{time_step}")

    # **决策变量**
    f = model.addVars(
        [(o, p, q) for o in range(len(total_orders)) for p in vertiports for q in vertiports if p != q],
        vtype=GRB.INTEGER, name="f"
    )

    x = model.addVars(
        [(o, p, q) for o in range(len(total_orders)) for p in vertiports for q in vertiports if p != q],
        vtype=GRB.BINARY, name="x"
    )

    # **目标函数：最大化总流量**
    model.setObjective(
        quicksum(f[o, p, q] for o in range(len(total_orders)) for p in vertiports for q in vertiports if p != q),
        GRB.MAXIMIZE
    )

    # **约束1️⃣：每个订单只能被分配到一条 (Start, End) 航线**
    model.addConstrs(
        quicksum(x[o, p, q] for p in vertiports for q in vertiports if p != q) == 1
        for o in range(len(total_orders))
    )

    # **约束2️⃣：订单的流量必须完整分配**
    model.addConstrs(
        quicksum(f[o, p, q] for p in vertiports for q in vertiports if p != q) == total_orders[o][2]
        for o in range(len(total_orders))
    )

    # **约束3️⃣：流量只能在选择的航线上分配**
    model.addConstrs(
        f[o, p, q] <= x[o, p, q] * total_orders[o][2]
        for o in range(len(total_orders)) for p in vertiports for q in vertiports if p != q
    )
    u = model.addVars(vertiports, vtype=GRB.CONTINUOUS, name="u")  # 允许超额流量

    for p in vertiports:
        if p in vertiport_states:
            max_capacity = vertiport_states[p].get("avail", float("inf"))
            model.addConstr(
                quicksum(f[o, p, q] for o in range(len(total_orders)) for q in vertiports if p != q) - u[
                    p] <= max_capacity
            )

    for q in vertiports:
        if q in vertiport_states:
            max_capacity = vertiport_states[q].get("avail", float("inf"))
            model.addConstr(
                quicksum(f[o, p, q] for o in range(len(total_orders)) for p in vertiports if p != q) - u[
                    q] <= max_capacity
            )

    # **让 Gurobi 最小化 `u[p]`，防止超量分配**
    model.setObjective(
        quicksum(f[o, p, q] for o in range(len(total_orders)) for p in vertiports for q in vertiports if p != q) -
        quicksum(u[p] for p in vertiports),
        GRB.MAXIMIZE
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
                    if p != q and f[o, p, q].x > 0.5:
                        flow_assigned = f[o, p, q].x
                        gurobi_results.append({
                            "start": p,
                            "end": q,
                            "flow": flow_assigned,
                            "distance": distance_air.get((p, q), 0)  # ✅ 添加 `distance`
                        })
                        total_assigned_flow += flow_assigned
        print(f"Total assigned flow: {total_assigned_flow}")

        # 🚀 计算 Gurobi 分配后的总流量
        total_flow_after = sum(res["flow"] for res in gurobi_results)
        print(f"📊 Gurobi 分配后总流量: {total_flow_after}")

        # 🚨 流量一致性检查
        if abs(total_flow_before - total_flow_after) < 1e-5:
            print(f"✅ 流量一致! 输入: {total_flow_before}, 分配后: {total_flow_after}")
        else:
            print(f"⚠️ 流量不匹配! 输入: {total_flow_before}, 分配后: {total_flow_after}")

    return gurobi_results

