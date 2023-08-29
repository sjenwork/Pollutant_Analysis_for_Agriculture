from utils.sql import connSQL
from pydantic import BaseModel
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from typing import List
import networkx as nx
import copy
import os

from RiverBasinPolyData import read_river_basin, read_river_poly, unify_basin_in_river_poly
from utils.plot_utils import generate_randomcolor, save_fig

from RiverMonitor import read_river_monitoring_data_ver3
from TaiwanCounty import read_taiwan_admin_map
from ComFacBiz import getComFacBiz, getComFacBiz_v2

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.ion()

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0


engine = connSQL('chemiPrim_Test_ssh')

chems = ['鉛', '鋅', '鎘']


river_poly = read_river_poly()
river_basin = read_river_basin()
taiwan_map = read_taiwan_admin_map()

river_poly = unify_basin_in_river_poly(river_poly, river_basin) 

plot_com_and_river = False
# 繪製廠商與河川的分佈
if plot_com_and_river:

    # 繪圖
    chem = chems[2]
    comFac = getComFacBiz(chem)
    # fig_path = 'images/廠商與河川分佈圖/'
    # comFac.reset_index(drop=True).to_excel(f'{fig_path}{chem}_廠商座標.xlsx')

    # 確認 river_basin 中的 geometry ，是否有包含 comFac 中的任意點，如果有，則在 river_basin 中新增欄位 exist，並設為 1，否則為 0
    joined = gpd.sjoin(river_basin, comFac, how='inner', op='contains')
    comFac['exist'] = 0
    comFac.loc[joined.index, 'exist'] = 1

    river_plot = river_poly
    filter_river_by_basin = True
    if filter_river_by_basin:
        # 依據找出包含水質測站的流域範圍，篩選出在此流域範圍內的河川資料
        joined2 = gpd.sjoin(river_poly, river_basin[river_basin.exist==1], how='inner', op='intersects')
        river_plot = river_poly.loc[joined2.index, :]


    # 繪圖

    selRegion = '桃園'
    xlims = {
        "全台": [[119, 122.5], [21.8, 25.5]],
        "桃園": [[121,121.4], [24.82, 25.12]],
        "台南": [[120, 120.8], [22.8,  23.3]],
             }
    
    plt.close('all')
    # fig, ax = plt.subplots(figsize=(21, 15))
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(xlims[selRegion][0])
    ax.set_ylim(xlims[selRegion][1])


    # 繪製basin，是否有和 廠商座標 有交集的（有顏色），和沒交集的（白色） 分開畫，
    n = len(river_basin)
    cmap = generate_randomcolor(n, toListedColormap=True, random_seed=200, grey=False)    
    river_basin[river_basin.exist==0].plot(
            ax=ax, column='BASIN_NAME', edgecolor="purple", 
            alpha=.3, color='white',
            )
    river_basin[river_basin.exist==1].plot(
            ax=ax, column='BASIN_NAME', edgecolor="purple", 
            alpha=.5, legend=False, cmap=cmap,
            legend_kwds={'loc': 'upper left', 'ncol': 1}
            )    
    # 河川
    river_plot.plot( legend=True, ax=ax, edgecolor='blue', alpha=1, linewidth=.5)

    # 行政區
    n = len(taiwan_map)
    cmap = generate_randomcolor(n, toListedColormap=True, random_seed=200, grey=True)
    taiwan_map.plot(ax=ax, column='countyname', edgecolor=(.2,.2,.2), alpha=.3, legend=False, cmap=cmap)    

    # 流域
    # leg = ax.get_legend()
    # leg.set_bbox_to_anchor((1, 1))
    # fig.subplots_adjust(left=-0.1)  # 數值越小，子圖離右邊界越近  

    # 在圖上標記每個basin的名稱，用箭頭指向basin的中心點
    for idx, row in river_basin[river_basin.exist==1].iterrows():
        ax.annotate(text=row.BASIN_NAME, xy=(row.geometry.centroid.x, row.geometry.centroid.y), xytext=(row.geometry.centroid.x, row.geometry.centroid.y), arrowprops=dict(arrowstyle="->", color='black', lw=1), ha='center', va='center', fontsize=12, color='red')    

    # 繪製散佈圖
    ax.scatter(comFac['twd97lon'], comFac['twd97lat'], c='red', s=4, alpha=.6, label='監測站', marker="^", linewidths=1)


    fig_name = f'{selRegion} - {chem}'
    ax.set_title(fig_name)
    fig_path = 'images/廠商與河川分佈圖/'
    save_fig(fig, fig_path, fig_name, dpi=300)    





