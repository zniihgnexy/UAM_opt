import pandas as pd

# # 读取原始CSV文件
# file_path = 'save_od_with_id.csv'
# data = pd.read_csv(file_path)
#
# # 过滤掉距离小于6公里的记录
# filtered_data = data[data['cumulative_distance'] >= 6]
#
# # 保存处理后的数据到新的CSV文件
# filtered_file_path = '6km_filtered_save_od_with_id.csv'
# filtered_data.to_csv(filtered_file_path, index=False)
#
# # 显示处理前后的数据变化
# original_count = len(data)
# filtered_count = len(filtered_data)
#
# print(f"Original data count: {original_count}")
# print(f"Filtered data count: {filtered_count}")
# import pandas as pd
# from sklearn.cluster import KMeans
# import folium
# from folium import plugins
#
# # 读取过滤后的CSV文件
# filtered_file_path = '6km_filtered_save_od_with_id.csv'
# data = pd.read_csv(filtered_file_path)
# print(data.columns)
# coordinates = data[['start_lat', 'start_lng']]
#
# # 进行KMeans聚类，假设选择聚类成5个类（你可以根据需要调整聚类数目）
# kmeans = KMeans(n_clusters=5, random_state=42)
# data['cluster'] = kmeans.fit_predict(coordinates)
#
# # 获取聚类中心
# centroids = kmeans.cluster_centers_
# cluster_coordinates = {}
# # 创建地图
# map_center = [data['start_lat'].mean(), data['start_lng'].mean()]
# m = folium.Map(location=map_center, zoom_start=12)
#
# # 绘制聚类中心
# for idx, centroid in enumerate(centroids):
#     folium.Marker(
#         location=[centroid[0], centroid[1]],
#         popup=f'Cluster {idx+1}',
#         icon=folium.Icon(color='blue', icon='info-sign')
#     ).add_to(m)
#
# # 输出每个簇的经纬度信息
# for cluster_num, coords in cluster_coordinates.items():
#     print(f'Cluster {cluster_num} coordinates:')
#     print(coords)  # 打印每个簇的经纬度信息
# # 保存地图为HTML文件
# map_file_path = '6kmcluster_centers_map_5.html'
# m.save(map_file_path)


# import pandas as pd
# import folium
# import numpy as np
#
# # 读取过滤后的CSV文件
# filtered_file_path = '6km_filtered_save_od_with_id.csv'
# data = pd.read_csv(filtered_file_path)
#
# # 定义网格大小（1.5km ≈ 0.01348度）
# GRID_SIZE = 0.01348
#
#
# # 函数：计算网格ID
# def calculate_grid_id(lat, lon, grid_size):
#     grid_lat = np.floor(lat / grid_size)
#     grid_lon = np.floor(lon / grid_size)
#     return int(grid_lat), int(grid_lon)
#
#
# # 为起始点和终点计算网格ID
# data['start_grid_id'] = data.apply(lambda row: calculate_grid_id(row['start_lat'], row['start_lng'], GRID_SIZE), axis=1)
# data['end_grid_id'] = data.apply(lambda row: calculate_grid_id(row['end_lat'], row['end_lng'], GRID_SIZE), axis=1)
#
# # 为每个网格生成唯一的网格ID
# data['start_grid_unique_id'] = data['start_grid_id'].apply(lambda x: f"{x[0]}_{x[1]}")
# data['end_grid_unique_id'] = data['end_grid_id'].apply(lambda x: f"{x[0]}_{x[1]}")
#
# # 打印数据中的一些基本信息
# print(f"Total data points: {len(data)}")
# print(f"Unique start grid IDs: {len(data['start_grid_unique_id'].unique())}")
# print(f"Unique end grid IDs: {len(data['end_grid_unique_id'].unique())}")
#
# # 创建一个地图，并将其中心点设置为数据的平均纬度和经度
# map_center = [data['start_lat'].mean(), data['start_lng'].mean()]
# m = folium.Map(location=map_center, zoom_start=12)
#
# # 可视化网格中心而不是每个数据点的起始位置
# # 为每个网格ID绘制标记
# unique_start_grid_ids = data['start_grid_unique_id'].unique()
# for grid_id in unique_start_grid_ids:
#     # 获取该网格的经纬度范围
#     grid_data = data[data['start_grid_unique_id'] == grid_id]
#     center_lat = grid_data['start_lat'].mean()
#     center_lng = grid_data['start_lng'].mean()
#
#     # 在地图上绘制网格中心的标记
#     folium.Marker(
#         location=[center_lat, center_lng],
#         popup=f"Grid ID: {grid_id}",
#         icon=folium.Icon(color='blue', icon='info-sign')
#     ).add_to(m)
#
# # 保存地图为HTML文件
# map_file_path = 'grid_map_visualization.html'
# m.save(map_file_path)

#

# 保存更新后的数据为新的CSV文件
# updated_file_path = '6km_with_grid_ids_1_5km.csv'
# data.to_csv(updated_file_path, index=False)

