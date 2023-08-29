import pandas as pd
import geopandas as gpd
import folium
from folium import features
from shapely.geometry import Point, LineString, Polygon

from utils.sql import connPostgreSQL

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0

with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
    # taiwan = gpd.read_postgis('SELECT *  FROM taiwan', engine, geom_col='geom')
    pol = gpd.read_postgis('''
                    SELECT a.ems_no, a.fac_name, a.address, a.unino, a.per_no , a.per_type , a.let_emi, a.let_watertype ,  b.basin_name, a.emi_item , a.emi_value, a.emi_units , a.geometry 
                    FROM water_pollution_data as a
                    inner JOIN riverbasin as b ON ST_Contains(b.geom , ST_Transform(a.geometry, 3826))
                    WHERE b.basin_name  IN ('二仁溪', '老街溪')
                    '''
                    , engine, geom_col='geometry')


    pol.fillna('', inplace=True)
    pol = pol.assign(x=pol.geometry.x, y=pol.geometry.y)
    site = pol.groupby(['x', 'y', 'basin_name'], as_index=False).agg({
        'ems_no': lambda x: ','.join(set(x)),
        'fac_name': lambda x: ','.join(set(x)),
        'address': lambda x: ','.join(set(x)),
        'let_watertype': lambda x: ','.join(set(x)),
        'emi_item': lambda x: ','.join(set(x)),
        'geometry': 'first',

    })





m = folium.Map(location=[25, 121], zoom_start=7)

m