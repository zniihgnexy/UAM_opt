from typing import List, Dict
from distance_battery import calculate_distance
from gurobi_solver import solve_gurobi

import pandas as pd
from typing import List, Dict
from distance_battery import calculate_distance


def regenerate_solution(t: int, unmet_demand: List, vehicle_states: Dict, vertiport_states: Dict,
                        original_solution: List[Dict]) -> List[Dict]:
    """
    Regenerate a new Gurobi solution, optionally retrieving the second-best solution.

    :param t: Current time step.
    :param unmet_demand: Unmet demand from the previous iteration (tuples of (start, end, flow)).
    :param vehicle_states: Current states of vehicles.
    :param vertiport_states: Current states of vertiports.
    :param original_solution: The original solution to ban.
    :return: A new solution that excludes the banned solution.
    """
    print(f"Regenerating solution for iteration {t + 1}...")

    # 读取当前时间步的新需求（从CSV文件中）
    csv_file_path = "updated_flow_data_with_corrected_distances.csv"
    data = pd.read_csv(csv_file_path)

    # 根据时间步 `t` 选择当前的需求数据
    data_t = data[data["Time"] == f"T{t}"]

    # 创建新需求列表
    new_demand = [
        {"start": row["start"], "end": row["end"], "flow": row["flow"], "distance": row["distance"]}
        for _, row in data_t.iterrows()
    ]

    # 合并上一轮未满足的需求和新需求
    combined_demand = [
                          {"start": d[0], "end": d[1], "flow": d[2], "distance": calculate_distance(d[0], d[1])}
                          for d in unmet_demand
                      ] + new_demand

    # 检查是否有需求数据
    if not combined_demand:
        print("No demand data available.")
        return []
    # 调用 Gurobi 求解器并请求次优解（可选）
    # new_solution = solve_gurobi(combined_demand, banned_solutions=None, get_second_best=get_second_best)
    new_solution = solve_gurobi(combined_demand,vertiport_states)

    # 打印 Gurobi 结果
    print("Gurobi results:", new_solution)

    return new_solution

