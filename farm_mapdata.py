import geopandas as gpd
from matplotlib import pyplot as plt
import pandas as pd
from utils.sql import connPostgreSQL

from RiverBasinPolyData import  read_river_basin
plt.ion()

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0

# Read in the shapefile
def read_legal_Agricultural_land(sql=None, contain_river_basin=False):
    if not contain_river_basin:
        table = 'agriculturalzone_mini'
    else:
        table = 'agriculturalzone_basin_mini'
        
    if sql is None:
        sql = f''' select * from {table} '''
        
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        gdf = gpd.read_postgis(sql, engine, geom_col='geom')    
        
    return gdf



def legal_Agricultural_land_to_riverbasin():
    data = read_legal_Agricultural_land()
    river_basin = read_river_basin()
    river_basin.to_crs(epsg=3826, inplace=True)
    river_basin['total_area'] = river_basin.geometry.area 
    print('成功讀取流域資料')   

    # 修正錯誤的 geometry
    if data.geometry.is_valid.sum() != len(data):
        data['geometry'] = data.geometry.buffer(0) # 修正錯誤的 geometry
        print('修正錯誤的 geometry')

    # 將data投影到3826
    data.to_crs(epsg=3826, inplace=True)

    # 計算data與流域的交集
    intersection = gpd.overlay(data, river_basin, how='intersection')
    intersection_dissolve = intersection.dissolve(by='BASIN_NAME')
    intersection_dissolve = intersection_dissolve.reset_index()
    print('成功計算data與流域的交集')

    # 找出交集後，但是沒有交集的流域
    missing = river_basin.loc[~river_basin['BASIN_NAME'].isin(intersection_dissolve['BASIN_NAME'])].copy()
    missing['geometry'] = None
    # 將有交集的流域與沒有交集的流域合併
    intersection_dissolve_all = pd.concat([intersection_dissolve, missing])    
    # 下面這個步驟應該要改成直接寫道資料庫
    intersection_dissolve_all.to_file('data/Farm_mapdata/全臺法定農業用地範圍圖_壓縮/全臺法定農業用地範圍圖_流域.shp', encoding='cp950')