# 繪製河川水質、廠商分佈
# bug. 水質測站沒有考慮到是不是有特定化學物質的監測
if True:
    chem = chems[2]
    # ver1
    # comFacBizs = getComFacBiz(chem)
    # 會有第二個版本，是把廠商做了進一步的篩選
    comFacBizs = getComFacBiz_v2(chem)


    countys = ['桃園市']
    xlims=[120.96, 121.4]# 桃園
    ylims=[24.8, 25.18]# 桃園
    # countys = ['台南市']
    # countys = ['臺南市', '高雄市']
    # xlims=[120, 121] # 較大範圍
    # ylims=[22.5, 23.4] # 較大範圍
    # xlims = [120.1, 120.5] # 較小範圍
    # ylims=[22.8, 23.2] # 較小範圍

    basin_focus = ['鹽水溪', '二仁溪', '老街溪', '南崁溪']

    monitoring_data_all = read_river_monitoring_data()
    # monitoring_data_all = read_river_monitoring_data_ver3() # 從歷史數據來的，沒有座標，所以不能布點
    monitoring_data_sub = monitoring_data_all[monitoring_data_all.county.isin(countys)]

    




    
    doannotate = False

    # 只標示測站（測站名稱），不畫廠商使用
    if doannotate:
        fig_path = f'images/疊圖/監測站位置布點_含名稱'
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
        fig.savefig(f'''{fig_path}/{'_'.join(countys)}.png''', dpi=300)    
    # 
    fig, ax = pin_ComFac(
            # figax=None,
            figax=(fig, ax),
            # figsize=(9, 9),
            comFacBizs=comFacBizs,        
    )
    fig, ax = plot_legend(fig, ax, selected_labels=['監測站', '廠商'])

    ax.set_title(f'{chem}', fontsize=16)

    fig_path = f'images/疊圖/水質測站與廠商分佈_v2'
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)
    fig.savefig(f'''{fig_path}/{'_'.join(countys)}__{chem}_zoomin.png''', dpi=300)



