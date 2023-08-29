import pathlib
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
from utils.sql import connSQL
from sqlalchemy import text
import re
import copy
from shapely.geometry import Point

from RiverBasinPolyData import read_river_basin
from TaiwanCounty import read_taiwan_admin_map
from utils.sql import connPostgreSQL
from RiverBasinPolyData import read_river_basin, read_river_poly, unify_basin_in_river_poly
from ComFacBiz import find_comfacbiz_fit

from _plot_mapping import plot_background, pin_ComFac, pin_river_monitor, pin_groundwater, pin_pol

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.ion()


def read_raw_data():
    df_twd97 = pd.read_csv('data/化學雲所有廠商資料/ComFacBizData_withXY_twd97.csv', index_col=0)
    df_wgs84 = pd.read_csv('data/化學雲所有廠商資料/ComFacBizData_withXY_wgs84.csv', index_col=0)

    # 比較 ComFacBizAddr、RegularAddr 兩欄位
    df_twd97_1 = df_twd97.loc[df_twd97.ComFacBizAddr != df_twd97.RegularAddr, ['ComFacBizAddr', 'RegularAddr']]
    df_twd97_2 = df_twd97.loc[df_twd97.RegularAddress != df_twd97.RegularAddr, ['ComFacBizAddr', 'RegularAddress']]
    df_twd97_3 = df_twd97.loc[df_twd97.CompanyAddress != df_twd97.RegularAddr, ['df_wgs84', 'RegularAddr']]
    df_twd97_4 = df_twd97.loc[df_twd97.CompanyAddress != df_twd97.ComFacBizAddr, ['CompanyAddress', 'ComFacBizAddr']]
    df_twd97_5 = df_twd97.loc[df_twd97.CompanyAddress != df_twd97.CompanySegAddress, ['CompanyAddress', 'CompanySegAddress']]

    df_wgs84_1 = df_wgs84.loc[df_wgs84['RegularAddr'] != df_wgs84['RegularAddr.1'], ['RegularAddr', 'RegularAddr.1']]

    '''
    ComFacBizAddr 是 原始地址
    RegularAddr 是 經過清理後的地址 （系統上）：移除地址中的 括號、括號內可能是樓層、郵遞區號，但可能會有全形數字
    RegularAddress 是 經過清理後的地址 （TGOS）：全形數字也處理掉了

    df_wgs84 中：
    RegularAddr 和 RegularAddr.1，後者是google標準化後的，但是半形全形沒有變，只是把中文數字變成阿拉伯數字
    '''

    df_twd97_final = df_twd97[['ComFacBizType', 'AdminNo', 'ComFacBizAdminNo', 'ComFacBizFactoryRegNo', 'ComFacBizName',
                               'CompanyAddress', 'TWD97TM2X', 'TWD97TM2Y', 'status', 'msg']]
    
    
    ''' 測試用
    def try_convert_to_float(x):
        try:
            return float(x)
        except:
            return float('nan')    
    q = df_twd97_final.TWD97TM2X.apply(try_convert_to_float)
    ind = q[q.isna()].index
    df_twd97_final.loc[ind]
    df_twd97.drop(ind).Type.unique()
    
    '''

    df_twd97_final.loc[df_twd97_final.Type!=1, ['TWD97TM2X', 'TWD97TM2Y']] = np.nan
    gdf_twd97_final = gpd.GeoDataFrame(df_twd97_final, geometry=gpd.points_from_xy(df_twd97_final.TWD97TM2X, df_twd97_final.TWD97TM2Y), crs='EPSG:3826')


    # taiwan = read_taiwan_admin_map()
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        gdf_twd97_final.to_postgis('comfacbiz_all', engine, if_exists='replace', index=False, chunksize=10000)