# import pandas as pd
# import folium
# import numpy as np
#
# # 读取过滤后的CSV文件
# filtered_file_path = '6km_filtered_save_od_with_id.csv'
# data = pd.read_csv(filtered_file_path)
#
# # 定义网格大小（每个网格大约 1.5km）
# GRID_SIZE = 0.01348
#
# # 创建地图，设置中心点
# map_center = [data['start_lat'].mean(), data['start_lng'].mean()]
# m = folium.Map(location=map_center, zoom_start=12)
#
# # 计算网格的范围并绘制矩形
# # 计算经纬度范围
# min_lat = data['start_lat'].min()
# max_lat = data['start_lat'].max()
# min_lng = data['start_lng'].min()
# max_lng = data['start_lng'].max()
#
# # 创建网格
# lat_range = np.arange(min_lat, max_lat, GRID_SIZE)
# lng_range = np.arange(min_lng, max_lng, GRID_SIZE)
#
# # 为每个网格绘制矩形
# for lat in lat_range:
#     for lng in lng_range:
#         # 每个网格的边界
#         bounds = [
#             [lat, lng],  # 左下角
#             [lat + GRID_SIZE, lng + GRID_SIZE]  # 右上角
#         ]
#         # 创建矩形并添加到地图
#         folium.Rectangle(bounds, color='blue', weight=1, fill=True, fill_opacity=0.1).add_to(m)
#
# # 保存地图为HTML文件
# map_file_path = '6km_grid_map.html'
# m.save(map_file_path)
#
import pandas as pd
import folium
import numpy as np
from sklearn.cluster import KMeans

# # 读取过滤后的CSV文件
# filtered_file_path = '6km_filtered_save_od_with_id.csv'
# data = pd.read_csv(filtered_file_path)
#
# # 定义网格大小（1.5km ≈ 0.01348度）
# GRID_SIZE = 0.01348
#
# # 函数：计算网格ID
# def calculate_grid_id(lat, lon, grid_size):
#     grid_lat = np.floor(lat / grid_size)
#     grid_lon = np.floor(lon / grid_size)
#     return int(grid_lat), int(grid_lon)
#
# # 为起始点和终点计算网格ID
# data['start_grid_id'] = data.apply(lambda row: calculate_grid_id(row['start_lat'], row['start_lng'], GRID_SIZE), axis=1)
# data['end_grid_id'] = data.apply(lambda row: calculate_grid_id(row['end_lat'], row['end_lng'], GRID_SIZE), axis=1)
#
# # KMeans 聚类
# coordinates = data[['start_lat', 'start_lng']]  # 聚类使用的坐标列（起点经纬度）
# kmeans = KMeans(n_clusters=10, random_state=42)  # 设定聚类数为5，可以根据需要调整
# data['cluster'] = kmeans.fit_predict(coordinates)
#
# # 获取聚类中心的经纬度
# centroids = kmeans.cluster_centers_
#
# # 为每个聚类中心计算网格 ID
# centroid_grid_ids = [calculate_grid_id(centroid[0], centroid[1], GRID_SIZE) for centroid in centroids]
#
# # 输出聚类中心的经纬度和网格 ID
# for idx, (centroid, grid_id) in enumerate(zip(centroids, centroid_grid_ids)):
#     print(f"Cluster {idx+1}:")
#     print(f"  Centroid Latitude: {centroid[0]}, Longitude: {centroid[1]}")
#     print(f"  Grid ID: {grid_id}")
#
# # 创建地图，并将其中心点设置为数据的平均纬度和经度
# map_center = [data['start_lat'].mean(), data['start_lng'].mean()]
# m = folium.Map(location=map_center, zoom_start=12)
#
# # 绘制聚类中心的标记，并显示其经纬度和网格ID
# for idx, (centroid, grid_id) in enumerate(zip(centroids, centroid_grid_ids)):
#     folium.Marker(
#         location=[centroid[0], centroid[1]],
#         popup=f"Cluster {idx+1} - Grid ID: {grid_id}",
#         icon=folium.Icon(color='red', icon='info-sign')
#     ).add_to(m)
#
# # 保存地图为HTML文件
# map_file_path = 'cluster_centers_map_with_grid_ids_10.html'
# m.save(map_file_path)
from geopy.distance import geodesic
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# # 读取过滤后的CSV文件
# filtered_file_path = '6km_filtered_save_od_with_id.csv'
# data = pd.read_csv(filtered_file_path)
#
# # 定义网格大小（1.5km ≈ 0.01348度）
# GRID_SIZE = 0.01348
#
# # 函数：计算网格ID
# def calculate_grid_id(lat, lon, grid_size):
#     grid_lat = np.floor(lat / grid_size)
#     grid_lon = np.floor(lon / grid_size)
#     return int(grid_lat), int(grid_lon)
#
# # 为起始点和终点计算网格ID
# data['start_grid_id'] = data.apply(lambda row: calculate_grid_id(row['start_lat'], row['start_lng'], GRID_SIZE), axis=1)
# data['end_grid_id'] = data.apply(lambda row: calculate_grid_id(row['end_lat'], row['end_lng'], GRID_SIZE), axis=1)
#
# # KMeans 聚类
# coordinates = data[['start_lat', 'start_lng']]  # 聚类使用的坐标列（起点经纬度）
# kmeans = KMeans(n_clusters=10, random_state=42)  # 设定聚类数为10
# data['cluster'] = kmeans.fit_predict(coordinates)
#
# # 获取聚类中心的经纬度
# centroids = kmeans.cluster_centers_
# # 自动调整簇6和簇7的聚类中心
# # 使用加权平均计算聚类中心：根据距离重新计算聚类中心
# def calculate_weighted_centroid(cluster_data):
#     """
#     计算簇的加权中心，权重为点到聚类中心的距离（距离越近，权重越大）
#     """
#     cluster_lat = cluster_data['start_lat']
#     cluster_lon = cluster_data['start_lng']
#
#     # 计算每个点到聚类中心的距离
#     dist = [geodesic((lat, lon), (cluster_lat.mean(), cluster_lon.mean())).km for lat, lon in
#             zip(cluster_lat, cluster_lon)]
#
#     # 计算加权平均纬度和经度（权重为距离的倒数）
#     weight = [1 / d if d != 0 else 1e-6 for d in dist]  # 避免除以0
#     weighted_lat = np.average(cluster_lat, weights=weight)
#     weighted_lon = np.average(cluster_lon, weights=weight)
#
#     return weighted_lat, weighted_lon
#
#
# # 自动调整簇6和簇7的聚类中心
# adjusted_centroids = []
# for idx, centroid in enumerate(centroids):
#     if idx == 5:  # 聚类6（0-based index是5）
#         # 重新计算簇6的加权聚类中心
#         cluster_points = data[data['cluster'] == 5]
#         new_lat, new_lon = calculate_weighted_centroid(cluster_points)
#         adjusted_centroids.append((new_lat, new_lon))  # 使用新的聚类中心
#     elif idx == 6:  # 聚类7（0-based index是6）
#         # 重新计算簇7的加权聚类中心
#         cluster_points = data[data['cluster'] == 6]
#         new_lat, new_lon = calculate_weighted_centroid(cluster_points)
#         adjusted_centroids.append((new_lat, new_lon))  # 使用新的聚类中心
#     else:
#         adjusted_centroids.append(centroid)  # 对其他簇保持原聚类中心
# # 获取数据中的最大和最小经纬度
# min_lat = data['start_lat'].min()
# max_lat = data['start_lat'].max()
# min_lon = data['start_lng'].min()
# max_lon = data['start_lng'].max()
#
# print(f"Latitude Range: {min_lat} to {max_lat}")
# print(f"Longitude Range: {min_lon} to {max_lon}")
#
# # 设置一个合理的经纬度范围（例如，基于数据的实际范围，稍微宽松一些）
# lat_min = min_lat - 0.01  # 向下扩展一点
# lat_max = max_lat + 0.01  # 向上扩展一点
# lon_min = min_lon - 0.01  # 向左扩展一点
# lon_max = max_lon + 0.01  # 向右扩展一点
# #
# # # 排除掉位于这个范围之外的聚类中心
# # valid_centroids = []
# # for centroid in centroids:
# #     lat, lon = centroid
# #     if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
# #         valid_centroids.append(centroid)
# #
# # # 输出有效的聚类中心
# # print("Valid cluster centroids within data's geographical range:")
# # for idx, centroid in enumerate(valid_centroids):
# #     print(f"Cluster {idx+1}: Centroid Latitude: {centroid[0]}, Longitude: {centroid[1]}")
# # # 创建地图，并将其中心点设置为数据的平均纬度和经度
# # map_center = [data['start_lat'].mean(), data['start_lng'].mean()]
# # m = folium.Map(location=map_center, zoom_start=12)
#
# # 输出调整后的聚类中心
# print("Adjusted Cluster Centroids:")
# # for idx, centroid in enumerate(adjusted_centroids):
# #     print(f"Cluster {idx+1}: Adjusted Centroid Latitude: {centroid[0]}, Longitude: {centroid[1]}")
# # 为每个调整后的聚类中心计算网格ID
# adjusted_centroid_grid_ids = [calculate_grid_id(centroid[0], centroid[1], GRID_SIZE) for centroid in adjusted_centroids]
#
# # 输出调整后的聚类中心及其对应的网格ID
# print("Adjusted Cluster Centroids and their Grid IDs:")
# for idx, (centroid, grid_id) in enumerate(zip(adjusted_centroids, adjusted_centroid_grid_ids)):
#     print(f"Cluster {idx+1}: Centroid Latitude: {centroid[0]}, Longitude: {centroid[1]}, Grid ID: {grid_id}")
# # 创建地图，并将其中心点设置为数据的平均纬度和经度
# map_center = [data['start_lat'].mean(), data['start_lng'].mean()]
# m = folium.Map(location=map_center, zoom_start=12)
#
# # 绘制调整后的聚类中心
# for idx, centroid in enumerate(adjusted_centroids):
#     folium.Marker(
#         location=[centroid[0], centroid[1]],
#         popup=f"Cluster {idx+1}",
#         icon=folium.Icon(color='red', icon='info-sign')
#     ).add_to(m)
#
# # 保存地图为HTML文件
# map_file_path = 'valid_cluster_centroids_map.html'
# m.save(map_file_path)


