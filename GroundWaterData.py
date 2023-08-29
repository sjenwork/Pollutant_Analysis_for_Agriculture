import geopandas as gpd
from utils.sql import connPostgreSQL

def read_GWREGION():
    gdf = gpd.read_file('data/Ground_Water/GWREGION/GWREGION.shp')
    gdf = gdf.to_crs('epsg:4326')
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        gdf.to_postgis('ground_water_map', engine, if_exists='replace', index=False)
    return gdf