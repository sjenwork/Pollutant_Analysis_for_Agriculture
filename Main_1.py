from RiverBasinPolyData import unify_basin_in_river_poly
from matplotlib import pyplot as plt
from ComFacBiz import getComFacBiz_location, getComFacBiz_location_v2
from utils.sql import connPostgreSQL

from sqlalchemy import text
import numpy as np
import os
import pandas as pd
import geopandas as gpd
from adjustText import adjust_text

'''
Objective:
    1. 底圖：流域、河川；標注：廠商位置 與 河川監測站位置圖，並標注對應的名稱
    2. 計算廠商與河川監測站的距離
'''
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.ion()

def prepare_data(chem_list=['鉛', '鋅'], time_between=[107, 111]):
    '''
    已修改為使用postgresql的資料
    '''
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:

        ###### 讀取圖資
        sql = ''' select * from taiwan '''
        taiwan_map = gpd.read_postgis(sql, engine, geom_col='geom')
        print(f'完成讀取台灣圖資')

        sql = ''' select * from riverbasin '''
        river_basin = gpd.read_postgis(sql, engine, geom_col='geom')
        print(f'完成讀取流域圖資')

        sql = ''' select * from riverpoly '''
        river_poly = gpd.read_postgis(sql, engine, geom_col='geom')
        river_poly = unify_basin_in_river_poly(river_poly, river_basin) 
        print(f'完成讀取河川圖資')

        ###### 讀取資料
        # params = {'chem_list': tuple(chem_list), 'time_between': tuple([i+1911 for i in time_between])}
        # sql = text(''' 
        #            SELECT * FROM river_monitoring_data_opendata 
        #            WHERE itemname IN :chem_list AND EXTRACT(YEAR FROM sampledate2) in :time_between
        # ''')
        # river_monitoring_data = gpd.read_postgis(sql, engine, geom_col='geometry', params=params)

        sql = ''' SELECT DISTINCT basin, sitename, geometry FROM river_monitoring_data_opendata '''
        river_monitor_unique_station = gpd.read_postgis(sql, engine, geom_col='geometry')
        river_monitor_unique_station = river_monitor_unique_station.set_crs(epsg=4326)
        river_monitor_unique_station = river_monitor_unique_station.to_crs(epsg='3826') # 轉換座標系統
        print(f'完成讀取河川監測站資料')

        sql  = ''' SELECT * FROM agriculturalzone_basin_mini '''
        farm = gpd.read_postgis(sql, engine, geom_col='geom')
        print(f'完成讀取農業法定用地資料')

    return river_basin, river_poly, river_monitor_unique_station, taiwan_map, farm
    