# import pandas as pd
# import numpy as np
#
# # 定义网格大小
# GRID_SIZE = 0.01348  # 1.5km ≈ 0.01348度
#
# # 网格划分函数
# def grid_id(lat, lon, min_lat, min_lon, grid_size):
#     # 计算网格位置
#     xx = int((lon - min_lon) / grid_size)
#     yy = int((lat - min_lat) / grid_size)
#     return xx, yy
# def deal_id(df):
#     # 合并两列的唯一值（去除 NaN）
#     unique_values = sorted(set(df['upid'].dropna()).union(set(df['offid'].dropna())))
#
#     # 创建映射字典
#     value_map = {v: i for i, v in enumerate(unique_values)}
#
#     # 应用映射到两列
#     df['upid'] = df['upid'].map(value_map).fillna(np.nan)
#     df['offid'] = df['offid'].map(value_map).fillna(np.nan)
#
#     # 将映射字典转换为 DataFrame
#     map_df = pd.DataFrame.from_dict(value_map, orient='index', columns=['Mapped_Value'])
#     map_df.reset_index(inplace=True)
#     map_df.columns = ['Original_Value', 'Mapped_Value']
#
#     # 保存映射字典到 CSV 文件
#     map_df.to_csv('6km_value_mapping.csv', index=False)
#     return df, len(value_map)
# # 网格化过程
# def process_grid_data(input_file, output_file):
#     # 读取原始 CSV 文件
#     print(f"Reading data from {input_file}...")
#     data = pd.read_csv(input_file)
#     # 打印列名以调试
#     print(f"Columns in the data: {data.columns.tolist()}")
#
#     # 获取经纬度的最小和最大值
#     print("Calculating latitude and longitude boundaries...")
#     min_lat = min(data['start_lat'].min(), data['end_lat'].min())
#     max_lat = max(data['start_lat'].max(), data['end_lat'].max())
#     min_lon = min(data['start_lng'].min(), data['end_lng'].min())
#     max_lon = max(data['start_lng'].max(), data['end_lng'].max())
#
#     # 打印经纬度的范围
#     print(f"Latitude range: {min_lat} to {max_lat}")
#     print(f"Longitude range: {min_lon} to {max_lon}")
#
#     # 计算网格划分的最大值
#     xl = int((max_lon - min_lon) / GRID_SIZE)
#     yl = int((max_lat - min_lat) / GRID_SIZE)
#     print(f"Grid dimensions: {xl} x {yl}")
#
#     # 计算起点的网格 ID
#     print("Calculating grid ID for pickup locations...")
#     data[['xx_on', 'yy_on']] = data.apply(
#         lambda row: grid_id(row['start_lat'], row['start_lng'], min_lat, min_lon, GRID_SIZE), axis=1,
#         result_type="expand")
#     data['upid'] = data['xx_on'] + xl * data['yy_on']
#     print(f"Generated {len(data)} grid IDs for pickup locations.")
#
#     # 计算终点的网格 ID
#     print("Calculating grid ID for dropoff locations...")
#     data[['xx_off', 'yy_off']] = data.apply(
#         lambda row: grid_id(row['end_lat'], row['end_lng'], min_lat, min_lon, GRID_SIZE), axis=1, result_type="expand")
#     data['offid'] = data['xx_off'] + xl * data['yy_off']
#     print(f"Generated {len(data)} grid IDs for dropoff locations.")
#
#     # 调用 deal_id 函数进行网格 ID 映射
#     data, lenid = deal_id(data)
#
#     # 打印映射后的 ID 数量
#     print(f"Number of unique grid IDs after mapping: {lenid}")
#
#     # 保存处理后的数据到新的 CSV 文件
#     print(f"Saving processed data to {output_file}...")
#     data.to_csv(output_file, index=False)
#
#     # 输出一些信息
#     print(f"Processing complete. Processed data saved to {output_file}")
#     print(f"Grid size: {GRID_SIZE} degrees, Total number of records: {len(data)}")
#
# # 调用处理函数，输入文件路径和输出文件路径
# process_grid_data('6km_filtered_save_od_with_id.csv', '6km_with_grid_ids.csv')


