import pandas as pd
import geopandas as gpd
import movingpandas as mpd
import folium
from folium.plugins import TimestampedGeoJson, AntPath
from datetime import datetime
import numpy as np
from shapely.geometry import Point
import math

grid_size =  0.0089932188*1.5

def draw_with_OSM(df,savename):
    # the df was sorted e.g.
    # df = df.sort_values(by=['t'], ascending=[True])

    start_point = Point(df.longitude.iloc[0],df.latitude.iloc[0])
    # print(start_point)
    m = folium.Map(location=[start_point.y, start_point.x], tiles="cartodbpositron", zoom_start=14)
    m.add_child(folium.LatLngPopup())
    minimap = folium.plugins.MiniMap()
    m.add_child(minimap)
    folium.TileLayer('OpenStreetMap').add_to(m)
    #
    count = 0
    for i in range(len(df)):

        # print(df.occupancy.iloc[i])
        if df.occupancy.iloc[i]==1 and start < 0:
            start = i
        if df.occupancy.iloc[i]==0 and start >= 0 :
            df1 = df.iloc[start:i]
            df1 = df1.set_index('t')
            # print(df1)
            gdf = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1.longitude, df1.latitude), crs=4236)
            trajs = mpd.TrajectoryCollection(gdf, 'id')
            # start_point = trajs.trajectories[0].get_start_location()
            # print(trajs)
            for index, traj in enumerate(trajs.trajectories):
                name = f"Taxi {traj.df['id'][0]}"  # 轨迹名称
                # print(name,traj)
                randr = lambda: np.random.randint(0, 255)
                color = '#%02X%02X%02X' % (randr(), randr(), randr())  # black
                # line
                geo_col = traj.to_point_gdf().geometry
                xy = [[y, x] for x, y in zip(geo_col.x, geo_col.y)]
                f1 = folium.FeatureGroup(name)
                # print(xy)
                AntPath(locations=xy, color=color, weight=3, opacity=0.7, dash_array=[20, 30]).add_to(f1)
                f1.add_to(m)

            start = -1
            count +=1
    folium.LayerControl().add_to(m)
    m.get_root().render()
    m.get_root().save("taxi_test_page.html")
    print(count)


def extraction_data(taxi_id):

    df = pd.read_csv(f"../ori_data/other/movingpd_sf_Spatiotemporal/cabspottingdata/new_{taxi_id}.txt", header=None, sep=" ")
    df.columns = ['latitude', 'longitude', 'occupancy', 't']
    df.insert(0, 'id', [taxi_id for _ in range(df.shape[0])])  # 插入新列：id
    # df = df[df.occupancy==1]
    # step. 提取某个时间范围的数据
    df.t = df.t.apply(lambda x: datetime.fromtimestamp(x))  # 时间戳转datetime

    df = df.sort_values(by=['t'], ascending=[True])  # 按t升序排序

    print(taxi_id,len(df))
    return df
    # print(1)

def extraction_od_data(taxi_id):

    df = pd.read_csv(f"../ori_data/other/movingpd_sf_Spatiotemporal/cabspottingdata/new_{taxi_id}.txt", header=None, sep=" ")
    df.columns = ['latitude', 'longitude', 'occupancy', 't']
    df.insert(0, 'id', [taxi_id for _ in range(df.shape[0])])  # 插入新列：id
    # df = df[df.occupancy==1]
    # step. 提取某个时间范围的数据
    df.t = df.t.apply(lambda x: datetime.fromtimestamp(x))  # 时间戳转datetime

    # chosen_index = df.t.apply(lambda x: (x.month == 5 and x.day == 18))  # option：仅保留一天的数据
    # df = df[chosen_index]
    df = df.sort_values(by=['t'], ascending=[True])  # 按t升序排序
    start = -1
    savepd = pd.DataFrame(columns=['id', 'lat_on', 'lon_on', 'time_on', 'time_off', 'lat_off', 'lon_off'])
    for i in range(len(df)):
        # print(df.occupancy.iloc[i])
        if df.occupancy.iloc[i]==1 and start < 0:
            start = i
        if df.occupancy.iloc[i]==0 and start >= 0 :
            df1 = df.iloc[start:i]
            savepd.loc[len(savepd.index)] = [df.id.iloc[start],df.latitude.iloc[start],df.longitude.iloc[start],
                                             df.t.iloc[start],df.t.iloc[i],df.latitude.iloc[i],df.longitude.iloc[i]]

            start = -1


    # print('now df columns=[latitude, longitude, id], index=t')

    # step. 根据df创建gdf和mpd.trajs
    # df = df.set_index('t')  # 以t为index
    # gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4236)
    # trajs = mpd.TrajectoryCollection(gdf, 'id')
    #
    # # step. 画图
    # start_point = trajs.trajectories[0].get_start_location()
    # m = folium.Map(location=[start_point.y, start_point.x], tiles="cartodbpositron", zoom_start=14)  # 经纬度反向
    # m.add_child(folium.LatLngPopup())
    # minimap = folium.plugins.MiniMap()
    # m.add_child(minimap)
    # folium.TileLayer('OpenStreetMap').add_to(m)
    #
    # for index, traj in enumerate(trajs.trajectories):
    #     name = f"Taxi {traj.df['id'][0]}"  # 轨迹名称
    #     randr = lambda: np.random.randint(0, 255)
    #     color = '#%02X%02X%02X' % (randr(), randr(), randr())  # black
    #     # line
    #     geo_col = traj.to_point_gdf().geometry
    #     xy = [[y, x] for x, y in zip(geo_col.x, geo_col.y)]
    #     f1 = folium.FeatureGroup(name)
    #     AntPath(locations=xy, color=color, weight=3, opacity=0.7, dash_array=[20, 30]).add_to(f1)
    #     f1.add_to(m)
    #
    # folium.LayerControl().add_to(m)
    #
    # m.get_root().render()
    # m.get_root().save("taxi_test_page.html")
    print(taxi_id,len(savepd))
    return savepd
    # print(1)

