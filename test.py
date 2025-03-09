import numpy as np
import pandas as pd

# === 加载数据 ===
file_path = "hh-odflow.npz"
data = np.load(file_path)
flow_data = data['arr_0']

# 读取停机坪数据（手动输入）
vertiport_info = pd.DataFrame({
    "Vertiport": [f"Vertiport_{i+1}" for i in range(10)],
    "Grid_ID": [755, 96, 707, 604, 757, 650, 653, 499, 248, 706]
})

# 统计每个停机坪作为起点/终点的订单数量和流量
vertiport_stats = {}

for grid_id in vertiport_info["Grid_ID"]:
    # 统计该 `Grid_ID` 作为起点的流量
    as_origin = np.sum(flow_data[:, grid_id, :])
    order_count_as_origin = np.count_nonzero(flow_data[:, grid_id, :])

    # 统计该 `Grid_ID` 作为终点的流量
    as_destination = np.sum(flow_data[:, :, grid_id])
    order_count_as_destination = np.count_nonzero(flow_data[:, :, grid_id])

    # 存入字典
    vertiport_stats[grid_id] = {
        "Vertiport": vertiport_info[vertiport_info["Grid_ID"] == grid_id]["Vertiport"].values[0],
        "Total_Orders_As_Origin": order_count_as_origin,
        "Total_Flow_As_Origin": as_origin,
        "Total_Orders_As_Destination": order_count_as_destination,
        "Total_Flow_As_Destination": as_destination
    }

# 转换为 DataFrame 并显示
vertiport_df = pd.DataFrame.from_dict(vertiport_stats, orient="index")

vertiport_df.to_csv("vertiport_statistics.csv", index=False)