# import pandas as pd
# import numpy as np
# from sklearn.cluster import KMeans
#
# # 定义网格大小
# GRID_SIZE = 0.01348  # 1.5km ≈ 0.01348度
#
#
# # 网格划分函数
# def grid_id(lat, lon, min_lat, min_lon, grid_size):
#     # 计算网格位置
#     xx = int((lon - min_lon) / grid_size)
#     yy = int((lat - min_lat) / grid_size)
#     return xx, yy
#
#
# # 处理网格 ID 映射的函数
# def deal_id(df):
#     # 合并两列的唯一值（去除 NaN）
#     unique_values = sorted(set(df['upid'].dropna()).union(set(df['offid'].dropna())))
#
#     # 创建映射字典
#     value_map = {v: i for i, v in enumerate(unique_values)}
#
#     # 应用映射到两列
#     df['upid'] = df['upid'].map(value_map).fillna(np.nan)
#     df['offid'] = df['offid'].map(value_map).fillna(np.nan)
#
#     # 将映射字典转换为 DataFrame
#     map_df = pd.DataFrame.from_dict(value_map, orient='index', columns=['Mapped_Value'])
#     map_df.reset_index(inplace=True)
#     map_df.columns = ['Original_Value', 'Mapped_Value']
#
#     # 保存映射字典到 CSV 文件
#     map_df.to_csv('6km_value_mapping.csv', index=False)
#     return df, len(value_map)
#
#
# # 计算聚类中心的网格 ID
# def get_centroid_grid_ids(centroids, min_lat, min_lon, grid_size):
#     # 计算每个聚类中心的网格 ID
#     centroid_grid_ids = []
#     for centroid in centroids:
#         lat, lon = centroid
#         grid_x, grid_y = grid_id(lat, lon, min_lat, min_lon, grid_size)
#         centroid_grid_ids.append((lat, lon, grid_x, grid_y))
#     return centroid_grid_ids
# def visualize_centroids(centroid_grid_ids, output_map_file):
#     # 创建地图，设置为聚类中心的平均位置
#     map_center = [np.mean([centroid[0] for centroid in centroid_grid_ids]), np.mean([centroid[1] for centroid in centroid_grid_ids])]
#     m = folium.Map(location=map_center, zoom_start=12)
#
#     # 添加聚类中心标记
#     for idx, (lat, lon, grid_x, grid_y) in enumerate(centroid_grid_ids):
#         folium.Marker(
#             location=[lat, lon],
#             popup=f"Cluster {idx+1} - Latitude: {lat}, Longitude: {lon}, Grid ID: ({grid_x}, {grid_y})",
#             icon=folium.Icon(color='red', icon='info-sign')
#         ).add_to(m)
#
#     # 保存地图为 HTML 文件
#     m.save(output_map_file)
#     print(f"Map with centroids saved to {output_map_file}")
#
# # 网格化过程并进行聚类
# def process_grid_data_with_clustering(input_file, output_file, n_clusters=5,map_output_file='centroids_map.html'):
#     # 读取原始 CSV 文件
#     print(f"Reading data from {input_file}...")
#     data = pd.read_csv(input_file)
#
#     # 打印列名以调试
#     print(f"Columns in the data: {data.columns.tolist()}")
#
#     # 获取经纬度的最小和最大值
#     print("Calculating latitude and longitude boundaries...")
#     min_lat = min(data['start_lat'].min(), data['end_lat'].min())
#     max_lat = max(data['start_lat'].max(), data['end_lat'].max())
#     min_lon = min(data['start_lng'].min(), data['end_lng'].min())
#     max_lon = max(data['start_lng'].max(), data['end_lng'].max())
#
#     # 打印经纬度的范围
#     print(f"Latitude range: {min_lat} to {max_lat}")
#     print(f"Longitude range: {min_lon} to {max_lon}")
#
#     # 计算网格划分的最大值
#     xl = int((max_lon - min_lon) / GRID_SIZE)
#     yl = int((max_lat - min_lat) / GRID_SIZE)
#     print(f"Grid dimensions: {xl} x {yl}")
#
#     # 计算起点的网格 ID
#     print("Calculating grid ID for pickup locations...")
#     data[['xx_on', 'yy_on']] = data.apply(
#         lambda row: grid_id(row['start_lat'], row['start_lng'], min_lat, min_lon, GRID_SIZE), axis=1,
#         result_type="expand")
#     data['upid'] = data['xx_on'] + xl * data['yy_on']
#     print(f"Generated {len(data)} grid IDs for pickup locations.")
#
#     # 计算终点的网格 ID
#     print("Calculating grid ID for dropoff locations...")
#     data[['xx_off', 'yy_off']] = data.apply(
#         lambda row: grid_id(row['end_lat'], row['end_lng'], min_lat, min_lon, GRID_SIZE), axis=1, result_type="expand")
#     data['offid'] = data['xx_off'] + xl * data['yy_off']
#     print(f"Generated {len(data)} grid IDs for dropoff locations.")
#
#     # 调用 deal_id 函数进行网格 ID 映射
#     data, lenid = deal_id(data)
#
#     # 打印映射后的 ID 数量
#     print(f"Number of unique grid IDs after mapping: {lenid}")
#
#     # 聚类：假设我们选择5个聚类中心（你可以根据需要调整聚类数目）
#     coordinates = data[['start_lat', 'start_lng']]  # 聚类使用的坐标列（起点经纬度）
#     kmeans = KMeans(n_clusters=n_clusters, random_state=42)  # 聚类
#     data['cluster'] = kmeans.fit_predict(coordinates)
#
#     # 获取聚类中心的经纬度
#     centroids = kmeans.cluster_centers_
#
#     # 计算每个聚类中心的网格 ID
#     print("Calculating grid IDs for cluster centroids...")
#     centroid_grid_ids = get_centroid_grid_ids(centroids, min_lat, min_lon, GRID_SIZE)
#
#     # 打印每个聚类中心的经纬度和对应的网格 ID
#     for idx, (lat, lon, grid_x, grid_y) in enumerate(centroid_grid_ids):
#         print(f"Cluster {idx + 1} centroid: Latitude: {lat}, Longitude: {lon}, Grid ID: ({grid_x}, {grid_y})")
#         # 可视化聚类中心
#
#     visualize_centroids(centroid_grid_ids, map_output_file)
#
#     # 保存处理后的数据到新的 CSV 文件
#     print(f"Saving processed data to {output_file}...")
#     data.to_csv(output_file, index=False)
#
#     # 输出一些信息
#     print(f"Processing complete. Processed data saved to {output_file}")
#     print(f"Grid size: {GRID_SIZE} degrees, Total number of records: {len(data)}")
#
#
# # 调用处理函数，输入文件路径和输出文件路径
# process_grid_data_with_clustering('6km_filtered_save_od_with_id.csv', '6km_with_grid_ids.csv',  n_clusters=5, map_output_file='6km——5centroids_map.html')
# import pandas as pd
# import numpy as np
# from sklearn.cluster import KMeans
# import folium
#
# # 定义网格大小
# GRID_SIZE = 0.01348  # 1.5km ≈ 0.01348度
#
#
# # 网格划分函数
# def grid_id(lat, lon, min_lat, min_lon, grid_size):
#     # 计算网格位置
#     xx = int((lon - min_lon) / grid_size)
#     yy = int((lat - min_lat) / grid_size)
#     return xx, yy
#
#
# # 重新生成映射文件
# def generate_mapping_file(df):
#     # 为每个网格 ID 生成唯一的标识符
#     unique_grid_ids = sorted(set(df['upid'].dropna()).union(set(df['offid'].dropna())))
#
#     # 创建映射字典
#     value_map = {v: i for i, v in enumerate(unique_grid_ids)}
#
#     # 将映射字典转换为 DataFrame
#     map_df = pd.DataFrame.from_dict(value_map, orient='index', columns=['Mapped_Value'])
#     map_df.reset_index(inplace=True)
#     map_df.columns = ['Original_Value', 'Mapped_Value']
#
#     # 保存映射字典到 CSV 文件
#     map_df.to_csv('6km_value_mapping.csv', index=False)
#     return map_df
#
#
# # 网格化处理
# def process_grid_data(nyc_taxi_data):
#     # 获取经纬度的最小和最大值
#     min_lat = min(nyc_taxi_data['start_lat'].min(), nyc_taxi_data['end_lat'].min())
#     max_lat = max(nyc_taxi_data['start_lat'].max(), nyc_taxi_data['end_lat'].max())
#     min_lon = min(nyc_taxi_data['start_lng'].min(), nyc_taxi_data['end_lng'].min())
#     max_lon = max(nyc_taxi_data['start_lng'].max(), nyc_taxi_data['end_lng'].max())
#
#     # 计算经纬度网格 ID
#     nyc_taxi_data[['xx_on', 'yy_on']] = nyc_taxi_data.apply(
#         lambda row: grid_id(row['start_lat'], row['start_lng'], min_lat, min_lon, GRID_SIZE), axis=1,
#         result_type="expand")
#     xl = int((max_lon - min_lon) / GRID_SIZE)
#     yl = int((max_lat - min_lat) / GRID_SIZE)
#     nyc_taxi_data['upid'] = nyc_taxi_data['xx_on'] + xl * nyc_taxi_data['yy_on']
#
#     nyc_taxi_data[['xx_off', 'yy_off']] = nyc_taxi_data.apply(
#         lambda row: grid_id(row['end_lat'], row['end_lng'], min_lat, min_lon, GRID_SIZE), axis=1, result_type="expand")
#     nyc_taxi_data['offid'] = nyc_taxi_data['xx_off'] + xl * nyc_taxi_data['yy_off']
#
#     return nyc_taxi_data
#
# # 主函数：网格化并生成映射文件
# def main(input_file, output_file):
#     # 读取原始数据
#     nyc_taxi_data = pd.read_csv(input_file)
#
#     # 处理网格数据并计算网格 ID
#     nyc_taxi_data = process_grid_data(nyc_taxi_data)
#
#     # 生成新的映射文件
#     mapping_df = generate_mapping_file(nyc_taxi_data)
#
#     # 打印映射文件的大小
#     print(f"Generated {len(mapping_df)} unique grid IDs in the mapping file.")
#
#     # 保存处理后的数据
#     nyc_taxi_data.to_csv(output_file, index=False)
#     print(f"Processed data saved to {output_file}")
#
#
# # 调用函数，输入文件路径和输出文件路径
# main('6km_filtered_save_od_with_id.csv', 'processed_taxi_data.csv')
#
# import pandas as pd
#
# # 读取 processed_taxi_data.csv 和 mapping 文件
# processed_file = 'processed_taxi_data.csv'
# mapping_file = '6km_value_mapping.csv'
#
# # 加载数据
# taxi_data = pd.read_csv(processed_file)
# mapping_df = pd.read_csv(mapping_file)
#
# # 打印列名以确保正确加载
# print(f"Columns in processed_taxi_data: {taxi_data.columns.tolist()}")
#
# # 创建一个映射字典，将 Original_Value 映射到 Mapped_Value
# mapping_dict = dict(zip(mapping_df['Original_Value'], mapping_df['Mapped_Value']))
#
# # 使用映射字典替换 upid 和 offid 列的值
# taxi_data['upid'] = taxi_data['upid'].map(mapping_dict).fillna(taxi_data['upid'])
# taxi_data['offid'] = taxi_data['offid'].map(mapping_dict).fillna(taxi_data['offid'])
#
# # 保存更新后的文件
# updated_file = 'updated_processed_taxi_data.csv'
# taxi_data.to_csv(updated_file, index=False)
#
# print(f"Updated taxi data saved to {updated_file}")
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import folium

