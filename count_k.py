import pandas as pd
import numpy as np
import math
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import osmnx as ox
from shapely.geometry import Point
import folium  # 用于生成地图
import os

# --------------------------
# 1. 获取旧金山市边界，并过滤数据
# --------------------------
region = "San Francisco, California, USA"
gdf = ox.geocode_to_gdf(region)
sf_polygon = gdf.iloc[0].geometry  # 旧金山市边界

def is_in_sf(lat, lon, polygon):
    """判断给定点是否在 polygon 内（点：顺序 (lon, lat)）"""
    return polygon.contains(Point(lon, lat))

# 加载原始流量数据，假设文件名为 "save_od_with_id.csv"
data = pd.read_csv("save_od_with_id.csv")

# 合并上下车点，并去重
coords = pd.concat([
    data[['lat_on', 'lon_on']].rename(columns={'lat_on': 'lat', 'lon_on': 'lon'}),
    data[['lat_off', 'lon_off']].rename(columns={'lat_off': 'lat', 'lon_off': 'lon'})
]).drop_duplicates()

# 过滤只保留落在 SF 内的点
coords = coords[coords.apply(lambda row: is_in_sf(row['lat'], row['lon'], sf_polygon), axis=1)]
print(f"过滤后剩余数据点数量：{len(coords)}")

# --------------------------
# 2. 设定聚类、网格参数
# --------------------------
# 采用 SF 边界的外包矩形
minx, miny, maxx, maxy = sf_polygon.bounds
LAT_MIN_grid, LAT_MAX_grid = miny, maxy
LON_MIN_grid, LON_MAX_grid = minx, maxx
GRID_SIZE = 0.0135  # 单位：度（约1.5公里）