def plot(BASIN_NAME, chem_info, time_between, data):
    '''
    已修改為使用postgresql的資料
    '''    
    farm = data['farm']
    river_basin = data['river_basin']
    river_poly = data['river_poly']
    river_monitor_unique_station = data['river_monitor_unique_station']


    comFacBizs = getComFacBiz_location_v2(chem_info, time_between) # 廠商做了進一步的篩選
    comFacBizs = comFacBizs.to_crs(epsg='3826') # 轉換座標系統

    # 農業法定用地
    farm_plot = farm[farm.basin_name == BASIN_NAME]

    # 選取河川流域
    # BASIN_NAME = '老街溪'
    river_basin_plot = river_basin[river_basin.basin_name == BASIN_NAME]
    river_poly_plot = river_poly[river_poly.basin_name == BASIN_NAME]

    # 選取河川監測站並排序
    river_monitor_unique_station_plot = river_monitor_unique_station[river_monitor_unique_station.basin.str.contains(BASIN_NAME)]
    river_monitor_unique_station_plot['x'] = river_monitor_unique_station_plot.geometry.x
    river_monitor_unique_station_plot['y'] = river_monitor_unique_station_plot.geometry.y
    if BASIN_NAME == '老街溪':
        river_monitor_unique_station_plot = river_monitor_unique_station_plot.sort_values(by='x')
    elif BASIN_NAME == '二仁溪':
        river_monitor_unique_station_plot = river_monitor_unique_station_plot.sort_values(by='y')

    # 從 river_basin_plot 的geometry 篩選出在流域內的廠商
    comFacBizs_basin = comFacBizs[comFacBizs.geometry.within(river_basin_plot.geometry.iloc[0])]
    if BASIN_NAME == '老街溪':
        comFacBizs_basin = comFacBizs_basin.sort_values(by='twd97lat')
    elif BASIN_NAME == '二仁溪':
        comFacBizs_basin = comFacBizs_basin.sort_values(by='twd97lon')

    # 繪圖
    plt.close('all')

    if BASIN_NAME == '老街溪':
        figsize = (8, 8)
    elif BASIN_NAME == '二仁溪':
        figsize = (9, 6)

    fig, ax = plt.subplots(figsize=figsize)
    # 找出最佳範圍
    river_basin_plot.plot(ax=ax, color=(.9, .9, .9), edgecolor='black', linewidth=1)
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    if BASIN_NAME == '老街溪':
        xlim = (xlim[0], xlim[1]*1.015)
    ax.cla()

    # 重新繪圖流域
    river_basin.plot(ax=ax, color=(.5,.5,.5))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    river_basin_plot.plot(ax=ax, color=(.9, .9, .9), edgecolor='black', linewidth=1)

    # 繪製農業法定用地
    farm_plot.plot(ax=ax, color='green', alpha=0.15, linewidth=.5)
    # 繪製河川
    river_poly_plot.plot(legend=True, ax=ax, edgecolor='grey', alpha=0.8, linewidth=.5)


    # 標記測站
    ax.scatter(river_monitor_unique_station_plot.geometry.x, river_monitor_unique_station_plot.geometry.y, c='red', s=40, alpha=1, label='測站', marker="o", linewidths=0)

    if True:
        # 使用adjust_text 標記測站
        texts = adjust_text([plt.text(i, j, s, fontsize=8, ha='center', va='center') for i, j, s in zip(river_monitor_unique_station_plot.geometry.x, river_monitor_unique_station_plot.geometry.y, river_monitor_unique_station_plot.sitename)])

    if False:
        # 使用annotate 標記測站
        labels_1 = [i.sitename for j,i in river_monitor_unique_station_plot.iterrows()]

        left_side = np.linspace(ylim[0], ylim[1], len(river_monitor_unique_station_plot))

        bottom_side = np.linspace(xlim[0], xlim[1], len(river_monitor_unique_station_plot))
        for i, (label, point) in enumerate(zip(labels_1, river_monitor_unique_station_plot.geometry)):
            if BASIN_NAME == '老街溪':
                ax.annotate(label, xy=(point.x, point.y), xytext=(xlim[0]-xlim[1]*0.01, left_side[i]), textcoords='data', xycoords='data', ha='right', va='center',
                            arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', connectionstyle="arc3,rad=0.3", lw=1, color='red', ls='dashed'),
                            # arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', lw=1, color='red', ls='dashed'),
                            bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='black', pad=0),
                            annotation_clip=False)
            elif BASIN_NAME == '二仁溪':
                # ax.annotate(label, xy=(point.x, point.y), xytext=(xlim[0]-xlim[1]*0.01, top_side[i]), textcoords='data', xycoords='data', ha='right', va='center',
                #             arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', connectionstyle="arc3,rad=0.3", lw=1, color='red', ls='dashed'),
                #             bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='black', pad=0),
                #             annotation_clip=False)
                ax.annotate(label, xy=(point.x, point.y), xytext=(bottom_side[i], ylim[1]+0.001*ylim[1]), textcoords='data', xycoords='data', ha='center', va='bottom', rotation=90,
                            arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', connectionstyle="arc3,rad=0.3", lw=1, color='red', ls='dashed'),
                            bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='black', pad=0),
                            annotation_clip=False)

    # 標記廠商
    ax.scatter(comFacBizs_basin.geometry.x, comFacBizs_basin.geometry.y, c='blue', s=20, alpha=1, label='廠商', marker="*", linewidths=0)

    if True:
        # 使用adjust_text標記廠商
        texts = adjust_text([plt.text(i, j, n+1, fontsize=8, ha='center', va='center') for n,(i, j, s) in enumerate(zip(comFacBizs_basin.geometry.x, comFacBizs_basin.geometry.y, comFacBizs_basin.comName))])
        names = list(comFacBizs_basin.comName)
        for i, name in enumerate(names):
            if BASIN_NAME == '二仁溪':
                ax.text(xlim[1]*1.001, ylim[1] - i*(ylim[1]-ylim[0])/len(names), str(i+1)+'. '+name, ha='left', va='top')
            elif BASIN_NAME == '老街溪':
                ax.text(xlim[1]*1.001, ylim[0] + i*(ylim[1]-ylim[0])/len(names), str(i+1)+'. '+name, ha='left', va='bottom')
        plt.subplots_adjust(right=0.7)

    if False:
        # 使用annotate標記廠商
        labels_2 = [i.comName for j,i in comFacBizs_basin.iterrows()]

        right_side = np.linspace(ylim[0], ylim[1], len(comFacBizs_basin))
        top_side = np.linspace(xlim[0], xlim[1], len(comFacBizs_basin))
        
        for i, (label, point) in enumerate(zip(labels_2, comFacBizs_basin.geometry)):
            # 繪製從點到標籤的線條
            if BASIN_NAME == '老街溪':
                ax.annotate(label, xy=(point.x, point.y), xytext=(xlim[1]+xlim[1]*0.005, right_side[i]), textcoords='data', xycoords='data', ha='left', va='center',
                            # arrowprops=dict(arrowstyle='->', lw=1, color='blue'),
                            # arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', lw=1, color='blue', ls='dashed'),
                            arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', connectionstyle="arc3,rad=0.3", lw=1, color='blue', ls='dashed'),
                            bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='black', pad=0),
                            annotation_clip=False)
            elif BASIN_NAME == '二仁溪':
                ypos = ylim[1]+0.001*ylim[1] if point.y>2.537*10**6 else ylim[0]-0.001*ylim[1]
                va = 'bottom' if point.y>2.537*10**6 else 'top'
                ax.annotate(label, xy=(point.x, point.y), xytext=(top_side[i], ypos), textcoords='data', xycoords='data', ha='center', va=va, rotation=90,
                            arrowprops=dict(arrowstyle='-|>,head_length=0.4,head_width=0.2', connectionstyle="arc3,rad=0.", lw=1, color='blue', ls='dashed'),
                            bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='black', pad=0),
                            annotation_clip=False)


    title = f'{BASIN_NAME} {chem_info}'
    ax.set_title(title)
    fig_path = 'images/廠商_河川_農地分佈圖_有標記名稱'
    fig_path_1 = f'''{fig_path}/'''
    if not os.path.exists(fig_path_1):
        os.makedirs(fig_path_1)

    fig.savefig(f'''{fig_path_1}/{title}_v4_test.png''', dpi=600)