import pandas as pd
import numpy as np
# from sklearn.cluster import KMeans
# from geopy.distance import geodesic
#
# # 定义网格大小
# GRID_SIZE = 0.01348  # 1.5km ≈ 0.01348度
#
# # 定义全局变量 xl
# xl = None  # 初始化 xl
#
#
# # 网格划分函数
# def calculate_grid_id(lat, lon, min_lat, min_lon, grid_size, precision=2):
#     # 使用全局 xl 变量来计算 Grid_ID
#     global xl
#     xx = int((lon - min_lon) / grid_size)  # 四舍五入控制精度
#     yy = int((lat - min_lat) / grid_size)  # 四舍五入控制精度
#     grid_id = xx + xl * yy  # 单一的 Grid_ID
#     return grid_id
#
#
# # 计算加权平均聚类中心
# def calculate_weighted_centroid(cluster_data, centroid_lat, centroid_lon):
#     # 计算每个点到聚类中心的距离
#     distances = [geodesic((lat, lon), (centroid_lat, centroid_lon)).km for lat, lon in
#                  zip(cluster_data['start_lat'], cluster_data['start_lng'])]
#
#     # 权重：距离的倒数（距离越近，权重越大）
#     weights = [1 / (d if d != 0 else 1e-6) for d in distances]  # 避免除以0
#
#     # 计算加权平均纬度和经度
#     weighted_lat = np.average(cluster_data['start_lat'], weights=weights)
#     weighted_lon = np.average(cluster_data['start_lng'], weights=weights)
#
#     return weighted_lat, weighted_lon
#
#
# def find_closest_grid_id(lat, lon, mapping_df, min_lat, min_lon, grid_size):
#     # 计算每个映射网格的中心经纬度
#     mapping_df['grid_lat'] = mapping_df['Original_Value'].apply(lambda x: (x // xl) * grid_size + min_lat)
#     mapping_df['grid_lon'] = mapping_df['Original_Value'].apply(lambda x: (x % xl) * grid_size + min_lon)
#
#     # 计算每个网格的经纬度与聚类中心的距离
#     distances = [geodesic((lat, lon), (row['grid_lat'], row['grid_lon'])).km for _, row in mapping_df.iterrows()]
#
#     # 找到最近的网格 ID
#     closest_grid_id = mapping_df.loc[np.argmin(distances), 'Original_Value']
#     return closest_grid_id
# # 读取并计算聚类中心的网格 ID
# def calculate_grid_id_for_centroids(df, n_clusters=5, mapping_file='6km_value_mapping.csv'):
#     # 使用 KMeans 对起点经纬度进行聚类
#     coordinates = df[['start_lat', 'start_lng']]  # 聚类使用的坐标列（起点经纬度）
#     kmeans = KMeans(n_clusters=n_clusters, random_state=42)  # 聚类
#     kmeans.fit(coordinates)
#
#     # 获取聚类中心的经纬度
#     centroids = kmeans.cluster_centers_
#
#     # 获取经纬度的最小和最大值，计算网格大小
#     min_lat = df['start_lat'].min()
#     max_lat = df['start_lat'].max()
#     min_lon = df['start_lng'].min()
#     max_lon = df['start_lng'].max()
#     global xl
#     xl = int((max_lon - min_lon) / GRID_SIZE)  # 最大列数
#
#     # 读取映射文件
#     mapping_df = pd.read_csv(mapping_file)
#     mapping_dict = dict(zip(mapping_df['Original_Value'], mapping_df['Mapped_Value']))
#
#     # 打印每个聚类中心的经纬度和对应的网格 ID 与最终的 Mapped_Value
#     print("Cluster Centers with Grid IDs and Final Mapped Values:")
#     for idx, (lat, lon) in enumerate(centroids):
#         grid_id_value = calculate_grid_id(lat, lon, min_lat, min_lon, GRID_SIZE)
#
#         # 查找该网格 ID 对应的最终映射值
#         mapped_value = mapping_dict.get(grid_id_value, None)
#
#         if mapped_value is None:
#             # 如果未找到映射值，进行加权平均调整
#             print(f"Grid ID {grid_id_value} not found in the mapping file. Adjusting cluster {idx + 1}.")
#
#             # 获取当前聚类的数据
#             cluster_data = df[kmeans.labels_ == idx]
#
#             # 计算加权平均聚类中心
#             weighted_lat, weighted_lon = calculate_weighted_centroid(cluster_data, lat, lon)
#
#             # 找到映射文件中最近的网格 ID
#             adjusted_grid_id = find_closest_grid_id(weighted_lat, weighted_lon, mapping_df, min_lat, min_lon, GRID_SIZE)
#             mapped_value = mapping_dict.get(adjusted_grid_id, "Not Found")  # 查找调整后的映射值
#             print(
#                 f"Adjusted Cluster {idx + 1} to new lat: {weighted_lat}, lon: {weighted_lon}, Grid ID: {adjusted_grid_id}")
#
#         print(
#             f"Cluster {idx + 1}: Latitude: {lat}, Longitude: {lon}, Grid ID: {grid_id_value}, Mapped Value: {mapped_value}")
#
#
# # 主函数：读取数据并进行聚类，输出聚类中心的 Grid_ID 和最终 Mapped Value
# def main(input_file, mapping_file):
#     # 读取已处理的文件（含起点和终点的经纬度和网格 ID）
#     df = pd.read_csv(input_file)
#
#     # 计算并输出聚类中心的经纬度和对应的网格 ID 与最终映射值
#     calculate_grid_id_for_centroids(df, mapping_file=mapping_file)
#
#
# # 调用函数，输入文件路径
# main('updated_processed_taxi_data.csv', '6km_value_mapping.csv')  # 请确保这个文件包含 'start_lat' 和 'start_lng' 列
import pandas as pd
import numpy as np

