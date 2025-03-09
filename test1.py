import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

# === 加载数据 ===
file_path = "hh-odflow.npz"
data = np.load(file_path)
flow_data = data['arr_0']

# 提取第 82 个时间片段的流量矩阵
time_index = 82  # 选择第 82 个时间片段
flow_matrix = flow_data[time_index]
# 提取所有流量值（包括零）
all_flow_values = flow_matrix[flow_matrix > 0]  # 只取非零流量

# 绘制流量的直方图
plt.figure(figsize=(12, 6))
sns.histplot(all_flow_values, kde=True, color='blue', bins=30)
plt.title(f"Flow Distribution at Time T{time_index + 1}")
plt.xlabel("Flow Value")
plt.ylabel("Frequency")
plt.show()
