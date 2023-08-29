import geopandas as gpd
from utils.sql import connPostgreSQL
from sqlalchemy import text
from shapely.geometry import Point

def read_taiwan_geojson(contains=[]):
    taiwan = gpd.read_file('data/TaiwanCounty/taiwan_county_geojson_mini.json')
    if contains:
        taiwan = taiwan[taiwan['NAME_2014'].str.contains('|'.join(contains)).fillna(False)]
    return taiwan

def to_postgis():
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        gdf = gpd.read_file('data/TaiwanCounty/mapdata202301070205/COUNTY_MOI_1090820.shp', encoding='utf-8')
        gdf=gdf.to_crs(epsg=4326)
        gdf.to_postgis('taiwan', engine, if_exists='replace')

def to_postgis():
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        gdf = gpd.read_file('data/TaiwanCounty/COUNTY_MOI_1090820_mini/COUNTY_MOI_1090820_mini.shp', encoding='utf-8')
        gdf=gdf.to_crs(epsg=4326)
        gdf.to_postgis('taiwan_mini', engine, if_exists='replace')

def read_taiwan_admin_map(countyname_like=None, point_twd97=None, point_wgs84=None):
    '''
        提供三種不同的參數，來讀取對應的台灣行政區域圖資
        1. 輸入 countyname_like，可為字串或串列，如 '台北市' 或 ['台北市', '新北市']
        2. 輸入 point_twd97，為一個 tuple，如 (121.5, 25.0) <- 未完成
        3. 輸入 point_wgs84，為一個 tuple，如 (121.5, 25.0)
    '''
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:

        if countyname_like is None and point_twd97 is None and point_wgs84 is None:
        ###### 讀取圖資
            sql = ''' select * from taiwan '''
            taiwan_map = gpd.read_postgis(sql, engine, geom_col='geometry')    


        elif countyname_like is not None:
            if type(countyname_like) is str:
                countyname_like = [countyname_like]
            where = ' or '.join([f'countyname like :countyname_{i}' for i in range(len(countyname_like))])
            sql = text(''' select * from taiwan ''' + ' where ' + where)
            params = {i: j for i, j in zip([f'countyname_{i}' for i in range(len(countyname_like))], [f'%{k}%' for k in countyname_like])}
            print(sql, params)

            taiwan_map = gpd.read_postgis(sql, engine, geom_col='geom', params=params)

        elif point_wgs84 is not None:
            sql = text(''' select * from taiwan where st_contains(geom, st_geomfromtext(:point, 4326)) ''')
            params = {'point': Point(*point_wgs84).wkt}
            taiwan_map = gpd.read_postgis(sql, engine, geom_col='geom', params=params)

    return taiwan_map