# # 加载 CSV 数据
# nyc_taxi_data = pd.read_csv('updated_processed_taxi_data.csv')
#
# # 将时间列转换为 datetime 类型
# nyc_taxi_data['time_on'] = pd.to_datetime(nyc_taxi_data['start_time'])  # 假设 'start_time' 列
# nyc_taxi_data['time_off'] = pd.to_datetime(nyc_taxi_data['end_time'])  # 假设 'end_time' 列
#
# # 对时间进行对齐到15分钟
# nyc_taxi_data['alignedtime'] = nyc_taxi_data['time_on'].dt.floor(f'{0.25 * 60}min')  # 对齐到15分钟
#
# # 对数据进行排序
# nyc_taxi_data = nyc_taxi_data.sort_values('alignedtime')
#
# # 生成时间范围，时间间隔为15分钟
# time = pd.DataFrame({'time': pd.date_range(start=nyc_taxi_data['alignedtime'].min(),
#                                            end=nyc_taxi_data['alignedtime'].max(),
#                                            freq=f'{0.25 * 60}min')})
#
# # 创建一个空的流量矩阵，尺寸为（时间段, 起点数, 终点数）
# lenid = len(nyc_taxi_data['upid'].unique())  # 假设每个起点和终点的 ID 唯一
# odflow = np.zeros((len(time), lenid, lenid))
#
# # 按时间、起点和终点分组并计算每个组合的数量
# group_time_odflow = nyc_taxi_data.groupby(['alignedtime', 'upid', 'offid']).size().reset_index(name='counts')
#
# # 将每个时间段内的流量值填充到流量矩阵中
# for index, row in time.iterrows():
#     timeslot = row['time']
#     # 筛选出与当前 timeslot 相同的记录，即在当前时间段内发生的所有乘客上下车区域组合
#     odflow_data = group_time_odflow[group_time_odflow["alignedtime"] == timeslot]
#     for i, row_ in odflow_data.iterrows():
#         o_id = int(row_['upid'])
#         d_id = int(row_['offid'])
#         count = row_['counts']
#
#         # 打印调试信息
#         print(f"Index: {index}, Time: {timeslot}, o_id: {o_id}, d_id: {d_id}")
#         print(f"Valid range: o_id (0 to {lenid - 1}), d_id (0 to {lenid - 1})")
#
#         # 确保 o_id 和 d_id 在合法范围内
#         o_id = np.clip(o_id, 0, lenid - 1)
#         d_id = np.clip(d_id, 0, lenid - 1)
#
#         print(f"Clipped o_id: {o_id}, Clipped d_id: {d_id}")
#
#         odflow[index, o_id, d_id] += count
#
#     if index % 1000 == 0:
#         print(f" {index}/{len(time)}")
#
#
#
# # 保存流量矩阵为 NPZ 文件
# np.savez_compressed('6kmodflow.npz', odflow=odflow)
import numpy as np