def calculate_grid_center_in_area(lat, lon, lat_min, lon_min, grid_size):
    grid_row = int((lat - lat_min) // grid_size)
    grid_col = int((lon - lon_min) // grid_size)
    grid_lat = lat_min + (grid_row + 0.5) * grid_size
    grid_lon = lon_min + (grid_col + 0.5) * grid_size
    return grid_lat, grid_lon

def get_all_possible_grid_centers(lat_min, lat_max, lon_min, lon_max, grid_size, polygon):
    """生成区域内所有落在 polygon 内的网格中心，返回字典 {grid_id: (center_lat, center_lon)}"""
    centers = {}
    n_rows = int((lat_max - lat_min) // grid_size)
    n_cols = int((lon_max - lon_min) // grid_size)
    for r in range(n_rows):
        for c in range(n_cols):
            center_lat = lat_min + (r + 0.5) * grid_size
            center_lon = lon_min + (c + 0.5) * grid_size
            point = Point(center_lon, center_lat)
            if polygon.contains(point):  # 仅保留在 SF 内的
                grid_id = r * n_cols + c
                centers[grid_id] = (center_lat, center_lon)
    return centers

def find_nearest_unused_in_area(candidate_lat, candidate_lon, used, lat_min, lon_min, grid_size, total_cols, lat_max, lon_max, polygon):
    best_id = None
    best_distance = float('inf')
    n_rows = int((lat_max - lat_min) // grid_size)
    n_cols = int((lon_max - lon_min) // grid_size)
    for r in range(n_rows):
        for c in range(n_cols):
            gid = r * n_cols + c
            if gid in used:
                continue
            grid_center = (lat_min + (r + 0.5) * grid_size, lon_min + (c + 0.5) * grid_size)
            if not polygon.contains(Point(grid_center[1], grid_center[0])):
                continue
            distance = math.sqrt((grid_center[0] - candidate_lat)**2 + (grid_center[1] - candidate_lon)**2)
            if distance < best_distance:
                best_distance = distance
                best_id = gid
                best_center = grid_center
    if best_id is not None:
        return best_id, best_center
    else:
        return None, (candidate_lat, candidate_lon)

# 创建输出文件夹
output_folder = "candidate_vertiports_SF"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
map_folder = "folium_maps"
if not os.path.exists(map_folder):
    os.makedirs(map_folder)

# --------------------------
# 3. 针对 k 从 2 到 10 进行聚类，生成候选停机坪数据，并保存及生成 folium 地图
# --------------------------
# 标准化所有坐标数据
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords[['lat', 'lon']])

for k in range(2, 11):
    print(f"\n使用 k={k} 进行聚类")
    kmeans = KMeans(n_clusters=k, init='k-means++', n_init=20, random_state=42)
    kmeans.fit(coords_scaled)
    
    # 聚类中心还原到原始经纬度
    centroids_scaled = kmeans.cluster_centers_
    centroids = scaler.inverse_transform(centroids_scaled)
    
    # 生成落在 SF 内的网格中心（基于 SF 边界的外包矩形，并过滤海域）
    all_centers = get_all_possible_grid_centers(LAT_MIN_grid, LAT_MAX_grid, LON_MIN_grid, LON_MAX_grid, GRID_SIZE, sf_polygon)
    total_cols = int((LON_MAX_grid - LON_MIN_grid) // GRID_SIZE)
    print(f"SF 内有效网格中心数量: {len(all_centers)}, 每行网格数量: {total_cols}")
    
    # 将聚类中心调整到网格中心
    adjusted_centroids = []
    grid_ids = []
    used = set()
    for i, (lat, lon) in enumerate(centroids):
        candidate_lat, candidate_lon = calculate_grid_center_in_area(lat, lon, LAT_MIN_grid, LON_MIN_grid, GRID_SIZE)
        grid_row = int((candidate_lat - LAT_MIN_grid) // GRID_SIZE)
        grid_col = int((candidate_lon - LON_MIN_grid) // GRID_SIZE)
        candidate_grid_id = grid_row * total_cols + grid_col
        if candidate_grid_id in used:
            new_id, new_center = find_nearest_unused_in_area(candidate_lat, candidate_lon, used,
                                                              LAT_MIN_grid, LON_MIN_grid, GRID_SIZE,
                                                              total_cols, LAT_MAX_grid, LON_MAX_grid, sf_polygon)
            if new_id is None:
                adjusted_lat, adjusted_lon = candidate_lat, candidate_lon
                unique_grid_id = candidate_grid_id
            else:
                adjusted_lat, adjusted_lon = new_center
                unique_grid_id = new_id
        else:
            adjusted_lat, adjusted_lon = candidate_lat, candidate_lon
            unique_grid_id = candidate_grid_id
        used.add(unique_grid_id)
        adjusted_centroids.append((adjusted_lat, adjusted_lon))
        grid_ids.append(unique_grid_id)
    adjusted_centroids = np.array(adjusted_centroids)
    
    # 生成候选停机坪数据 DataFrame
    vertiport_data = pd.DataFrame({
        "Vertiport": [f"Vertiport_{i+1}" for i in range(k)],
        "Latitude": adjusted_centroids[:, 0],
        "Longitude": adjusted_centroids[:, 1],
        "Grid_ID": grid_ids
    })
    # 再次过滤确保所有点在 SF 内
    vertiport_data = vertiport_data[vertiport_data.apply(lambda row: sf_polygon.contains(Point(row["Longitude"], row["Latitude"])), axis=1)]
    
    print(f"\n对于 k={k} 的候选停机坪数据:")
    print(vertiport_data)
    
    # 保存到 CSV
    csv_filename = f"candidate_vertiports_SF_k{k}.csv"
    vertiport_data.to_csv(os.path.join(output_folder, csv_filename), index=False)
    print(f"候选停机坪数据已保存到 {csv_filename}")
    
    # 生成 Folium 地图可视化
    # 将地图中心定位于 SF 边界的中心
    sf_center = [sf_polygon.centroid.y, sf_polygon.centroid.x]
    m = folium.Map(location=sf_center, zoom_start=12)
    
    # 添加每个候选点的标记
    for i, row in vertiport_data.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row['Vertiport']} (Grid_ID: {row['Grid_ID']})",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    # 保存地图为 HTML 文件
    map_filename = f"candidate_vertiports_SF_k{k}.html"
    m.save(os.path.join(map_folder, map_filename))
    print(f"Folium 地图已保存到 {map_filename}")