def view_data():
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = '''
            SELECT com.*, twn.*
            FROM comfacbiz_all com, taiwan twn
            WHERE ST_Within(com.geometry , ST_Transform(twn.geom, 3826)) 
                ''' #跑不出來，太大了
        sql = '''
            select * from comfacbiz_all where status = 1
        '''
        
        comFacBizs = gpd.read_postgis(sql, engine, geom_col='geometry')

    comFacBizs_1 = find_comfacbiz_fit('鋅', time_between=[1071, 1114])
    comFacBizs_2 = find_comfacbiz_fit('鉛', time_between=[1071, 1114])

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        # 從 tawian轉成epsg3826後的行政區劃分的geometry找出所有和桃園有交集的basin，
        sql = '''
            SELECT basin.*
            FROM taiwan twn, riverbasin basin
            WHERE ST_Intersects(ST_transform (twn.geometry, 3826), basin.geometry) AND twn.countyname = '桃園市'
        '''
        river_basin = gpd.read_postgis(sql, engine, geom_col='geometry')
        river_basin_bk = copy.deepcopy(river_basin)
        river_basin = copy.deepcopy(river_basin_bk)

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = ''' select * from riverpoly_with_basin '''
        river_poly = gpd.read_postgis(sql, engine, geom_col='geometry')
        # river_poly = river_poly.set_geometry('geomery')
        river_poly_bk = copy.deepcopy(river_poly)

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = ''' select distinct sitename, geometry from river_monitoring_data_opendata '''
        river_monitoring = gpd.read_postgis(sql, engine, geom_col='geometry')
        river_monitoring = river_monitoring.set_geometry('geometry')
        river_monitoring_bk = copy.deepcopy(river_monitoring)

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        basin_name=['二仁溪', '老街溪']
        basin_name = river_basin.BASIN_NAME.unique().tolist()
        sql  = text(''' SELECT * FROM agriculturalzone_basin_mini where basin_name in :basin_name ''')
        params = {'basin_name': tuple(basin_name)}
        farm = gpd.read_postgis(sql, engine, geom_col='geom', params=params)

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        basin_name = river_basin.BASIN_NAME.unique().tolist()
        sql = text(''' 
                SELECT a.測站編號, a.設置地, a.測站名稱, a.geometry, b.basin_name FROM ground_water_monitor_station a
                inner join riverbasin as b ON ST_Contains(b.geometry , ST_Transform(a.geometry, 3826))
                WHERE b.basin_name  IN :basin_name ''')
        params = {'basin_name': tuple(basin_name)}
        ground_water_data = gpd.read_postgis(sql, engine, params=params, geom_col='geometry')

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text('''
            SELECT a.ems_no, a.fac_name, a.address, a.unino, a.per_no , a.per_type , a.let_emi, a.let_watertype ,  b.basin_name, a.emi_item , a.emi_value, a.emi_units , a.geometry 
            FROM water_pollution_data as a
            inner JOIN riverbasin as b ON ST_Contains(b.geometry , ST_Transform(a.geometry, 3826))
            WHERE b.basin_name  IN :basin_name
            ''')
        params = {'basin_name': tuple(basin_name)}
        pol = gpd.read_postgis(sql , engine, geom_col='geometry', params=params)
        print(f'完成讀取污染排放')

        pol.fillna('', inplace=True)
        pol = pol.assign(x=pol.geometry.x, y=pol.geometry.y)
        pol_site = pol.groupby(['x', 'y', 'basin_name'], as_index=False).agg({
            'ems_no': lambda x: ','.join(set(x)),
            'fac_name': lambda x: ','.join(set(x)),
            'address': lambda x: ','.join(set(x)),
            'let_watertype': lambda x: ','.join(set(x)),
            'emi_item': lambda x: ','.join(set(x)),
            'geometry': 'first',

        })
        pol_site = gpd.GeoDataFrame(pol_site)        
        pol_site.set_crs(epsg=4326, inplace=True)
        pol_site.to_crs(epsg=3826, inplace=True)

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = ''' select s.* 
        from soil_groundwater_data s, taiwan twn
        where ST_Intersects(ST_transform (twn.geometry, 3826), s.geometry) AND twn.countyname = '桃園市' 
        '''
        soilpol = gpd.read_postgis(sql , engine, geom_col='geometry')

    taiwan_map = read_taiwan_admin_map()
    taiwan_map = taiwan_map.to_crs('EPSG:3826')

    comFacBizs['twd97lon'] = comFacBizs.geometry.x
    comFacBizs['twd97lat'] = comFacBizs.geometry.y

    comFacBizs_1 = gpd.GeoDataFrame(comFacBizs_1, geometry=gpd.points_from_xy(comFacBizs_1.TWD97TM2X, comFacBizs_1.TWD97TM2Y))
    comFacBizs_1['twd97lon'] = comFacBizs_1.geometry.x
    comFacBizs_1['twd97lat'] = comFacBizs_1.geometry.y
    comFacBizs_1 = comFacBizs_1[comFacBizs_1.addr.str.contains('桃園')]
    comFacBizs_1.geometry.unique()

    comFacBizs_2 = gpd.GeoDataFrame(comFacBizs_2, geometry=gpd.points_from_xy(comFacBizs_2.TWD97TM2X, comFacBizs_2.TWD97TM2Y))
    comFacBizs_2['twd97lon'] = comFacBizs_2.geometry.x
    comFacBizs_2['twd97lat'] = comFacBizs_2.geometry.y
    comFacBizs_2 = comFacBizs_2[comFacBizs_2.addr.str.contains('桃園')]
    comFacBizs_2.geometry.unique()

    comFacBizs2 = {}
    comFacBizs2['鋅'] = comFacBizs_1
    comFacBizs2['鉛'] = comFacBizs_2


    river_basin = river_basin.rename({'basin_name': 'BASIN_NAME', 'geom': 'geometry'}, axis=1)
    # river_basin = river_basin.set_geometry('geometry')  
    # river_basin = river_basin.set_crs(epsg=3826)
    # river_basin2 = read_river_basin()
    # gdf.plot()
    # river_poly2 = unify_basin_in_river_poly(river_poly, river_basin.drop('gid', axis=1))
    river_poly2 = river_poly
    # river_poly2 = river_poly2.rename({"river_name": "RIVER_NAME", 'geom': 'geometry'}, axis=1)
    # river_poly2 = river_poly2.set_geometry('geometry')

    # river_monitoring = river_monitoring.set_crs(epsg=4326)
    river_monitoring = river_monitoring.to_crs('EPSG:3826')
    river_monitoring['twd97lon'] = river_monitoring.geometry.x
    river_monitoring['twd97lat'] = river_monitoring.geometry.y

    ground_water_data['twd97lon'] = ground_water_data.geometry.x
    ground_water_data['twd97lat'] = ground_water_data.geometry.y

    pol_site['twd97lon'] = pol_site.geometry.x
    pol_site['twd97lat'] = pol_site.geometry.y
    pol_site = pol_site[['twd97lon', 'twd97lat', 'fac_name', 'geometry']]

    soilpol['twd97lon'] = soilpol.geometry.x
    soilpol['twd97lat'] = soilpol.geometry.y

    rb_focus = ['二仁溪', '老街溪']
    item_params = { 
        '二仁溪': { "xlim":[164000, 198000], "ylim":[2523000, 2546000]}, # 桃園 
        # '二仁溪': { "xlim":None, "ylim":None}, # 桃園 
        '老街溪': { "xlim":[264000, 275000], "ylim":[2745000, 2776000]}, # 桃園 
        '桃園市': { "xlim":[240000, 300000], "ylim":[2720000, 2782000]}, # 桃園 

    }
    county_focus = ['桃園市']

    plot_by = 'river_basin'
    plot_by = 'county'

    if plot_by == 'county':
        for chem in ['鋅', '鉛']:   
            taiwan_map_plot = copy.deepcopy(taiwan_map)
            taiwan_map_plot = taiwan_map_plot.assign(exist=0)
            for item in county_focus[:]:
                taiwan_map_plot.loc[taiwan_map_plot.COUNTYNAME == item, 'exist'] = 1
                plt.close('all')
                fig, ax = plot_background(
                taiwan_map=taiwan_map, 
                river_basin=river_basin, 
                river_poly=river_poly,
                # xlims=None, ylims=None, # 全台
                xlims=item_params[item]['xlim'], ylims=item_params[item]['ylim'], # 桃園
                # xlims=[150000, 350000], ylims=[2400000, 2800000], # 全台
                # xlims=region_info['xlims'], ylims=region_info['ylims'],
                figsize=(12, 12),
                # figsize=(9, 7),
                # basin_focus=[item],
                taiwan_focus=item.split(','),
                # river_focus=[item],
                taiwan_map_color='lightgray',
                )
                farm.plot(ax=ax, color='green', alpha=0.15, linewidth=.5)

                fig, ax = pin_river_monitor(
                        # figax=None,
                        figax=(fig, ax),
                        # figsize=(9, 9),
                        river_monitor=river_monitoring,
                        size=10,
                )

                fig, ax = pin_groundwater(
                        # figax=None,
                        figax=(fig, ax),
                        # figsize=(9, 9),
                        data=ground_water_data,
                        color='blue',
                        alpha=0.9,
                        size=10,
                        marker='o',
                )


                fig, ax = pin_ComFac(
                        # figax=None,
                        figax=(fig, ax),
                        # figsize=(9, 9),
                        comFacBizs=comFacBizs2[chem],        
                        # color=(0.2, 0.7, 0.7),
                        color=(0.1, 0.4, 0.7),
                        alpha=1,
                        size=7,
                        marker='x',
                )    

                taiwan_map_plot[taiwan_map_plot.exist==0].plot(ax=ax, column='COUNTYNAME', edgecolor=(.2,.2,.2), alpha=1, legend=False, color=(0.9,0.9,0.9,1))
                ax.scatter(soilpol['twd97lon'], soilpol['twd97lat'], c='brown', s=10, alpha=1, label='', marker='^', linewidths=1)

                name = f'桃園廠商分佈圖_{chem}'
                # name = f'{rb}流域 所有廠商分佈圖_test'
                plt.title(name)
                pth = 'images/所有廠商'
                fullname = os.path.join(pth, name)
                plt.savefig(fullname, dpi=300)


        # 存成 geojson 
        taiwan_map.to_file('data/for_web/taiwan_map.geojson', driver='GeoJSON', encoding='utf-8')
        comFacBizs_1_1 = comFacBizs_1.drop_duplicates(subset=['twd97lon', 'twd97lat'])
        comFacBizs_1_1.to_file('data/for_web/comFacBizs_鉛.geojson', driver='GeoJSON', encoding='utf-8')
        comFacBizs_2_1 = comFacBizs_2.drop_duplicates(subset=['twd97lon', 'twd97lat'])
        comFacBizs_2_1.to_file('data/for_web/comFacBizs_鋅.geojson', driver='GeoJSON', encoding='utf-8')
        river_basin.to_file('data/for_web/river_basin.geojson', driver='GeoJSON', encoding='utf-8')
        river_poly.to_file('data/for_web/river_poly.geojson', driver='GeoJSON', encoding='utf-8')
        

        river_monitoring.to_file('data/for_web/河川監測測站.geojson', driver='GeoJSON', encoding='utf-8')
        ground_water_data.to_file('data/for_web/地下水監測站.geojson', driver='GeoJSON', encoding='utf-8')
        soilpol.to_file('data/for_web/土壤及地下水污染場址位置.geojson', driver='GeoJSON', encoding='utf-8')
        
    if plot_by == 'river_basin':
        for rb in rb_focus[:]:
            plt.close('all')
            fig, ax = plot_background(
            taiwan_map=taiwan_map, 
            # river_basin=river_basin, 
            # river_poly=river_poly2,
            # xlims=None, ylims=None, # 全台
            # xlims=params[rb]['xlim'], ylims=params[rb]['ylim'], # 桃園
            xlims=[150000, 350000], ylims=[2400000, 2800000], # 全台
            # xlims=region_info['xlims'], ylims=region_info['ylims'],
            figsize=(9, 7),
            # figsize=(9, 7),
            # basin_focus=[rb],
            # taiwan_focus=countys,
            # river_focus=[rb],
            taiwan_map_color='lightgray',
            )

            farm.plot(ax=ax, color='green', alpha=0.15, linewidth=.5)
            
            fig, ax = pin_pol(
                    # figax=None,
                    figax=(fig, ax),
                    # figsize=(9, 9),
                    data=pol_site,
                    color='brown',
                    alpha=0.9,
                    size=10,
                    marker='x',            
            )

            fig, ax = pin_ComFac(
                    # figax=None,
                    figax=(fig, ax),
                    # figsize=(9, 9),
                    comFacBizs=comFacBizs,        
                    # color=(0.2, 0.7, 0.7),
                    color=(0.1, 0.4, 0.7),
                    alpha=0.9,
                    size=.4,
                    marker='.',
            )    

            fig, ax = pin_river_monitor(
                    # figax=None,
                    figax=(fig, ax),
                    # figsize=(9, 9),
                    river_monitor=river_monitoring,
                    size=10,
            )

            fig, ax = pin_groundwater(
                    # figax=None,
                    figax=(fig, ax),
                    # figsize=(9, 9),
                    data=ground_water_data,
                    color='blue',
                    alpha=0.9,
                    size=10,
                    marker='o',
            )




            name = f'全臺廠商分佈圖'
            # name = f'{rb}流域 所有廠商分佈圖_test'
            plt.title(name)
            pth = 'images/所有廠商'
            fullname = os.path.join(pth, name)
            plt.savefig(fullname, dpi=300)