# 加载 .npz 文件
npz_file = np.load('6kmodflow.npz')

# 查看文件内容，输出所有数组的键（即存储的各个数组的名字）
print("Contents of the .npz file:")
print(npz_file.files)

# 假设文件中存储了一个名为 'odflow' 的数组
odflow = npz_file['odflow']

# 查看数组的形状和数据类型
print("\nArray 'odflow' shape:", odflow.shape)
print("Array 'odflow' data type:", odflow.dtype)

# 检查是否有缺失值或无穷大值
print("\nChecking for NaN values:", np.isnan(odflow).sum())
print("Checking for Inf values:", np.isinf(odflow).sum())

# 检查最小值、最大值、均值等统计信息，确保数据合理
print("\nStatistics of 'odflow' array:")
print("Min:", odflow.min())
print("Max:", odflow.max())
print("Mean:", odflow.mean())
print("Std:", odflow.std())

# 查看部分数据，检查是否符合预期
print("\nFirst few entries of the 'odflow' matrix (first 3 time slots and 3 regions):")
print(odflow[:3, :3, :3])  # 查看前3个时间段和前3个起点-终点的流量数据
import pandas as pd
import numpy as np

# 加载原始数据
nyc_taxi_data = pd.read_csv('updated_processed_taxi_data.csv')

