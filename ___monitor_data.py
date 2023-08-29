import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import os
import numpy as np
import geopandas as gpd

from RiverMonitor import read_river_monitoring_data
from RiverBasinPolyData import read_river_poly, read_river_basin
from utils.plot_utils import generate_randomcolor, save_fig

from GroundWaterData import read_GWREGION
from TaiwanCounty import read_taiwan_geojson


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.ion()

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0


run_1 = False # 二仁溪109-110.xlsx
run_2 = False # 區域性地下水水質監測資料.xlsx by行政區
run_2_1 = False # 區域性地下水水質監測資料.xlsx by地下水分區
run_2_繪製地圖 = False # 繪製地下水分區圖
run_3 = False # 水污染源許可及申報資料.csv

if run_1:

    # 二仁溪109-110.xlsx檔案不完整，重新下載分完整的檔案「河川流域監測.csv」
    # df1 = pd.read_excel('data/二仁溪109-110.xlsx')

    selectedRiver = '二仁溪'
    selectedCounty = '高雄市'

    df1 = read_river_monitoring_data()
    # 選出特定河川、縣市、鄉鎮市區的資料，township的部分還不確定該如何選擇
    df1_sub = df1[(df1.river==selectedRiver) & (df1.county==selectedCounty) & (df1.township=='-') ]


    plot_timeseries = False
    plot_Statistic = False
    plot_Heatmap = False
    plot_demo_map = True
    plot_demo_map_timeseries = False

    # region 繪製時序圖
    if plot_timeseries:
        # 在同一個 AxesSubplot 物件上對每個 'sitename' 繪製線圖
        plt.ioff()
        plt.close('all')

        itemnames = df1_sub['itemname'].unique()
        for itemname in itemnames[:]:
            # if itemname!='酸鹼值':
            #     continue
            df_tmp = df1_sub[df1_sub['itemname'] == itemname]
            df_tmp.set_index('sampledate2', inplace=True)
            df_monthly = df_tmp.groupby(['sitename', 'itemunit']).resample('MS').agg({
                'itemvalue': 'mean',
            }).reset_index()

            # 繪製時序圖
            fig, ax = plt.subplots(figsize=(14, 4))
            sitenames = df_monthly.sitename.unique()
            colors = plt.get_cmap('tab10')  # 使用 matplotlib 的 'tab10' 色彩循環
            color_dict = dict(zip(sitenames, colors.colors))  # 將 'sitename' 和顏色對應起來    
            for sitename in df_monthly['sitename'].unique():
                df_tmp2 = df_monthly[df_monthly['sitename'] == sitename]
                ax.plot_date(df_tmp2['sampledate2'], df_tmp2['itemvalue'], color=color_dict[sitename], linestyle='-', marker='o')

            # 設定 x 軸的範圍和刻度
            start_date = pd.to_datetime('2016-10-01')
            end_date = pd.to_datetime('2023-06-30')
            ax.set_xlim(start_date, end_date)

            months_major = mdates.MonthLocator(interval=3)  # 每三個月一個主要刻度
            months_minor = mdates.MonthLocator()  # 每個月一個次要刻度

            ax.xaxis.set_major_locator(months_major)
            ax.xaxis.set_minor_locator(months_minor)

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # 為主要刻度設定標籤格式

            plt.xticks(rotation=20)
            plt.grid(True)  # 添加網格線


            ax.set_ylabel(df_monthly['itemunit'].iloc[0])
            ax.set_title(f'{itemname} 時序圖')
            plt.legend(sitenames, loc='upper right')


            fig_path = 'images/河川水質/時序圖/'
            if not os.path.exists(fig_path):
                os.makedirs(fig_path)
            fig.savefig(f'{fig_path}/{itemname}.png', dpi=300)  # 存檔，並設定解析度為 300 dpi
    #endregion



    # region 繪製Violin圖
    if plot_Statistic:
        plt.ioff()
        plt.close('all')

        itemnames = df1_sub['itemname'].unique()
        for itemname in itemnames[:]:
            plt.close('all')
            print(itemname)
            # if itemname!='硒':
            # if itemname != '酸鹼值':
            #     continue
            df_tmp = df1_sub[df1_sub['itemname'] == itemname]
            df_tmp.set_index('sampledate2', inplace=True)
            df_monthly = df_tmp.groupby(['sitename', 'itemunit']).resample('MS').agg({
                'itemvalue': 'mean',
            }).reset_index()
            df_monthly['month'] = df_monthly['sampledate2'].dt.strftime('%m').astype(int)

            # 繪製圖
            # plot = 'violinplot'
            # plot = 'swarmplot'
            plot = 'pointplot'

            fig, ax = plt.subplots(figsize=(14, 4))
            sitenames = df_monthly.sitename.unique()
            colors = plt.get_cmap('tab10')  # 使用 matplotlib 的 'tab10' 色彩循環
            color_dict = dict(zip(sitenames, colors.colors))  # 將 'sitename' 和顏色對應起來
            if plot == 'violinplot':
                sns.violinplot(x='month', y='itemvalue', hue='sitename', data=df_monthly, palette=color_dict, ax=ax, dodge=True)
            elif plot == 'swarmplot':
                sns.swarmplot(x='month', y='itemvalue', hue='sitename', data=df_monthly, palette=color_dict, ax=ax, dodge=True)
            elif plot == 'pointplot':
                sns.pointplot(x='month', y='itemvalue', hue='sitename', data=df_monthly, palette=color_dict, ax=ax, dodge=0.4)
            # 確保x軸刻度為月份從1到12月，如果沒有這些完整的月份，提供完整的月份，且讓科度和點對齊
            ax.set_xticks(range(0, 12))
            ax.set_xticklabels(range(1,13))

            plt.grid(True)  # 添加網格線
            ax.set_ylabel(df_monthly['itemunit'].iloc[0])
            ax.set_title(f'{itemname} 時序圖')

            # legend，水平放置在圖的下方，並移除外框線
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5)
            # 移除legend的外框線
            ax.get_legend().get_frame().set_linewidth(0.0)
            

            # 調整axes的位置，使圖例不會被圖蓋住
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

            fig_path = f'images/河川水質/{plot}/'
            if not os.path.exists(fig_path):
                os.makedirs(fig_path)
            fig.savefig(f'{fig_path}/{itemname}.png', dpi=300)  # 存檔，並設定解析度為 300 dpi        

    # endregion  

    # region
    if plot_Heatmap:
        # 以 sitename 和 itemname 為群組，以 sampledate2 為欄位名稱，製作透視表，有值為 1，沒有值為 0
        df_pivot = df1_sub.pivot_table(index=['sitename', 'itemname'], columns='sampledate2', values='itemvalue', aggfunc='count', fill_value=0).T
        fig_path = 'images/河川水質/heatmap/'
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
        df_pivot.to_excel(f'{fig_path}/河川水質監測項目.xlsx')
    
    # endregion

    # 繪製範例圖 -> 繪製流域分佈圖
    # region
    if plot_demo_map:
        # ------- 
        # 讀取台灣地圖
        # county = read_taiwan_geojson(contains=['高雄', '臺南'])
        county = read_taiwan_geojson(contains=[])
        # ------- 

        # ------- 
        # 讀取河川流域
        
        river = read_river_poly()
        basin = read_river_basin()
        # river_save = river.where(pd.notnull(river), None)
        # river_save.to_file("data/riverpoly/riverpoly.json", driver="GeoJSON")
        # https://mapshaper.org/
        # river = read_river_poly_json()

        # ------- 
        # 讀取河川水質監測站
        df1 = read_river_monitoring_data()
        df1 = gpd.GeoDataFrame(
            df1, geometry=gpd.points_from_xy(df1.twd97lon, df1.twd97lat))        
        # df1.to_file("data/rivermonitoring/rivermonitoring.json", driver="GeoJSON")
        # 河川水質測站河川名稱修正
        # df1.river = df1.river.replace('南港溪(投)', '南港溪')
        df1.river = df1.river.replace('北港溪(雲)', '北港溪')
        df1.river = df1.river.replace('蘇澳溪', '蘇澳港')
        df1.river = df1.river.replace('二仁溪', '二仁溪(二層行溪)')
        df1.river = df1.river.replace('淡水河本流', '淡水河')
        df1.river = df1.river.replace('和平溪', '和平溪(大濁水溪)')
        df1.river = df1.river.replace('立霧溪', '立霧溪(達梓里溪)')
        df1.river = df1.river.replace('吉安溪', '吉安溪(七腳川溪)')
        df1_river = df1.river.unique()
        # ------- 

        # 找出水質測站的河川不在河川資料中的列表
        # df1_river_not_in_river = [item for item in df1_river if item not in river.RIVER_NAME.unique()]
        # ['南港溪(投)', '北港溪(雲)', '蘇澳溪', '美崙溪', '二仁溪', '淡水河本流',
        # '北港溪(投)', '和平溪', '立霧溪', '茄苳溪(竹)', '茄苳溪(桃)', '南港溪(苗)',
        # '清水溪(投)', '吉安溪', '三棧溪', '三峽河', '福興溪']





        # color_dict = generate_colordict(county.NAME_2014.unique(), trans_level=0.5, random_seed=100)
        # cmap = transparent_cmap(plt.get_cmap('tab10'), 0)
        # cmap = transparent_cmap(color_dict, 1)

        # 取出df1中獨立的sitename與對應的twd97lon、twd97lat， 並
        df1_unique_station = df1.drop_duplicates(subset=['sitename', 'twd97lon', 'twd97lat'])
        df1_unique_station.to_file("data/River_Monitor_Data/rivermonitoring/rivermonitoring.json", driver="GeoJSON")        

        # 確認 basin 中的 geometry ，是否有包含 df1_unique_station 中的任意點，如果有，則在basin中新增欄位 exist，並設為 1，否則為 0
        # df1_unique_station.apply(lambda row: 1 if basin.contains(row.geometry).any() else 0, axis=1)
        df1_unique_station = df1_unique_station.set_crs(epsg=4326)
        joined = gpd.sjoin(basin, df1_unique_station, how='inner', op='contains')
        basin['exist'] = 0
        basin.loc[joined.index, 'exist'] = 1

        # river_plot = river[river.RIVER_NAME.isin(df1_river)]
        river_plot = river
        filter_river_by_basin = False
        if filter_river_by_basin:
            # 依據找出包含水質測站的流域範圍，篩選出在此流域範圍內的河川資料
            joined2 = gpd.sjoin(river, basin[basin.exist==1], how='inner', op='intersects')
            river_plot = river.loc[joined2.index, :]

        # 繪製圖
        plot_by_basin = True
        plot_by_river = not plot_by_basin

        selectedRiver = '全國'
        if plot_by_river:
            fig_name = f'{selectedRiver}流域監測站分佈圖(依河川分區)'
        elif plot_by_basin:
            fig_name = f'{selectedRiver}流域監測站分佈圖(依流域分區)'

        plt.close('all')
        fig, ax = plt.subplots(figsize=(21, 15))
        # for 二仁溪 # ax.set_xlim([120.1, 120.5]) # ax.set_ylim([22.84, 23.02])
        ax.set_xlim([119, 122.5])
        ax.set_ylim([21.8, 25.5])

        # 繪製行政區域，不同行政區域使用不同的顏色，並設定線的粗細
        if plot_by_river:
            n = len(county)
            cmap = generate_randomcolor(n, toListedColormap=True, random_seed=200, grey=True)
            county.plot(ax=ax, column='NAME_2014', edgecolor=(.2,.2,.2), alpha=.3, legend=True, cmap=cmap)
        elif plot_by_basin:
            n = len(basin)
            cmap = generate_randomcolor(n, toListedColormap=True, random_seed=200, grey=False)
            basin[basin.exist==0].plot(
                    ax=ax, column='BASIN_NAME', edgecolor="purple", 
                    alpha=.3, color='white',
                    )
            basin[basin.exist==1].plot(
                    ax=ax, column='BASIN_NAME', edgecolor="purple", 
                    alpha=.5, legend=True, cmap=cmap,
                    legend_kwds={'loc': 'upper left', 'ncol': 1}
                    )
            # 在圖上標記每個basin的名稱，用箭頭指向basin的中心點
            for idx, row in basin[basin.exist==1].iterrows():
                ax.annotate(text=row.BASIN_NAME, xy=(row.geometry.centroid.x, row.geometry.centroid.y), xytext=(row.geometry.centroid.x, row.geometry.centroid.y), arrowprops=dict(arrowstyle="->", color='black', lw=1), ha='center', va='center', fontsize=6, color='red')


        river_plot.plot( legend=True, ax=ax, edgecolor='blue', alpha=1, linewidth=.5)

        leg = ax.get_legend()
        leg.set_bbox_to_anchor((1, 1))
        fig.subplots_adjust(left=-0.1)  # 數值越小，子圖離右邊界越近



        # df1_unique_station 的座標點繪製在圖上
        ax.scatter(df1_unique_station['twd97lon'], df1_unique_station['twd97lat'], c='red', s=4, alpha=.6, label='監測站', marker="^", linewidths=1)


        ax.set_title(fig_name)
        fig_path = 'images/河川水質/時序圖範例/'
        save_fig(fig, fig_path, fig_name, dpi=300)

    # endregion



    # region
    # 找出與特定河川距離小於特定距離的監測站
    plot_高屏溪流域 = True
    if plot_高屏溪流域:
        basin = read_river_basin()
        basin = basin[basin.BASIN_NAME == '高屏溪']
        river = read_river_poly()
        df1 = read_river_monitoring_data()
        df1 = gpd.GeoDataFrame(
            df1, geometry=gpd.points_from_xy(df1.twd97lon, df1.twd97lat))
        
        df1_unique_station = df1.drop_duplicates(subset=['sitename', 'twd97lon', 'twd97lat'])
        # 找出所有df1，有在 basin 中的點，並將df1中不存在的點移除
        df1_unique_station_sub = df1_unique_station[df1_unique_station.geometry.within(basin.geometry.iloc[0])]

        distance = 0.1
        buffered = df1_unique_station_sub.buffer(distance)
        gdf_buffered = gpd.GeoDataFrame(geometry=gpd.GeoSeries(buffered))
        result = gpd.overlay(river, gdf_buffered, how='intersection')

    # endregion

    # region
    plot_test = True
    if plot_test:
        # import rasterio
        # with rasterio.open('data/內政部20公尺網格數值地形模型資料/dem_20m.tif') as dem:
        #     elevation = dem.read(1)
        import rasterio
        from rasterio.warp import calculate_default_transform, reproject, Resampling
        from pyproj import CRS

        dst_crs = CRS.from_epsg(4326)  # 目標座標系統

        # 轉換 dem_20m.tif 的座標系統
        with rasterio.open('data/內政部20公尺網格數值地形模型資料/dem_20m.tif') as src:
            transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open('output.tif', 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

        def transformxy2h(x, y):
            with rasterio.open('data/內政部20公尺網格數值地形模型資料/dem_20m_epsg4326.tif') as dem:
                # 讀取DEM數據
                elevation = dem.read(1)

                # 轉換經緯度座標到影像座標
                row, col = dem.index(x, y)

                # 從影像中提取海拔
                altitude = elevation[row, col]
            return altitude

        def calculate_height(df):
            # 假設 df1 中的 'geometry' 欄位是點，我們可以提取出經緯度
            df['longitude'] = df['geometry'].x
            df['latitude'] = df['geometry'].y

            # 使用 `transformxy2h` 函式來計算高度
            df['height'] = df.apply(lambda row: transformxy2h(row['longitude'], row['latitude']), axis=1)

            return df
        
        import matplotlib.colors as colors

        df2_unique_station = calculate_height(df1_unique_station)
        
        clevel = list(range(0, 100, 10)) + [200, 400, 800, 1600]

        # 為了建立 colorbar，我們需要定義一個 norm 物件，並指定我們的色階區間
        cmap = plt.cm.get_cmap('viridis', len(clevel)-1) # 使用你喜歡的colormap
        norm = colors.BoundaryNorm(clevel, len(clevel)-1)

        fig, ax = plt.subplots(1, 1)

        df2_unique_station.plot(column='height', ax=ax, cmap=cmap, norm=norm)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        fig.colorbar(sm, ticks=clevel, orientation='vertical')

        plt.show()


    # endregion

    # region
    if plot_demo_map_timeseries:
        # 繪製空間分佈中個測站的時序圖
        # 計算出df1_sub中，以sitename群組，itemname不重複的數量
        df1_sub_count = df1_sub.groupby(['sitename'])['itemname'].nunique().reset_index()

        df1_sub.itemname.unique()
        # 繪製df1_sub2各sitename的時序圖
        from matplotlib.dates import DateFormatter

        
        itemname = '鉛'
        # itemname = '鋅'
        max_value = df1_sub[df1_sub['itemname'] == itemname]['itemvalue'].max()
        max_value = max_value + max_value * 0.1
        sitenames = df1_sub['sitename'].unique()
        # ------------------------------------------------------------------
        # 以下這段以後再跑的時候要想看看，之前是先篩出df1_sub的資料，再去從測站裡面挑資料
        # 下面的做法是從df1_sub挑出測站之後，再回去df1裡面挑選資料出
        # 但對結果好像沒什麼影響
        
        if True:
            df1_sub = df1[df1.sitename.isin(sitenames)]
        # ------------------------------------------------------------------
        for sitename in df1_sub['sitename'].unique()[:]:
            df_tmp = df1_sub[(df1_sub['sitename'] == sitename) & (df1_sub['itemname'] == itemname)]
            # print(sitename, df_tmp.sampledate2.dt.strftime('%Y-%m').unique())
            df_tmp.set_index('sampledate2', inplace=True)
            df_tmp = df_tmp.resample('3MS').agg({
                'itemvalue': 'mean',
                'itemunit': 'first'
            })
            new_index = pd.date_range(start='2021-01-01', end='2023-04-01', freq='3MS').rename('sampledate2')
            df_tmp = df_tmp.reindex(new_index)
            df_tmp.reset_index(inplace=True)
            # print(sitename, df_tmp.sampledate2.dt.strftime('%Y-%m').unique())
            df_tmp.sampledate2 = df_tmp.sampledate2.dt.strftime('%Y-%m')
            plt.close('all')
            fig, ax = plt.subplots(figsize=(8, 3))
            df_tmp.plot.bar(ax=ax, x='sampledate2', y='itemvalue', label=sitename)
            # df_tmp['itemvalue'].plot(ax=ax, label=sitename)
            ax.set_title(f'{selectedRiver}流域監測站時序圖 - {itemname}', fontsize=16)
            ax.tick_params(axis='x', labelrotation=20, labelsize=8)  # 調整x軸刻度的旋轉角度和字體大小
            ax.tick_params(axis='y', labelsize=8)  # 調整y軸刻度的字體大小
            ax.set_xlabel('時間')
            ax.set_ylabel(df1_sub['itemunit'].iloc[0])
            ax.set_ylim([0, max_value])

            plt.tight_layout()  # 自動調整軸的大小
            plt.grid(True)  # 添加網格線

            # 存檔
            fig_path = f'images/河川水質/時序圖範例/{itemname}_v2'
            if not os.path.exists(fig_path):
                os.makedirs(fig_path)
            fig.savefig(f'{fig_path}/{selectedRiver}流域監測站時序圖-{sitename}-{itemname}.png', dpi=300)
    # endregion







if run_2_繪製地圖:



    gdf = read_GWREGION()

    county = read_taiwan_geojson()

    # 繪製地圖
    plt.close('all')
    fig, ax = plt.subplots(figsize=(10, 8))
    # fig, ax = plt.subplots(1, 1)

    county.plot(ax=ax, color='white', edgecolor='black')
    gdf.plot(column='ZONNAME', cmap='Set1',  alpha=0.5, legend=True, ax=ax)
    leg = ax.get_legend()
    # trans = mpl.transforms.BboxTransformTo(ax.get_window_extent())
    leg.set_bbox_to_anchor((1.3, 0.5))
    ax.set_xlim([119, 122.5])
    ax.set_ylim([21.8, 25.5])

    fig_path = f'images/區域性地下水/分布圖/'
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)    
    fig.savefig(f'{fig_path}/分布圖.png', dpi=300)  # 存檔，並設定解析度為 300 dpi