if True:
    # 以下這段比較亂，是要找出各流域的測站上下游的位置
    class RIVER_MONITOR_STATION(BaseModel):
        river: str
        station: List[str]= ''

    monitoring_data_all = read_river_monitoring_data()
    

    countys = ['桃園市', ]
    # countys = ['臺南市']
    # basin = ['南崁溪流域']
    # basin = ['老街溪流域']
    basin = ['鹽水溪流域']
    basin = ['二仁溪流域']

    # monitoring_data_sub2 = monitoring_data_all[monitoring_data_all.county.isin(countys)]
    # monitoring_data_sub2_station = monitoring_data_sub2.sitename.unique()
    monitoring_data_basin = monitoring_data_all[monitoring_data_all.basin.isin(basin)]
    monitoring_data_basin_station = monitoring_data_basin.sitename.unique()

    

    groups = {
        'group1': ['桃園市', '南崁溪流域'],
        'group2': ['桃園市', '老街溪流域'],
        'group3': ['臺南市', '鹽水溪流域'],
        'group4': ['臺南市', '二仁溪流域'],
    }


    def plot_map_diagram(
            edges,
            pos=None,
            path=None,
            name=None,
            figsize=(9, 9),
    ):
        def find_xylim(pos):
            # 從pos中分解出x和y的座標
            x_coords = [v[0] for v in pos.values()]
            y_coords = [v[1] for v in pos.values()]
            
            # 找出x和y座標的最小和最大值
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # 在最小和最大值的基礎上加上邊界
            x_margin = (x_max - x_min) * 0.3  # 10% 的邊界
            y_margin = (y_max - y_min) * 0.3  # 10% 的邊界
            
            return [(x_min - x_margin, x_max + x_margin), (y_min - y_margin, y_max + y_margin)]

        plt.close('all')
        fig, ax = plt.subplots(figsize=figsize)
        G = nx.DiGraph()
        G.add_edges_from(edges)
        if pos is None:
            pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=1500, edge_color='black', ax=ax)
        xlim, ylim = find_xylim(pos)
        ax.set_xlim(*xlim)  # x軸範圍從-1到10
        ax.set_ylim(*ylim)  # y軸範圍從-1到6

        if path is not None:
            if not os.path.exists(path):
                os.makedirs(path)
            if name is None:
                name = 'test'
            plt.savefig(f'''{path}/{name}.png''', dpi=300)       
             
        return fig, ax


    edges_list = {
        '南崁溪流域': {
            "edges" : [
                ("桃46新興路橋", "宏太橋"), ("宏太橋", "星見橋"), ("星見橋", "茄苳溪橋"), ("茄苳溪橋", "南崁溪橋"), 
                ("大埔橋", "舊路大橋"), ("舊路大橋", "龜山橋"), ("龜山橋", "天助橋"), ("天助橋", "大檜溪橋"), ("大檜溪橋", "南崁溪橋"),
                ("南崁溪橋", "竹圍大橋")
                ],
            "pos" : {"桃46新興路橋": [-.5, -2], "宏太橋": [-.5, 0], "星見橋": [-.5, 2], "茄苳溪橋": [-.5, 3], "南崁溪橋": [0, 5],
                "大埔橋": [3.5, 1.5], "舊路大橋": [2.5, 1], "龜山橋": [1.5, 0], "天助橋": [0.5, 1], "大檜溪橋": [0.5, 2],
                "竹圍大橋": [-1, 7]},
            'figsize': (9, 9)
        },
        '老街溪流域': {
            "edges" : [
                    ("美都麗橋", "北勢橋"), ("北勢橋", "環鄉橋(原為宋屋)"), 
                    ("平鎮第一號橋", "環鄉橋(原為宋屋)"),
                    ("環鄉橋(原為宋屋)", "公園橋上游(原為青埔橋)"), ("公園橋上游(原為青埔橋)", "中正橋"), ("中正橋", "許厝港一號橋")
                ],
            "pos" : { "美都麗橋": [1.5, -2], "北勢橋": [1.5, 0], "環鄉橋(原為宋屋)": [1.5, 1], 
                    "平鎮第一號橋": [1, 0], "公園橋上游(原為青埔橋)": [1.5, 3],
                    "中正橋": [1.5, 5], "許厝港一號橋": [1, 6], },
            'figsize': (6, 9)
        },
        '鹽水溪流域': {
            "edges" : [
                    ("新灣橋", "豐化橋"), 
                    ("同心橋", "千鳥橋"), ("千鳥橋", "豐化橋"), 
                    ("豐化橋", "永安橋"), ("永安橋", "溪頂寮大橋(原太平橋)"), ("溪頂寮大橋(原太平橋)", "鹽水溪橋"),
                ],
            "pos" : { "新灣橋": [0, 0], "豐化橋": [0, 2], "同心橋": [2, 1.5], 
                    "千鳥橋": [2, 2], 
                    "永安橋": [-1, 2], "溪頂寮大橋(原太平橋)": [-2, 1], "鹽水溪橋": [-3,1]} ,
            'figsize': (12, 4)
        },
        '二仁溪流域': {
            "edges" : [
                    ("二層橋", "古亭橋"), ("古亭橋", "崇德橋"), ("崇德橋", "南雄橋"), ("南雄橋", "石安橋"), ("石安橋", "二層行橋"), ("二層行橋", "南萣橋"),
                    ("五空橋", "永寧橋"), ("永寧橋", "南萣橋")
                ],
            "pos" : { "二層橋": [9, 0], "古亭橋": [7, -3], "崇德橋": [6, -4], "南雄橋": [5, -3], "石安橋": [4, -2], "二層行橋": [2, -1], "南萣橋": [0, 0], 
                    "五空橋": [2, 1], "永寧橋": [1, 1]},
            'figsize': (12, 4)
        },
    }

    basin_list = ['南崁溪流域', '老街溪流域', '鹽水溪流域', '二仁溪流域']
    for basin in basin_list[:]:
        fig, ax = plot_map_diagram(
            edges=edges_list[basin]['edges'], 
            pos=edges_list[basin]['pos'], 
            figsize=edges_list[basin]['figsize'],
            path=f'./images/河川水質/流域分析/{basin}', 
            name=f'{basin}空間分佈示意圖'
            )



    # monitoring_data_all = read_river_monitoring_data_ver3() #沒有座標的資料



