from bokeh.models import WMTSTileSource, Plot, Range1d, WMTSTileSource, WheelZoomTool, PanTool
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.layouts import column
from bokeh.models import ColumnDataSource


from pyproj import Proj, transform

import geopandas as gpd
from utils.sql import connPostgreSQL


def proj_transform(xlims, ylims):
    # 定義WGS 84和Web Mercator投影
    in_proj = Proj(proj='latlong', datum='WGS84')
    out_proj = Proj(proj='merc', a=6378137, b=6378137)

    # 轉換經緯度到Web Mercator坐標
    x1, y1 = transform(in_proj, out_proj, xlims[0], ylims[0])  # 左下角
    x2, y2 = transform(in_proj, out_proj, xlims[1], ylims[1])  # 右上角

    return (x1, x2), (y1, y2)


def dataFormat2bokeh_failed(data):
    # 這個不知為何無法和 wmts 一起使用
    def extract_coords(geom):
        if geom.type == 'Polygon':
            return [list(geom.exterior.coords.xy[0]), list(geom.exterior.coords.xy[1])]
        elif geom.type == 'MultiPolygon':
            all_coords_x = []
            all_coords_y = []
            for part in geom:
                all_coords_x.append(list(part.exterior.coords.xy[0]))
                all_coords_y.append(list(part.exterior.coords.xy[1]))
            return [all_coords_x, all_coords_y]
    data['coords'] = data['geometry'].apply(extract_coords)
    data['xs'] = [coords[0] for coords in data['coords']]
    data['ys'] = [coords[1] for coords in data['coords']]
    source = ColumnDataSource(data.drop(columns=['geometry', 'coords']))    
    return source


def read_data(name):
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        if name == 'taiwan':
            sql = ''' SELECT * FROM taiwan_mini'''
            data = gpd.read_postgis(sql, engine, geom_col='geometry')
            data = data.to_crs(epsg=3857)
            data.to_postgis('taiwan_mini_3857', engine, if_exists='replace')
        
        if name == 'riverpoly':
            sql = ''' SELECT * FROM riverpoly '''
            data = gpd.read_postgis(sql, engine, geom_col='geom')

    return data
def dataFormat2bokeh(data):
    xs = []
    ys = []

    # 循環遍歷每個多邊形，提取坐標
    for geom in data.geometry:
        if geom.geom_type == 'MultiPolygon':
            for poly in geom:
                x, y = poly.exterior.coords.xy
                xs.append(x.tolist())
                ys.append(y.tolist())
        elif geom.geom_type == 'Polygon':
            x, y = geom.exterior.coords.xy
            xs.append(x.tolist())
            ys.append(y.tolist())

    # 轉換為Bokeh的ColumnDataSource
    return ColumnDataSource(data={'xs': xs, 'ys': ys})



def createFiture(
        width=1200, 
        height=800,
        x_range=(119, 123), 
        y_range= (21.5, 25.5)
):
    x_range, y_range = proj_transform(x_range, y_range)
    p = figure(
        width=width, 
        height=height, 
        x_range=x_range, 
        y_range=y_range, 
        x_axis_type="mercator", 
        y_axis_type="mercator",
        # tools="pan,wheel_zoom,reset"

        )
    wheel_zoom = p.select(type=WheelZoomTool)
    p.toolbar.active_scroll = wheel_zoom[0]
    return p


def addLayer(
        p,
        taiwan=True,
        riverpoly=True,
    ):
    url = 'https://wmts.nlsc.gov.tw/wmts/EMAP/default/EPSG:3857/{z}/{y}/{x}'
    # url2 = 'http://210.68.245.182:62280/geoserver/gwc/service/wmts/rest/data:taiwan_mini/generic/EPSG:900913/EPSG:900913:{z}/{y}/{x}?format=image/png'
    url2 = 'http://localhost:5430/geoserver/gwc/service/wmts/rest/data:taiwan_mini/generic/EPSG:900913/EPSG:900913:{z}/{y}/{x}?format=image/png'
    tile_source1 = WMTSTileSource(url=url)
    tile_source2 = WMTSTileSource(url=url2)
    # p.add_tile(tile_source1)
    p.add_tile(tile_source2)
    if taiwan:
        source = dataFormat2bokeh(read_data('taiwan'))
        p.patches('xs', 'ys', source=source, fill_color="None", line_color="black")
    # p.multi_polygons('xs', 'ys', source=source, fill_color="white", line_color="black") # 搭配 dataFormat2bokeh_failed
    # p.toolbar.active_scroll = wheel_zoom


    # 顯示地圖
    show(p)

def main():
    p = createFiture()
    addLayer(
        p,
        taiwan=False,
        )