if run_2:
    selectedCounty = '高雄市'   

    df2 = pd.read_csv('data/區域性地下水水質監測資料.csv')
    df2 = df2.fillna('-');
    df2['itemvalue'] = pd.to_numeric(df2['itemvalue'], errors='coerce')
    df2['sampledate2'] = pd.to_datetime(pd.to_datetime(df2['sampledate'], format='mixed').dt.strftime('%Y-%m'))
    df2 = df2.sort_values(by=['itemname', 'siteengname', 'sampledate2'])
    df2 = df2.dropna(subset=['itemvalue'])

    do_observe = False
    # 資料觀察
    if do_observe:
        ugwdistname = df2.ugwdistname.unique()



    # 選出特定行政區
    df2_sub = df2[df2['county']==selectedCounty]
    

    plot_timeseries = False
    plot_Statistic = False
    plot_heatmap = False
    # region 繪製時序圖
    if plot_timeseries:
        plt.ioff()
        plt.close('all')

        itemnames = df2_sub['itemname'].unique()
        colors = np.random.rand(len(sitenames), 3) #生成50個RGB顏色
        color_dict = dict(zip(sitenames, colors))  # 將 'sitename' 和顏色對應起來        
        for itemname in itemnames[:]:
            # if itemname!='總鹼度':
            #     continue
            df_tmp = df2_sub[df2_sub['itemname'] == itemname]
            # 確認 單位 是否一致，不一致會記錄在圖上，並且只取第一個單位
            itemunits = df_tmp['itemunit'].unique()
            if len(itemunits) > 1:
                df_tmp['itemunit'] = df_tmp['itemunit'].iloc[0]

            # 計算不重複的月份，紀錄在圖表上
            unique_month = df_tmp.sampledate2.dt.month.unique()
            unique_month.sort()

            df_tmp.set_index('sampledate2', inplace=True)
            df_monthly = df_tmp.groupby(['sitename', 'itemunit']).resample('MS').agg({
                'itemvalue': 'mean',
            }).reset_index()

            # 繪製時序圖
            fig, ax = plt.subplots(figsize=(14, 6))
            sitenames = df_monthly.sitename.unique()

            for sitename in sitenames[:]:
                df_tmp2 = df_monthly[df_monthly['sitename'] == sitename]
                ax.plot_date(df_tmp2['sampledate2'], df_tmp2['itemvalue'], color=color_dict[sitename], linestyle='-', marker='o')

            # 設定 x 軸的範圍和刻度
            start_date = pd.to_datetime('2013-10-01')
            end_date = pd.to_datetime('2023-06-30')
            ax.set_xlim(start_date, end_date)

            months_major = mdates.MonthLocator(interval=6)  # 每三個月一個主要刻度
            months_minor = mdates.MonthLocator()  # 每個月一個次要刻度

            ax.xaxis.set_major_locator(months_major)
            ax.xaxis.set_minor_locator(months_minor)

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # 為主要刻度設定標籤格式

            plt.xticks(rotation=20)
            plt.grid(True)  # 添加網格線

            ax.set_ylabel(df_monthly['itemunit'].iloc[0])
            comment = f'''（註：此測項的所有監測月分包含 {','.join(map(str,unique_month))} 月）'''
            if len(itemunits) > 1 :
                comment += f'''\n（註：此測項的單位有 {','.join(map(str,itemunits))}）'''
            ax.set_title(f'{itemname} 時序圖\n{comment}')


            # plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5)
            # plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15))
            # plt.legend()
            plt.legend(sitenames, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5)

            ax.get_legend().get_frame().set_linewidth(0.0)
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 + box.height * 0.5, box.width, box.height * 0.5])


            fig_path = f'images/區域性地下水/{selectedCounty}/時序圖/'
            if not os.path.exists(fig_path):
                os.makedirs(fig_path)
            fig.savefig(f'{fig_path}/{itemname}.png', dpi=300)  # 存檔，並設定解析度為 300 dpi
    # endregion

    # region
    # 以 sitename 和 itemname 為群組，以 sampledate2 為欄位名稱，製作透視表，有值為 1，沒有值為 0
    if plot_heatmap:
        df_pivot = df2_sub.pivot_table(index=['sitename', 'itemname'], columns='sampledate2', values='itemvalue', aggfunc='count', fill_value=0).T
        fig_path = f'images/區域性地下水/{selectedCounty}/heatmap/'
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
        df_pivot.to_excel(f'{fig_path}/河川水質監測項目.xlsx')    
    # endregion
    
    # region
    if plot_Statistic:
        # 以季為單位，重新統計
        itemnames = df2_sub['itemname'].unique()
        colors = np.random.rand(len(sitenames), 3) #生成50個RGB顏色
        color_dict = dict(zip(sitenames, colors))  # 將 'sitename' 和顏色對應起來        
        for itemname in itemnames[:]:
            # if itemname!='總鹼度':
            #     continue
            df_tmp = df2_sub[df2_sub['itemname'] == itemname]
            # 確認 單位 是否一致，不一致會記錄在圖上，並且只取第一個單位
            itemunits = df_tmp['itemunit'].unique()
            if len(itemunits) > 1:
                df_tmp.loc[:, 'itemunit'] = df_tmp['itemunit'].iloc[0]

            # 計算不重複的月份，紀錄在圖表上
            unique_month = df_tmp.sampledate2.dt.month.unique()
            unique_month.sort()

            df_tmp.set_index('sampledate2', inplace=True)
            df_monthly = df_tmp.groupby(['sitename', 'itemunit']).resample('3MS').agg({
                'itemvalue': 'mean',
            }).reset_index()
            df_monthly['month'] = df_monthly['sampledate2'].dt.strftime('%m').astype(int)

            # 繪製圖
            # plot = 'violinplot'
            plot = 'swarmplot'
            plot = 'pointplot'

            fig, ax = plt.subplots(figsize=(14, 6))
            if plot == 'violinplot':
                sns.violinplot(x='month', y='itemvalue', hue='sitename', data=df_monthly, palette=color_dict, ax=ax, dodge=True)
            elif plot == 'swarmplot':
                sns.swarmplot(x='month', y='itemvalue', hue='sitename', data=df_monthly, palette=color_dict, ax=ax, dodge=True)
            elif plot == 'pointplot':
                sns.pointplot(x='month', y='itemvalue', hue='sitename', data=df_monthly, palette=color_dict, ax=ax, dodge=0.4)
            # 確保x軸刻度為月份從1到12月，如果沒有這些完整的月份，提供完整的月份，且讓科度和點對齊
            ax.set_xticks(range(0, 4))
            ax.set_xticklabels(range(1,13,3))

            plt.grid(True)  # 添加網格線
            ax.set_ylabel(df_monthly['itemunit'].iloc[0])
            ax.set_title(f'{itemname} 年週期')

            # legend，水平放置在圖的下方，並移除外框線
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5)
            # 移除legend的外框線
            ax.get_legend().get_frame().set_linewidth(0.0)
            

            # 調整axes的位置，使圖例不會被圖蓋住
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 + box.height * 0.5, box.width, box.height * 0.5])

            fig_path = f'images/區域性地下水/{selectedCounty}/{plot}/'
            if not os.path.exists(fig_path):
                os.makedirs(fig_path)
            fig.savefig(f'{fig_path}/{itemname}.png', dpi=300)  # 存檔，並設定解析度為 300 dpi        
    # endregion

