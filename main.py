from utils.sql import connPostgreSQL
import geopandas as gpd

with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
    # data = gpd.read_postgis('SELECT distinct sitename, geometry  FROM river_monitoring_data_opendata', engine, geom_col='geometry')
    # basin = gpd.read_postgis('SELECT *  FROM riverbasin', engine, geom_col='geom')
    riverpoly = gpd.read_postgis('SELECT *  FROM riverpoly', engine, geom_col='geom')

    
# data.set_crs(epsg=4326, inplace=True)
# basin.to_crs(epsg=4326, inplace=True)
riverpoly.to_crs(epsg=4326, inplace=True)
# data.to_file('data/River_Monitor_Data/allsite', orient='records', encoding='utf-8'    )
# basin.to_file('data/River_Basin_Poly/basin_wgs84', orient='records', encoding='utf-8'    )
riverpoly.to_file('data/River_Basin_Poly/riverpoly_wgs84', orient='records', encoding='utf-8'    )

