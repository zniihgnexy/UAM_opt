from gurobipy import Model, GRB

# def solve_gurobi(demand_data, banned_solutions=None, get_second_best=False):
#     """
#     Solves the optimization problem with Gurobi and optionally retrieves the second-best solution.
#
#     :param demand_data: List of demands with start, end, flow, and distance.
#     :param banned_solutions: List of solutions to ban, each represented as [(start, end)].
#     :param get_second_best: If True, retrieves the second-best solution from the solution pool.
#     :return: List of paths representing the Gurobi solution.
#     """
#     from numpy import isfinite
#
#     # Filter invalid demand data
#     valid_demand_data = [
#         d for d in demand_data
#         if isfinite(d["flow"]) and isfinite(d["distance"]) and d["flow"] > 0 and d["distance"] > 0
#     ]
#     print(f"Valid demand data: {valid_demand_data}")
#
#     if len(valid_demand_data) != len(demand_data):
#         print("Warning: Invalid demand data removed.")
#         print(f"Invalid entries: {[d for d in demand_data if d not in valid_demand_data]}")
#
#     model = Model("UAM_Optimization")
#
#     # Variables: Assign flow for each demand
#     flow_vars = {
#         (d["start"], d["end"]): model.addVar(vtype=GRB.INTEGER, name=f"flow_{d['start']}_{d['end']}")
#         for d in valid_demand_data
#     }
#
#     # Objective: Minimize total travel cost
#     model.setObjective(
#         sum(d["distance"] * flow_vars[(d["start"], d["end"])] for d in valid_demand_data),
#         GRB.MINIMIZE
#     )
#
#     # Constraints: Add flow capacity constraints
#     # for d in valid_demand_data:
#     #     model.addConstr(flow_vars[(d["start"], d["end"])] <= d["flow"], f"capacity_{d['start']}_{d['end']}")
#
#     # Add banned solution constraints
#     # if banned_solutions:
#     #     for banned in banned_solutions:
#     #         # Ensure banned pairs exist in flow_vars
#     #         banned_pairs = [(b[0], b[1]) for b in banned if (b[0], b[1]) in flow_vars]
#     #         if banned_pairs:
#     #             model.addConstr(
#     #                 sum(flow_vars[p] for p in banned_pairs) <= len(banned_pairs) - 1,
#     #                 f"banned_solution_{banned}"
#     #             )
#
#     # Enable the solution pool
#     model.setParam("PoolSearchMode", 2)  # Enable the solution pool search
#     model.setParam("PoolSolutions", 2)  # Store up to 2 solutions
#
#     # Solve the model
#     model.optimize()
#
#     # Extract results
#     if model.status == GRB.OPTIMAL:
#         solution = []
#         if get_second_best and model.SolCount > 1:
#             # Retrieve the second-best solution
#             model.setParam("SolutionNumber", 1)
#             for start, end, d in ((d["start"], d["end"], d) for d in valid_demand_data):
#                 flow_value = flow_vars[(start, end)].Xn
#                 if isfinite(flow_value) and flow_value > 0:
#                     solution.append({"start": start, "end": end, "flow": flow_value, "distance": d["distance"]})
#                 else:
#                     print(f"DEBUG: No flow or invalid flow from {start} to {end}: {flow_value}")
#         else:
#             # Retrieve the best solution
#             for start, end, d in ((d["start"], d["end"], d) for d in valid_demand_data):
#                 flow_value = flow_vars[(start, end)].X
#                 if isfinite(flow_value) and flow_value > 0:
#                     solution.append({"start": start, "end": end, "flow": flow_value, "distance": d["distance"]})
#                 else:
#                     print(f"DEBUG: No flow or invalid flow from {start} to {end}: {flow_value}")
#         valid_flows = [flow_value for start, end, d in ((d["start"], d["end"], d) for d in valid_demand_data)
#                        if isfinite(flow_vars[(start, end)].X) and flow_vars[(start, end)].X > 0]
#
#         if len(valid_flows) == 0:
#             print("DEBUG: No valid flows found in the solution, coverage_rate will be 0")
#         else:
#             print(f"DEBUG: Valid flows: {valid_flows}")
#
#         return solution
#     else:
#         print("No optimal solution found.")
#         return []

