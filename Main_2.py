from utils.sql import connPostgreSQL
import geopandas as gpd
from sqlalchemy import create_engine, text
from RiverBasinPolyData import unify_basin_in_river_poly
from matplotlib import pyplot as plt
import os
from utils.plot_utils import generate_randomcolor, transparent_cmap
from adjustText import adjust_text
import copy
from ComFacBiz import find_comfacbiz_fit
import pandas as pd

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.ion()

def read(basin_name=['二仁溪', '老街溪']):
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text(''' select * from taiwan ''')
        taiwan = gpd.read_postgis(sql, engine, geom_col='geometry')
        taiwan.to_crs(epsg=3826, inplace=True)
        print(f'完成讀取台灣圖資')

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text(''' select * from riverbasin where basin_name in :basin_name ''')
        params = {'basin_name': tuple(basin_name)}
        river_basin = gpd.read_postgis(sql, engine, geom_col='geometry', params=params)
        print(f'完成讀取流域圖資')

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text(''' select * from riverpoly_with_basin where basin_name in :basin_name ''')
        params = {'basin_name': tuple(basin_name)}
        river_poly = gpd.read_postgis(sql, engine, geom_col='geometry', params=params)
        # river_poly2 = unify_basin_in_river_poly(river_poly, river_basin) 
        # river_poly2.to_postgis('riverpoly_with_basin', engine, if_exists='replace', index=False)
        print(f'完成讀取河川圖資')

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = ''' select * from ground_water_map '''
        ground_water_map = gpd.read_postgis(sql, engine, geom_col='geometry')
        print(f'完成讀取地下水圖資')

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text(''' SELECT DISTINCT basin, sitename, geometry FROM river_monitoring_data_opendata where basin in ('二仁溪流域', '老街溪流域') ''')
        params = {'basin_name': tuple([f'{i}流域' for i in basin_name])}
        river_monitor_unique_station = gpd.read_postgis(sql, engine, geom_col='geometry')
        river_monitor_unique_station = river_monitor_unique_station.set_crs(epsg=4326)
        river_monitor_unique_station = river_monitor_unique_station.to_crs(epsg='3826') # 轉換座標系統
        river_monitor_unique_station.basin =river_monitor_unique_station.basin.str.replace('流域', '')
        river_monitor_unique_station.sitename = river_monitor_unique_station.sitename.apply(lambda i: i.split('(')[0])
        print(f'完成讀取河川監測站資料')

    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text(''' 
                SELECT a.測站編號, a.設置地, a.測站名稱, a.geometry, b.basin_name    FROM ground_water_monitor_station a
                inner join riverbasin as b ON ST_Contains(b.geometry , ST_Transform(a.geometry, 3826))
                WHERE b.basin_name  IN :basin_name ''')
        params = {'basin_name': tuple(basin_name)}
        ground_water_data = gpd.read_postgis(sql, engine, params=params, geom_col='geometry')
        print(f'完成讀取地下水監測站資料')


    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql  = text(''' SELECT * FROM agriculturalzone_basin_mini where basin_name in :basin_name ''')
        params = {'basin_name': tuple(basin_name)}
        farm = gpd.read_postgis(sql, engine, geom_col='geom', params=params)
        print(f'完成讀取農業法定用地資料')


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

        pol_site.drop(['x', 'y', 'geometry'], axis=1).to_excel('data/Water_pollution_Data/排放點_彙整.xlsx', index=False)

        comFacBizs = {}
        for chem in ['鉛', '鋅']:
            tmp = find_comfacbiz_fit(chem, time_between=[1071, 1114])
            comFacBizs[chem] = tmp.drop_duplicates(subset=['TWD97TM2X', 'TWD97TM2Y', 'comName'])
        return taiwan, river_basin, river_poly, ground_water_map, pol, pol_site, river_monitor_unique_station, ground_water_data, farm, comFacBizs


