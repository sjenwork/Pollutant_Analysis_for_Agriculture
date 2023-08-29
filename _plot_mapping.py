from RiverMonitor import read_river_monitoring_data
from matplotlib import pyplot as plt
from utils.plot_utils import generate_randomcolor
from RiverBasinPolyData import read_river_basin, read_river_poly, unify_basin_in_river_poly
from TaiwanCounty import read_taiwan_geojson
from ComFacBiz import getComFacBiz_location, getComFacBiz_location_v2

import geopandas as gpd
import os

def plot_background(
            taiwan_map=None, 
            river_basin=None,
            river_poly=None,
            xlims='default',
            ylims='default',
            figsize=(21, 15),
            taiwan_focus = [],
            river_focus = [], # 如果有river_focus，則不會採用 taiwan_focus 所涵蓋的行政區，否則以taiwan_focus為主
            basin_focus = [], # 如果有basin_focus，則不會採用 river_focus 和 taiwan_focus 所涵蓋的行政區，否則以taiwan_focus為主
            taiwan_map_color='gray',
            ):
        if xlims == 'default':
            xlims = [119, 122.5]
        if ylims == 'default':
            ylims = [21.8, 25.5]
        plt.ion()
        plt.close('all')

        fig, ax = plt.subplots(figsize=figsize)
        # for 二仁溪 # ax.set_xlim([120.1, 120.5]) # ax.set_ylim([22.84, 23.02])

        if xlims is not None:
            ax.set_xlim(xlims)
            ax.set_ylim(ylims)


        if taiwan_map is not None:
            n = len(taiwan_map)
            cmap = generate_randomcolor(n, toListedColormap=True, random_seed=200, grey=True)
            taiwan_map = taiwan_map.assign(exist=0)
            if len(taiwan_focus)>0:
                index = taiwan_map[taiwan_map.COUNTYNAME.isin(taiwan_focus)].index
                if len(index) == 0:
                    raise Exception(f'taiwan_focus {taiwan_focus} is not in taiwan_map')
                taiwan_map.loc[index, 'exist'] = 1
            taiwan_map[taiwan_map.exist==0].plot(ax=ax, column='COUNTYNAME', edgecolor=(.2,.2,.2), alpha=.9, legend=False, color=taiwan_map_color)
            if len(taiwan_focus)>0:
                taiwan_map[taiwan_map.exist==1].plot(ax=ax, column='COUNTYNAME', edgecolor=(.2,.2,.2), alpha=.9, legend=False, color='none')

        if river_basin is not None:
            n = len(river_basin)
            cmap = generate_randomcolor(n, toListedColormap=True, random_seed=200, grey=False)
            # 如果有去算出流域 和 資料的交集，就用以下這段
            cal_intersect = False
            if cal_intersect:
                river_basin[river_basin.exist==0].plot(
                        ax=ax, column='BASIN_NAME', edgecolor="purple", 
                        alpha=.3, color='white',
                        )
                river_basin[river_basin.exist==1].plot(
                        ax=ax, column='BASIN_NAME', edgecolor="purple", 
                        alpha=.5, legend=True, cmap=cmap,
                        legend_kwds={'loc': 'upper left', 'ncol': 1}
                        )          

                for idx, row in river_basin[river_basin.exist==1].iterrows():
                    ax.annotate(
                        text=row.BASIN_NAME, 
                        xy=(row.geometry.centroid.x, row.geometry.centroid.y), 
                        xytext=(row.geometry.centroid.x, row.geometry.centroid.y), 
                        arrowprops=dict(arrowstyle="->", color='black', lw=1), 
                        ha='center', va='center', fontsize=6, color='red')

            if len(basin_focus)>0:
                river_basin = river_basin.assign(exist=0)
                river_basin.loc[river_basin.BASIN_NAME.isin(basin_focus), 'exist'] = 1
                river_basin[river_basin.exist==0].plot(ax=ax, column='NAME_2014', edgecolor="purple", alpha=.3, legend=False, color='gray')
                river_basin[river_basin.exist==1].plot(ax=ax, column='NAME_2014', edgecolor="purple", alpha=.3, legend=False, color='none')
            else:
                river_basin.plot(
                        ax=ax, column='BASIN_NAME', edgecolor="purple", 
                        alpha=.3, color='white',
                        )
            for idx, row in river_basin.iterrows():
                ax.annotate(
                    text=row.BASIN_NAME, 
                    xy=(row.geometry.centroid.x, row.geometry.centroid.y), 
                    xytext=(row.geometry.centroid.x, row.geometry.centroid.y), 
                    arrowprops=dict(arrowstyle="->", color='black', lw=1), 
                    ha='center', va='center', fontsize=6, color='red')
            
        if river_poly is not None:
            if len(basin_focus)>0:
                river_poly = river_poly[river_poly.BASIN_NAME.isin(basin_focus)]
            elif len(river_focus)>0:
                river_poly = river_poly[river_poly.RIVER_NAME.isin(river_focus)]
            elif len(taiwan_focus)>0:
                taiwan_map_focus = taiwan_map[taiwan_map.exist==1]
                joined = gpd.sjoin(river_poly, taiwan_map_focus, how='inner', op='within')
                river_poly = river_poly.loc[joined.index]

            river_poly.plot( 
                legend=True, ax=ax, 
                edgecolor='grey', alpha=0.2, 
                linewidth=.5)  

        return fig, ax
    