def main_plot():
    river_basin, river_poly, river_monitor_unique_station, taiwan_map, farm = prepare_data()

    data = {
        'river_basin': river_basin,
        'river_poly': river_poly,
        'river_monitor_unique_station': river_monitor_unique_station,
        'taiwan_map': taiwan_map,
        'farm': farm
    }
    time_between = [1071, 1114]
    chem_list = ['鉛', '鋅']
    BASIN_NAME_List = ['老街溪', '二仁溪']
    for BASIN_NAME in BASIN_NAME_List[:]:
        for chem_info in chem_list[:]:
            plot(BASIN_NAME, chem_info, time_between, data)




    




def calculat_distance(data):
    river_basin, river_poly, river_monitor_unique_station, taiwan_map, farm = prepare_data()
    river_monitor_unique_station = data['river_monitor_unique_station']
    comFacBizs = data['comFacBizs']
    river_basin = data['river_basin']

    time_between = [1071, 1114]
    chem_list = ['鉛', '鋅']
    BASIN_NAME_List = ['老街溪', '二仁溪']
    for BASIN_NAME in BASIN_NAME_List[:]:
        for chem_info in chem_list[:]:
            river_monitor_unique_station_plot = river_monitor_unique_station[river_monitor_unique_station.basin.str.contains(BASIN_NAME)]
            comFacBizs = getComFacBiz_location_v2(chem_info, time_between) # 取得廠商資料
            comFacBizs = comFacBizs.to_crs(epsg='3826') # 轉換座標系統
            river_basin_plot = river_basin[river_basin.basin_name == BASIN_NAME]
            comFacBizs_basin = comFacBizs[comFacBizs.geometry.within(river_basin_plot.geometry.iloc[0])]

            gdfA = river_monitor_unique_station_plot[['sitename', 'geometry']]
            gdfB = comFacBizs_basin[['comName', 'geometry']]
            gdfA['x'] = gdfA.geometry.x
            gdfA['y'] = gdfA.geometry.y
            gdfB['x'] = gdfB.geometry.x
            gdfB['y'] = gdfB.geometry.y
            if BASIN_NAME == '老街溪':
                gdfA = gdfA.sort_values(by="y")
                gdfB = gdfB.sort_values(by="y")
            elif BASIN_NAME == '二仁溪':
                gdfA = gdfA.sort_values(by="x")
                gdfB = gdfB.sort_values(by="x")


            nA = len(gdfA)
            nB = len(gdfB)
            dist_matrix = np.zeros((nA, nB))

            for i in range(nA):
                for j in range(nB):
                    dist_matrix[i, j] = gdfA.geometry.iloc[i].distance(gdfB.geometry.iloc[j])/1000
            dist_matrix = pd.DataFrame(dist_matrix, index=gdfA.sitename, columns=gdfB.comName).T

            dist_matrix.to_excel(f'data/Result_data/廠商與監測站距離試算/{BASIN_NAME}_{chem_info}_距離.xlsx')