def plot(taiwan, river_basin, river_poly, ground_water_map, pol, pol_site, river_monitor_unique_station, ground_water_data, farm, comFacBizs):
    chemlist = ['鉛', '鋅']

    for basin in river_basin.basin_name:
        for chem in chemlist:

            plt.close('all')
            river_basin_plot = river_basin[river_basin.basin_name == basin]
            river_poly_plot = river_poly[river_poly.basin_name == basin]
            farm_plot = farm[farm.basin_name == basin]
            river_monitor_unique_station_plot = river_monitor_unique_station[river_monitor_unique_station.basin == basin]
            ground_water_data_plot = ground_water_data[ground_water_data.basin_name == basin]
            pol_site_plot = pol_site[(pol_site.basin_name == basin) & (pol_site.emi_item.apply(lambda x: chem in x.split(',')))]
            comFacBizs_plot = comFacBizs[chem]

            # 計算 river_monitor_unique_station_plot 半徑 5公里
            river_monitor_unique_station_plot_5km = copy.deepcopy(river_monitor_unique_station_plot)
            river_monitor_unique_station_plot_5km = river_monitor_unique_station_plot_5km.buffer(5000)
            # print(ground_water_data_plot)

            figsize = (6,6)
            fig, ax = plt.subplots(figsize=figsize)

            # # 找出最佳範圍
            river_basin_plot.plot(ax=ax, color=(.9, .9, .9), edgecolor='black', linewidth=1)
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            if basin == '老街溪':
                xlim = (xlim[0]*0.995, xlim[1]*1.015)
            ax.cla()


            cmap = generate_randomcolor(len(ground_water_map), toListedColormap=True)


            # # 重新繪圖流域
            river_basin.plot(ax=ax, color=(.5,.5,.5))
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            taiwan.plot(ax=ax, color=(.4,.07,.4,.1), edgecolor='None', linewidth=.2)

            river_basin_plot.plot(ax=ax, color=(.9, .9, .9), edgecolor='black', linewidth=1)
            river_poly_plot.plot(legend=True, ax=ax, edgecolor='grey', alpha=0.8, linewidth=.5)
            farm_plot.plot(ax=ax, color='green', alpha=0.15, linewidth=.5)
            river_monitor_unique_station_plot_5km.plot(ax=ax, color='red', alpha=0.15, linewidth=.5)
            # ground_water_map.plot(column='ZONNAME', color=(.2,.1,.9,.4),  alpha=0.15, legend=False, label='地下水', ax=ax)
            # ground_water_map.plot(column='ZONNAME', cmap=cmap,  alpha=0.15, legend=False, label='地下水', ax=ax)

            # handles = [ plt.Line2D([0], [0], color=c, lw=4, label=j['ZONNAME'])  for (i,j), c in zip(ground_water_map.iterrows(), cmap.colors) ]
            # labels= [j['ZONNAME'] for i,j in ground_water_map.iterrows() ]
            # ax.legend(handles=handles, labels=labels, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3)
            # handles, labels = ground_water_map_ax.get_legend_handles_labels()
            # print(handles, labels)%%


            ax.scatter(x=ground_water_data_plot.geometry.x, y=ground_water_data_plot.geometry.y, c='green', s=40, alpha=1, label='地下水測站', marker="^", linewidths=1)
            ax.scatter(x=river_monitor_unique_station_plot.geometry.x, y=river_monitor_unique_station_plot.geometry.y, c='red', s=40, alpha=1, label='河川水質測站', marker="o", linewidths=0)
            ax.scatter(x=pol_site_plot.geometry.x, y=pol_site_plot.geometry.y, c='blue', s=20, alpha=1, label='水污染源許可及申報資料', marker="*", linewidths=1)
            ax.scatter(x=comFacBizs_plot.TWD97TM2X, y=comFacBizs_plot.TWD97TM2Y, c='black', s=20, alpha=1, label='廠商資料', marker="x", linewidths=1)


            adjust_text([plt.text(i, j, s, fontsize=8, color='red' ,ha='center', va='center') for i, j, s in zip(river_monitor_unique_station_plot.geometry.x, river_monitor_unique_station_plot.geometry.y, river_monitor_unique_station_plot.sitename)])
            adjust_text([plt.text(i, j, s, fontsize=8, color='green' ,ha='center', va='center') for i, j, s in zip(ground_water_data_plot.geometry.x, ground_water_data_plot.geometry.y, ground_water_data_plot.測站名稱)])

            plt.legend(loc='lower left', bbox_to_anchor=(0, 0), ncol=1, frameon=False, fontsize=8)
            title = f'{basin}_{chem}'
            ax.set_title(title)
            fig_path = 'images/河川-排放點'
            fig_path_img = f'''{fig_path}/img/'''
            fig_path_fn = f'''{fig_path}/data/'''

            if not os.path.exists(fig_path_img):
                os.makedirs(fig_path_img)
            if not os.path.exists(fig_path_fn):
                os.makedirs(fig_path_fn)

            fig.savefig(f'''{fig_path_img}/{title}.png''', dpi=300)        

            pol_site_plot.drop(['geometry'], axis=1).to_excel(f'''{fig_path_fn}/{title}.xlsx''', index=False)


def find_distance_from_station():

    basin_name = ['二仁溪', '老街溪']
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        sql = text(''' SELECT DISTINCT basin, sitename, geometry FROM river_monitoring_data_opendata where basin in ('二仁溪流域', '老街溪流域') ''')
        params = {'basin_name': tuple([f'{i}流域' for i in basin_name])}
        river_monitor_unique_station = gpd.read_postgis(sql, engine, geom_col='geometry')
        river_monitor_unique_station = river_monitor_unique_station.set_crs(epsg=4326)
        river_monitor_unique_station = river_monitor_unique_station.to_crs(epsg='3826') # 轉換座標系統
        river_monitor_unique_station.basin =river_monitor_unique_station.basin.str.replace('流域', '')
        river_monitor_unique_station.sitename = river_monitor_unique_station.sitename.apply(lambda i: i.split('(')[0])
        print(f'完成讀取河川監測站資料')
    
    comFacBizs = {}
    chem_list = ['鉛', '鋅']
    for chem in chem_list:
        comFacBizs[chem] = find_comfacbiz_fit(chem, time_between=[1071, 1114])

    res = []
    for chem in chem_list:
        com = comFacBizs[chem]
        com_cal = gpd.GeoDataFrame(com, geometry=gpd.points_from_xy(com.TWD97TM2X, com.TWD97TM2Y))
        for basin in basin_name:
            station = river_monitor_unique_station[river_monitor_unique_station.basin == basin]
            for i, site in station.iterrows():
                # 找出com_cal和site的距離 < 5km的
                com_cal['distance'] = com_cal.geometry.distance(site.geometry)  
                com_cal_plot = com_cal[com_cal['distance'] < 5000.]
                com_cal_plot = com_cal_plot.sort_values(by='distance')
                com_cal_plot = com_cal_plot.drop_duplicates(subset=['comName', 'TWD97TM2X', 'TWD97TM2Y'], keep='first')
                com_cal_plot = com_cal_plot[['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'distance',]]
                com_cal_plot = com_cal_plot.assign(sitename=site.sitename, chemical=chem)
                res.append(com_cal_plot)
    res2 = pd.concat(res)
    res2.to_excel('data/Result_data/廠商與監測站距離試算/5公里內廠商與監測站距離.xlsx', index=False)


                

# def main():
#     data = read()
    # plot(*data)