def get_distnce(names='value_mapping.csv'):
    df = pd.read_csv(names, dtype=str,index_col=False)
    df['Original_Value'] = df['Original_Value'].astype(np.float64).astype(np.int64)
    df['Mapped_Value'] = df['Mapped_Value'].astype(np.float64).astype(np.int64)

    xl = 247
    yl = 1156
    out = list()
    for index1, row1 in df.iterrows():
        for index2, row2 in df.iterrows():
            # map_df.columns = ['Original_Value', 'Mapped_Value']
            ID1= row1.Original_Value
            ID2 = row2.Original_Value
            x1 = ID1 / xl
            y1 = ID1 % xl

            x2 = ID2 / xl
            y2 = ID2 % xl
            # lx=(0.26/10)*111320
            # ly=(0.22/10)*100000
            lx = ly = 1.5
            d = (((lx * (x2 - x1)) ** 2 + (ly * (y2 - y1)) ** 2) ** 0.5)
            out.append((row1.Mapped_Value, row2.Mapped_Value, d))

    name = ['from', 'to', 'distance']
    result = pd.DataFrame(columns=name, data=out)
    print(len(result))
    result.to_csv('distance1.csv')

def deal_id(df):
    # 合并两列的唯一值（去除 NaN）
    unique_values = sorted(set(df['upid'].dropna()).union(set(df['offid'].dropna())))

    # 创建映射字典
    value_map = {v: i for i, v in enumerate(unique_values)}

    # 应用映射到两列
    df['upid'] = df['upid'].map(value_map).fillna(np.nan)
    df['offid'] = df['offid'].map(value_map).fillna(np.nan)

    # 将映射字典转换为 DataFrame
    map_df = pd.DataFrame.from_dict(value_map, orient='index', columns=['Mapped_Value'])
    map_df.reset_index(inplace=True)
    map_df.columns = ['Original_Value', 'Mapped_Value']

    # 保存映射字典到 CSV 文件
    map_df.to_csv('value_mapping.csv', index=False)
    return df, len(value_map)