def pin_river_monitor(
        figax=None,
        figsize=(7, 9),
        river_monitor=None,
        doannotate=False,
        size=4,
        color='red',
        alpha=.6,
        marker='^',
        ):
    if figax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = figax
    
    if river_monitor is not None:
        river_monitor_unique_station = river_monitor.drop_duplicates(subset=['sitename', 'twd97lon', 'twd97lat'])
        ax.scatter(river_monitor_unique_station['twd97lon'], river_monitor_unique_station['twd97lat'], c=color, s=size, alpha=alpha, label='監測站', marker=marker, linewidths=1)

        if doannotate:
            for idx, row in river_monitor_unique_station.iterrows():
                ax.annotate(
                    text=row.sitename, 
                    xy=(row.geometry.centroid.x, row.geometry.centroid.y), 
                    xytext=(row.geometry.centroid.x+0.03, row.geometry.centroid.y+0.01), 
                    arrowprops=dict(arrowstyle="->", color='black', lw=1), 
                    ha='center', va='center', fontsize=6, color='red')

    return fig, ax

def pin_ComFac(
        figax=None,
        figsize=(7, 9),
        comFacBizs=None,
        color='blue',
        alpha=.6,
        size=4,
        marker="*",
    ):
    if figax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = figax
    
    if comFacBizs is not None:
        ax.scatter(comFacBizs['twd97lon'], comFacBizs['twd97lat'], c=color, s=size, alpha=alpha, label='廠商', marker=marker, linewidths=1)

    return fig, ax

def pin_groundwater(
        figax=None,
        figsize=(7, 9),
        data=None,
        color='blue',
        alpha=.6,
        size=4,
        marker="*",
    ):
    if figax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = figax
    
    if data is not None:
        ax.scatter(data['twd97lon'], data['twd97lat'], c=color, s=size, alpha=alpha, label='廠商', marker=marker, linewidths=1)

    return fig, ax

def pin_pol(
        figax=None,
        figsize=(7, 9),
        data=None,
        color='blue',
        alpha=.6,
        size=4,
        marker="*",
    ):
    if figax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig, ax = figax
    
    if data is not None:
        ax.scatter(data['twd97lon'], data['twd97lat'], c=color, s=size, alpha=alpha, label='廠商', marker=marker, linewidths=1)

    return fig, ax

def plot_legend(fig, ax, selected_labels):
    # 獲取所有的圖例物件和標籤
    handles, labels = ax.get_legend_handles_labels()

    # 創建一個字典，將標籤映射到相對應的圖例物件
    label_to_handle = dict(zip(labels, handles))

    # 選擇你想要的圖例標籤
    # selected_labels = ['Label 1', 'Label 2']

    # 獲取選擇的圖例物件
    selected_handles = [label_to_handle[label] for label in selected_labels]

    # 創建圖例
    ax.legend(handles=selected_handles, labels=selected_labels)       
    return fig, ax 