from gurobipy import Model, GRB, quicksum
from gurobipy import Model, GRB
from numpy import isfinite
from collections import defaultdict


from gurobipy import Model, GRB, quicksum
from collections import defaultdict

from gurobipy import Model, GRB, quicksum
from numpy import isfinite
from collections import defaultdict


from gurobipy import Model, GRB, quicksum
from numpy import isfinite

from gurobipy import Model, GRB, quicksum
from numpy import isfinite

from gurobipy import Model, GRB, quicksum

from gurobipy import Model, GRB, quicksum
from numpy import isfinite

from gurobipy import Model, GRB, quicksum
from numpy import isfinite


def solve_gurobi(combined_demand, vertiport_states):
    """
    Gurobi 优化：重新分配流量，确保：
    - ✅ **每个订单可以部分满足**
    - ✅ **总流量尽可能大**
    - ✅ **流量为离散整数**
    - ✅ **遵守停机坪容量限制**
    """

    model = Model("UAM_Optimization")
    model.setParam('OutputFlag', 1)  # 开启求解日志

    # =================== 1. 数据预处理 ===================
    valid_demand_data = [
        (i, d["start"], d["end"], int(d["flow"]), d["distance"])
        for i, d in enumerate(combined_demand)
        if isfinite(d["flow"]) and isfinite(d["distance"]) and d["flow"] > 0 and d["distance"] > 0
    ]

    # 计算原始总需求流量（用于调试）
    total_original_flow = sum(flow for _, _, _, flow, _ in valid_demand_data)
    print(f"原始总需求流量: {total_original_flow}")

    # =================== 2. 创建优化变量 ===================
    # 变量格式: (订单索引, 起点, 终点)
    demand_indices = [(i, start, end) for i, start, end, _, _ in valid_demand_data]

    # 定义整数型决策变量（允许减少流量）
    flow_vars = model.addVars(
        demand_indices,
        vtype=GRB.INTEGER,
        lb=0,
        name="flow"
    )

    # =================== 3. 设置约束条件 ===================
    # 约束1: 每个订单分配流量不超过原始需求
    model.addConstrs(
        flow_vars[i, start, end] <= original_flow
        for i, start, end, original_flow, _ in valid_demand_data
    )

    # 约束2: 每个停机坪出发流量不超过可用载具数
    vertiport_departures = defaultdict(list)
    for i, start, end, flow, _ in valid_demand_data:
        vertiport_departures[start].append(flow_vars[i, start, end])

    for vertiport, state in vertiport_states.items():
        avail = state.get('avail', 0)
        if avail < 0:
            raise ValueError(f"停机坪 {vertiport} 的可用载具数不能为负值")

        if vertiport in vertiport_departures:
            model.addConstr(
                quicksum(vertiport_departures[vertiport]) <= avail,
                name=f"vertiport_cap_{vertiport}"
            )

    # =================== 4. 设置目标函数 ===================
    model.setObjective(
        quicksum(flow_vars),  # 最大化总满足流量
        GRB.MAXIMIZE
    )

    # =================== 5. 求解与结果处理 ===================
    model.optimize()

    if model.status == GRB.OPTIMAL:
        solution = []
        total_optimized_flow = 0

        for i, start, end, _, distance in valid_demand_data:
            var = flow_vars[i, start, end]
            optimized_flow = int(var.X)

            if optimized_flow > 0:
                solution.append({
                    'start': start,
                    'end': end,
                    'flow': optimized_flow,
                    'distance': distance
                })
                total_optimized_flow += optimized_flow

        print(f"优化成功！满足流量: {total_optimized_flow}/{total_original_flow}")
        return solution
    else:
        print(f"求解失败！状态码: {model.status}")
        if model.status == GRB.INFEASIBLE:
            print("模型不可行，建议检查:")
            print("- 停机坪可用载具是否足够")
            print("- 订单需求是否全部为0")
        return []