# 查看 'upid' 和 'offid' 的唯一值数量
unique_upid = nyc_taxi_data['upid'].unique()
unique_offid = nyc_taxi_data['offid'].unique()

print(f"Number of unique 'upid' values: {len(unique_upid)}")
print(f"Number of unique 'offid' values: {len(unique_offid)}")

# 检查 'upid' 和 'offid' 的范围
print(f"Range of 'upid': {min(unique_upid)} to {max(unique_upid)}")
print(f"Range of 'offid': {min(unique_offid)} to {max(unique_offid)}")

# 检查数据类型和是否有空值
print(f"Data type of 'upid': {nyc_taxi_data['upid'].dtype}")
print(f"Data type of 'offid': {nyc_taxi_data['offid'].dtype}")
print(f"Missing values in 'upid': {nyc_taxi_data['upid'].isnull().sum()}")
print(f"Missing values in 'offid': {nyc_taxi_data['offid'].isnull().sum()}")

# 确保 'upid' 和 'offid' 是整数类型，如果不是则转换
nyc_taxi_data['upid'] = nyc_taxi_data['upid'].astype(int)
nyc_taxi_data['offid'] = nyc_taxi_data['offid'].astype(int)

# 重新计算 lenid，确保其是正确的
lenid = len(np.unique(np.concatenate([nyc_taxi_data['upid'].values, nyc_taxi_data['offid'].values])))
print(f"Total unique regions (lenid): {lenid}")
import pandas as pd
import numpy as np

# 加载原始数据
nyc_taxi_data = pd.read_csv('updated_processed_taxi_data.csv')

# 将时间列转换为 datetime 类型
nyc_taxi_data['time_on'] = pd.to_datetime(nyc_taxi_data['start_time'])  # 假设 'start_time' 列
nyc_taxi_data['time_off'] = pd.to_datetime(nyc_taxi_data['end_time'])  # 假设 'end_time' 列

# 对时间进行对齐到15分钟
nyc_taxi_data['alignedtime'] = nyc_taxi_data['time_on'].dt.floor(f'{0.25 * 60}min')  # 对齐到15分钟

# 对数据进行排序
nyc_taxi_data = nyc_taxi_data.sort_values('alignedtime')

# 生成时间范围，时间间隔为15分钟
time = pd.DataFrame({'time': pd.date_range(start=nyc_taxi_data['alignedtime'].min(),
                                           end=nyc_taxi_data['alignedtime'].max(),
                                           freq=f'{0.25 * 60}min')})
# 打印时间段的数量
print(f"Number of time slots: {len(time)}")

# 打印 lenid 和流量矩阵的维度
print(f"Time slots: {len(time)}, Regions: {lenid}")
print(f"Expected matrix dimensions: ({len(time)}, {lenid}, {lenid})")

# 计算内存需求（以 GB 为单位）
memory_needed_gb = len(time) * lenid * lenid * 8 / (1024 ** 3)
print(f"Estimated memory required: {memory_needed_gb:.2f} GB")
# 计算唯一的起点和终点
unique_upid = nyc_taxi_data['upid'].unique()
unique_offid = nyc_taxi_data['offid'].unique()

print(f"Number of unique 'upid' values: {len(unique_upid)}")
print(f"Number of unique 'offid' values: {len(unique_offid)}")

# 重新计算 lenid，确保其是正确的
lenid = len(np.unique(np.concatenate([nyc_taxi_data['upid'].values, nyc_taxi_data['offid'].values])))
print(f"Total unique regions (lenid): {lenid}")

# 创建一个空的流量矩阵，尺寸为（时间段, 起点数, 终点数）
odflow = np.zeros((len(time), lenid, lenid))


# 按时间、起点和终点分组并计算每个组合的数量
group_time_odflow = nyc_taxi_data.groupby(['alignedtime', 'upid', 'offid']).size().reset_index(name='counts')

# 将每个时间段内的流量值填充到流量矩阵中
for index, row in time.iterrows():
    timeslot = row['time']
    # 筛选出与当前 timeslot 相同的记录，即在当前时间段内发生的所有乘客上下车区域组合
    odflow_data = group_time_odflow[group_time_odflow["alignedtime"] == timeslot]
    for i, row_ in odflow_data.iterrows():
        o_id = int(row_['upid'])
        d_id = int(row_['offid'])
        count = row_['counts']

        # 确保 o_id 和 d_id 在合法范围内
        o_id = np.clip(o_id, 0, lenid - 1)
        d_id = np.clip(d_id, 0, lenid - 1)

        odflow[index, o_id, d_id] += count

    if index % 1000 == 0:
        print(f" {index}/{len(time)}")

# 保存流量矩阵为 NPZ 文件
np.savez_compressed('6kmodflow_corrected.npz', odflow=odflow)