def get_flow(path):

    taxi_data = pd.read_csv(path, dtype=str,index_col=False)

    # headers = taxi_data.columns.tolist()
    # print(headers)
    order = ['id', 'lat_on', 'lon_on', 'time_on', 'time_off', 'lat_off', 'lon_off']


    taxi_data = taxi_data.fillna(value=0)
    print(order)

    taxi_data[order[1]] = taxi_data[order[1]].astype(np.float64)
    taxi_data[order[2]] = taxi_data[order[2]].astype(np.float64)
    taxi_data[order[5]] =taxi_data[order[5]].astype(np.float64)
    taxi_data[order[6]] = taxi_data[order[6]].astype(np.float64)
    # taxi_data[order[7]] = taxi_data[order[7]].astype(np.float64).astype(np.int64)

    nyc_taxi_data = taxi_data
    # print(nyc_taxi_data)

    # print(taxi_data)
    longitude = list(nyc_taxi_data[order[2]])
    latitude = list(nyc_taxi_data[order[1]])
    loc_df = pd.DataFrame()  # 提取经纬度数据
    loc_df['longitude'] = longitude
    loc_df['latitude'] = latitude
    xa, xb =min([taxi_data.lon_on.min(),taxi_data.lon_off.min()]), max([taxi_data.lon_on.max(),taxi_data.lon_off.max()])
    ya, yb = min([taxi_data.lat_on.min(),taxi_data.lat_off.min()]), max([taxi_data.lat_on.max(),taxi_data.lat_off.max()])
    x = loc_df['longitude']  # pickup_longitude
    y = loc_df['latitude']  # pickup_latitude
    # xl = yl = 10
    loc_df['xx'] = (x - xa) / grid_size
    xx = loc_df['xx'].astype(np.int64)
    loc_df['yy'] = (y - ya) / grid_size
    yy = loc_df['yy'].astype(np.int64)
    xl = int((xb-xa)/grid_size)
    yl = int((yb - ya) / grid_size)
    # loc_df['upid'] = xx + xl * yy + 0
    # print(loc_df)
    xx = xx.clip(0, xl)
    yy = yy.clip(0, yl)
    loc_df['id1'] = (xx + xl * yy)
    # nyc_taxi_data['upid'] = loc_df['id1'].astype(np.int64)
    nyc_taxi_data['upid'] = (xx + xl * yy)
    # print(nyc_taxi_data['upid'])
    print(f'longitude {[xa,xb]}\t latitude {[ya,yb]}\t {[xl,yl]}')

    longitude = list(nyc_taxi_data[order[6]])
    latitude = list(nyc_taxi_data[order[5]])
    loc_df = pd.DataFrame()  # 提取经纬度数据
    loc_df['longitude'] = longitude
    loc_df['latitude'] = latitude
    x = loc_df['longitude']  # pickup_longitude
    y = loc_df['latitude']  # pickup_latitude
    # 计算xx和yy，基于行政区域的经纬度边界划分网格
    loc_df['xx'] = (x - xa) / grid_size
    xx = loc_df['xx'].astype(np.int64)
    loc_df['yy'] = (y - ya) /grid_size
    yy = loc_df['yy'].astype(np.int64)
    # 检查是否超出边界
    xx = xx.clip(0, xl )
    yy = yy.clip(0, yl)
    # nyc_taxi_data['offid'] = xx + xl * yy +
    # loc_df['id2'] = loc_df['id2'].astype(np.int64)
    nyc_taxi_data['offid'] = (xx + xl * yy)
    nyc_taxi_data,lenid = deal_id(nyc_taxi_data)
    print(f'lenid {lenid}')

    nyc_taxi_data.to_csv('save_od_with_id.csv', index=False)
    # print(max(nyc_taxi_data['upid']), min(nyc_taxi_data['upid']))
    # print(max(nyc_taxi_data['offid']),min(nyc_taxi_data['offid']))
    # except:
    #     print("ERROR !!!!")
    #     loc_df.to_csv(f'../ori_data/{year}/{datatype}_errordata_%d-%02d.csv')
    # nyc_taxi_data['upid'] = nyc_taxi_data['upid'].astype(np.int64)
    # nyc_taxi_data['offid'] = nyc_taxi_data['offid'].astype(np.int64)

    nyc_taxi_data[order[4]] = pd.to_datetime(nyc_taxi_data[order[4]])
    nyc_taxi_data[order[3]] = pd.to_datetime(nyc_taxi_data[order[3]])

    nyc_taxi_data['alignedtime'] = nyc_taxi_data.time_on.dt.floor(f'{0.25 * 60}min')

    # print(nyc_taxi_data['alignedtime'])
    nyc_taxi_data = nyc_taxi_data.sort_values('alignedtime')



    time = pd.DataFrame({'time': pd.date_range(f'2008-5-17 18:00:00', f'2008-6-10 01:45:00', freq=f'{0.25 * 60}min')})

    time = time[: -1]
    odflow = np.zeros((len(time), lenid, lenid))

    group_time_odflow = nyc_taxi_data.groupby(['alignedtime', 'upid', 'offid']).size().reset_index(name='counts')
    print(group_time_odflow)
    for index, row in time.iterrows():
        timeslot = row['time']
        #筛选出与当前 timeslot 相同的记录，即在当前时间段内发生的所有乘客上下车区域组合。
        odflow_data = group_time_odflow[group_time_odflow["alignedtime"] == timeslot]
        for i, row_ in odflow_data.iterrows():
            o_id = int(row_['upid'])
            d_id = int(row_['offid'])
            count = row_['counts']
            odflow[index, o_id, d_id] += count
        if index % 1000==0:
            print(f" {index}/{len(time)}")


    f = f'h-odflow.npz'
    np.savez_compressed(f, odflow)
    # np.savetxt(f, odflow, delimiter=",")
    print(f)




if __name__ == '__main__':
    # taxi_id = 'abboip'
    # df3 = pd.concat([df1, df2])
    # extraction_data(taxi_id)

    '''以下部分将txt的gps数据转换成od的csv'''

    fp = open(f"../ori_data/other/movingpd_sf_Spatiotemporal/cabspottingdata/_cabs.txt", 'r')
    savefile ='save_od.csv'
    get_flow(savefile)
    get_distnce()


    # lines = fp.readlines()
    # id_list = [line.split("\"")[1] for line in lines]
    # # step. 读所有txt，并处理为df
    # raw_df = pd.DataFrame()
    # s = 1
    # for id in id_list:
    #     # print(id)
    #     raw_df = pd.concat([raw_df,extraction_od_data(id)])#extraction_data(id)])
    #
    # print(len(raw_df))
    # raw_df.to_csv('save_od.csv',index=False)


    # df = pd.read_csv('save.csv',index_col=False)
    # min_lat = df['latitude'].min()
    # max_lat = df['latitude'].max()
    # min_lon = df['longitude'].min()
    # max_lon = df['longitude'].max()
    #
    # print(min_lat,max_lat,min_lon,max_lon)
    # print(math.cos(math.radians(min_lat)),math.cos(math.radians(max_lat)))
    # print()