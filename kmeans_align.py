import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from scipy.spatial.distance import cdist
import folium
import math

# 网格划分参数
GRID_SIZE = 0.0135  # 网格大小，对应约 1.5 公里
LAT_MIN, LAT_MAX = 37.6, 37.9  # 纬度范围（根据数据调整）
LON_MIN, LON_MAX = -123.0, -122.3  # 经度范围（根据数据调整）

def calculate_grid_center(lat, lon):
    """计算最近的网格中心点"""
    grid_row = int((lat - LAT_MIN) // GRID_SIZE)
    grid_col = int((lon - LON_MIN) // GRID_SIZE)
    grid_lat = LAT_MIN + (grid_row + 0.5) * GRID_SIZE
    grid_lon = LON_MIN + (grid_col + 0.5) * GRID_SIZE
    return grid_lat, grid_lon

def haversine(lat1, lon1, lat2, lon2):
    """计算两个经纬度点之间的 Haversine 距离（单位：公里）"""
    R = 6371  # 地球平均半径，单位：公里
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 1. 加载原始流量数据
data = pd.read_csv("save_od_with_id.csv")

# 2. 合并上下车点
coords = pd.concat([
    data[['lat_on', 'lon_on']].rename(columns={'lat_on': 'lat', 'lon_on': 'lon'}),
    data[['lat_off', 'lon_off']].rename(columns={'lat_off': 'lat', 'lon_off': 'lon'})
]).drop_duplicates()

# 3. 地理边界筛选，去除异常点
coords = coords[
    (coords['lat'] >= LAT_MIN) & (coords['lat'] <= LAT_MAX) &
    (coords['lon'] >= LON_MIN) & (coords['lon'] <= LON_MAX)
]
print(f"筛选后剩余数据点数量：{len(coords)}")

# 4. 使用 K-Means 聚类
k = 10  # 停机坪数量，可根据实际情况调整
kmeans = KMeans(n_clusters=k, random_state=42)
kmeans.fit(coords[['lat', 'lon']])

# 聚类中心点
centroids = kmeans.cluster_centers_

# 每个点的初始聚类标签
coords['cluster_before'] = kmeans.labels_

# 统计调整前每个簇的覆盖点数量
cluster_counts_before = coords['cluster_before'].value_counts().sort_index()

# 5. 调整聚类中心点到最近网格中心
adjusted_centroids = []
grid_ids = []  # 存储网格区域 ID
total_cols = int((LON_MAX - LON_MIN) / GRID_SIZE)  # 网格总列数

for lat, lon in centroids:
    adjusted_lat, adjusted_lon = calculate_grid_center(lat, lon)
    adjusted_centroids.append((adjusted_lat, adjusted_lon))
    # 计算网格行列号
    grid_row = int((adjusted_lat - LAT_MIN) // GRID_SIZE)
    grid_col = int((adjusted_lon - LON_MIN) // GRID_SIZE)
    grid_id = grid_row * total_cols + grid_col  # 生成唯一数值 ID
    grid_ids.append(grid_id)

# 转换为 NumPy 数组
adjusted_centroids = np.array(adjusted_centroids)

# 保存到 DataFrame
vertiport_data = pd.DataFrame({
    "Vertiport": [f"Vertiport_{i+1}" for i in range(len(centroids))],
    "Latitude": adjusted_centroids[:, 0],
    "Longitude": adjusted_centroids[:, 1],
    "Grid_ID": grid_ids  # 存储为唯一数值 ID
})

# 保存为 CSV
vertiport_data.to_csv("adjusted_vertiports_numeric.csv", index=False)
# 重新分配每个点到最近的调整后网格中心
distances_to_adjusted = cdist(coords[['lat', 'lon']].values, adjusted_centroids)
coords['cluster_after'] = np.argmin(distances_to_adjusted, axis=1)

# 统计调整后每个簇的覆盖点数量
cluster_counts_after = coords['cluster_after'].value_counts().sort_index()

# 6. 比较覆盖点数量
comparison = pd.DataFrame({
    'Cluster': range(1, k + 1),
    'Before_Adjustment': cluster_counts_before.values,
    'After_Adjustment': cluster_counts_after.values
})
comparison['Absolute_Error'] = abs(comparison['Before_Adjustment'] - comparison['After_Adjustment'])
comparison['Relative_Error (%)'] = (comparison['Absolute_Error'] / comparison['Before_Adjustment']) * 100

# 7. 计算中心点之间的距离
distance_matrix = []
for i, (lat1, lon1) in enumerate(adjusted_centroids):
    row = []
    for j, (lat2, lon2) in enumerate(adjusted_centroids):
        if i == j:
            row.append(0)  # 自己到自己的距离为 0
        else:
            row.append(haversine(lat1, lon1, lat2, lon2))  # 计算 Haversine 距离
    distance_matrix.append(row)

# 转换为 DataFrame 并保存为 CSV
distance_df = pd.DataFrame(distance_matrix, columns=[f"Cluster {i+1}" for i in range(k)],
                           index=[f"Cluster {i+1}" for i in range(k)])
# distance_df.to_csv('centroid_distance_matrix.csv', index=True)
# print("停机坪中心点之间的距离矩阵已保存为 'centroid_distance_matrix.csv'")
#
# # 输出比较结果
# print("调整前后覆盖点数量比较：")
# print(comparison)
#
# # 保存比较结果到 CSV 文件
# comparison.to_csv('cluster_coverage_comparison.csv', index=False)
# print("调整前后覆盖点数量比较已保存为 'cluster_coverage_comparison.csv'")

# 保存最终的停机坪信息到文件
final_vertiports = pd.DataFrame({
    'Vertiport': [f"Vertiport_{i+1}" for i in range(len(adjusted_centroids))],
    'Latitude': adjusted_centroids[:, 0],
    'Longitude': adjusted_centroids[:, 1],
    'Grid_ID': grid_ids  # 对应的网格区域 ID
})

# 保存到 CSV 文件
final_vertiports.to_csv('final_vertiports_with_grid.csv', index=False)
print("最终的停机坪和网格区域 ID 已保存为 'final_vertiports_with_grid.csv'")

# # 8. 可视化结果
# # 初始化地图，中心为数据平均位置
# m = folium.Map(location=[coords['lat'].mean(), coords['lon'].mean()], zoom_start=12)
#
# # 添加调整后的聚类中心点到地图
# for i, (lat, lon) in enumerate(adjusted_centroids):
#     folium.Marker(
#         location=[lat, lon],
#         popup=f"停机坪 {i+1}: ({lat:.5f}, {lon:.5f}), "
#               f"覆盖点数量: {cluster_counts_after[i]}, "
#               f"误差: {comparison['Absolute_Error'].iloc[i]}",
#         icon=folium.Icon(color="blue", icon="info-sign")
#     ).add_to(m)
#
# # 添加原始点到地图
# for _, row in coords.iterrows():
#     folium.CircleMarker(
#         location=[row['lat'], row['lon']],
#         radius=2,
#         color='green',
#         fill=True,
#         fill_opacity=0.5
#     ).add_to(m)
#
# # 保存地图
# m.save("adjusted_kmeans_candidates_map.html")
# print("地图已保存为 'adjusted_kmeans_candidates_map.html'")