def mixed_plot(
        comFacBizs,
        river_monitoring_data,
        chem_info, 
        region_info, 
        basin_focus = ['鹽水溪', '二仁溪', '老街溪', '南崁溪'], 
        background_info=None,
        save_river_monitor_fig=False,
        fig_path_1=f'images/疊圖/監測站位置布點_含名稱',  #搭配 save_river_monitor_fig 的存檔路徑
        fig_path_2=f'images/疊圖/水質測站與廠商分佈_v2',  # 完整繪圖的存檔路徑
        ):
    '''
    1. 畫地圖
    2. 畫流域
    3. 畫河川
    4. 畫河川監測站
    5. 畫廠商座標
    '''
    # 資料準備
    if background_info is None:
        print('read background info')
        taiwan_map = read_taiwan_geojson(contains=[])
        river_poly = read_river_poly()
        river_poly = unify_basin_in_river_poly(river_poly, river_basin) 
        river_basin = read_river_basin()
    else:
        print('use background info')
        taiwan_map = background_info['taiwan_map']
        river_poly = background_info['river_poly']
        river_basin = background_info['river_basin']

    countys = region_info['countys']
    river_monitoring_data = river_monitoring_data[river_monitoring_data.county.isin(countys)]

    # 畫圖
    fig, ax = plot_background(
        taiwan_map=taiwan_map, 
        river_basin=river_basin, 
        river_poly=river_poly,
        # xlims=[119, 122.5], ylims=[21.8, 25.5], # 全台
        # xlims=[120.96, 121.4], ylims=[24.8, 25.18], # 桃園
        xlims=region_info['xlims'], ylims=region_info['ylims'],
        figsize=(9, 7),
        # figsize=(9, 7),
        basin_focus=basin_focus,
        taiwan_focus=countys,
        # river_focus=['南崁溪', '新街溪', '老街溪', '社子溪']
        )

    fig, ax = pin_river_monitor(
            # figax=None,
            figax=(fig, ax),
            # figsize=(9, 9),
            river_monitor=river_monitoring_data,
    )

    if not os.path.exists(fig_path_1):
        os.makedirs(fig_path_1)

    if save_river_monitor_fig:
        fig.savefig(f'''{fig_path_1}/{'_'.join(countys)}.png''', dpi=300)

    fig, ax = pin_ComFac(
            # figax=None,
            figax=(fig, ax),
            # figsize=(9, 9),
            comFacBizs=comFacBizs,        
    )
    fig, ax = plot_legend(fig, ax, selected_labels=['監測站', '廠商'])

    ax.set_title(f'{chem_info}', fontsize=16)

    if not os.path.exists(fig_path_2):
        os.makedirs(fig_path_2)
    fig.savefig(f'''{fig_path_2}/{'_'.join(countys)}__{chem_info}_zoomin.png''', dpi=300)
    

    


if __name__ == '__main__':

    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.ion()

    chem_list = ['鉛', '鋅', '鎘']
    # chem_info = chem_list[0]
    region_list = [
        { "countys": ['桃園市'], "xlims":[120.96, 121.4], "ylims":[24.8, 25.18] },
        { "countys": ['臺南市', '高雄市'], "xlims":[120.1, 120.5], "ylims":[22.8, 23.2] },
    ]
    background_info = {
        "taiwan_map": read_taiwan_geojson(contains=[]),
        "river_poly": read_river_poly(),
        "river_basin": read_river_basin()
    }
    background_info["river_poly"] = unify_basin_in_river_poly(
        background_info['river_poly'], background_info['river_basin']
        ) 
    

    river_monitoring_data = read_river_monitoring_data()
    time_between = [1071, 1114]
    for chem_info in chem_list[:]:
        for region_info in region_list[:]:
            # comFacBizs = getComFacBiz_location(chem)   #全部廠商
            comFacBizs = getComFacBiz_location_v2(chem_info, time_between) # 廠商做了進一步的篩選
            mixed_plot(
                comFacBizs=comFacBizs,
                river_monitoring_data=river_monitoring_data,
                chem_info=chem_info,
                region_info=region_info,
                background_info=background_info,
                save_river_monitor_fig=True,
                fig_path_1=f'images/疊圖/監測站位置布點_含名稱',  #搭配 save_river_monitor_fig 的存檔路徑
                fig_path_2=f'images/疊圖/水質測站與廠商分佈_{time_between[0]}-{time_between[1]}',  # 完整繪圖的存檔路徑
            )