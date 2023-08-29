import geopandas as gpd

def twd97_to_wgs84(df, x_col=None, y_col=None):
    '''
    和 ComFacBiz 中的不同， ComFacBiz 的是 Point ，這裡是 Polygon
    '''
    if 'geometry' not in df.columns:
        df_gpd = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['x_col'], df['x_col']) )
    else:
        df_gpd = df.copy()
    if df_gpd.crs == None:
        df_gpd = df_gpd.set_crs(epsg=3826)
    df_gpd = df_gpd.to_crs(epsg=4326)
    return df_gpd