if run_2_1:
    df2 = pd.read_csv('data/區域性地下水水質監測資料.csv')
    df2 = df2.fillna('-');
    df2['itemvalue'] = pd.to_numeric(df2['itemvalue'], errors='coerce')
    df2['sampledate2'] = pd.to_datetime(pd.to_datetime(df2['sampledate'], format='mixed').dt.strftime('%Y-%m'))
    df2 = df2.sort_values(by=['itemname', 'siteengname', 'sampledate2'])
    df2 = df2.dropna(subset=['itemvalue'])


    def q1(x):
        return x.quantile(0.25)

    def q2(x):
        return x.quantile(0.5)

    def q3(x):
        return x.quantile(0.75)
    # 依據 ugwdistname、itemengname群組，計算每個群組的平均值、標準差、最大值、最小值、總數量、不重複的sitename數量
    df2_sub = df2.groupby(['itemname', 'ugwdistname']).agg({
        'itemvalue': ['mean', 'std', 'max', 'min', 'count'],
        'sitename': ['nunique'],
    }).reset_index()
    df2_sub.columns = ['itemname', 'ugwdistname', 'mean', 'std', 'max', 'min', 'count', 'sitename_nunique']

    # 依據 ugwdistname、itemengname、sampledate的年月 群組，計算每個群組的中位數、平均值、標準差、最大值、最小值、總數量、不重複的sitename數量
    df2_sub2 = df2.groupby(['itemname', 'ugwdistname', 'sampledate2']).agg({
        'itemvalue': ['mean', 'std', 'max', 'min', 'count', q1, 'median', q3],
        'sitename': ['nunique'],
    }).reset_index()
    df2_sub2.columns = ['itemname', 'ugwdistname', 'sampledate2', 'mean', 'std', 'max', 'min', 'count', 'q1', 'q2', 'q3' ,'sitename_nunique']

    fig_path = f'images/區域性地下水/統計資料/'
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)
    df2_sub2.to_excel(f'{fig_path}/統計.xlsx') 

    # 使用plotly繪製df2_sub2，x軸為sampledate2，y軸為itemvalue，顏色為ugwdistname，圖例為itemname
    import plotly.express as px
    fig = px.scatter(df2_sub2, x="sampledate2", y="mean", color="ugwdistname", facet_col="itemname")








if run_3:
    df3 = pd.read_csv('data/水污染源許可及申報資料.csv')
    df3.columns = df3.columns.map(lambda x: x.strip('"')).map(lambda x: x.strip())