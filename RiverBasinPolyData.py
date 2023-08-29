import geopandas as gpd

def read_river_poly(contains=[]):
    river = gpd.read_file('data/River_Basin_Poly/riverpoly/riverpoly.shp')
    river2 = river.to_crs('epsg:4326')    
    if contains:
        river2 = river2[river2['RIVER_NAME'].str.contains('|'.join(contains)).fillna(False)]
    return river2

def read_river_poly_json(contains=[]):
    river = gpd.read_file('data/River_Basin_Poly/riverpoly/riverpoly_compress.json')
    # river2 = river.to_crs('epsg:4326')    
    if contains:
        river = river[river['RIVER_NAME'].str.contains('|'.join(contains)).fillna(False)]
    return river

def read_river_basin():
    basin = gpd.read_file('data/River_Basin_Poly/basin/basin.shp')
    basin = basin.to_crs('epsg:4326')    
    return basin

def unify_basin_in_river_poly(river_poly, river_basin):
    '''
    將同個流域內的所有河川，統一為同一個流域名稱
    '''
    # 执行空间连接
    joined = gpd.sjoin(river_poly, river_basin, how='left', op='intersects')
    try:
        river_poly = joined[list(river_poly.columns) + ['BASIN_NAME']]
    except:
        columns = list(river_poly.columns.drop('gid')) + ['basin_name']
        river_poly = joined[columns]

    # --- 有重複比對到多個basin的，從面積去排序，但失敗了...... 
    if False:
        joined = joined.dropna(subset=['index_right'])
        # 從river_basin取出對應的geometry
        joined['geometry_basin'] = joined['index_right'].apply(lambda x: river_basin.loc[x, 'geometry'])
        # 計算交集面積
        joined['intersection_area'] = joined.apply(lambda x: gpd.GeoSeries(x['geometry']).intersection(gpd.GeoSeries(x['geometry_basin'])).area, axis=1)
        # 按交集面積对每个river_poly的匹配进行排序，并只保留面积最大的
        joined = joined.reset_index()
        joined = joined.sort_values('intersection_area', ascending=False).groupby('index', as_index=False).first()
        # 新增 basin 欄位，其值為 BASIN_NAME 的對應值
        river_poly['basin'] = joined['BASIN_NAME']
    return river_poly