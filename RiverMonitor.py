import geopandas as gpd
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as mpatches
from utils.plot_utils import generate_colordict
import matplotlib.dates as mdates
from utils.plot_utils import generate_randomcolor
from functools import partial
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf

from utils.sql import connPostgreSQL
from sqlalchemy import text
import copy
import os

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0


def read_river_monitoring_data():
    df1 = pd.read_csv('data/River_Monitor_Data/opendata/河川流域監測.csv')

    # 資料前處理
    df1.columns = df1.columns.map(lambda x: x.strip('"')).map(lambda x: x.strip())
    df1 = df1.fillna('-');
    df1['itemvalue'] = pd.to_numeric(df1['itemvalue'], errors='coerce')
    df1['sampledate2'] = pd.to_datetime(pd.to_datetime(df1['sampledate'], format='mixed').dt.strftime('%Y-%m'))
    df1 = df1.sort_values(by=['itemname', 'siteengname', 'sampledate2'])
    df1 = df1.dropna(subset=['itemvalue'])

    geo_df1 = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1['twd97lon'], df1['twd97lat']))

    return geo_df1

def read_river_monitoring_data_update():
    def process_itemvalue(i):
        if type(i) == str:
            if ('<' in i) or ('&lt;' in i):
                return float(i.replace('&lt;', '').replace('<',''))/2
        return float(i)    

    def process_mdl(i):
        if type(i) == str:
            if ('<' in i) or ('&lt;' in i):
                return 'mdl'
        return '-'
        
    # 這比 河川流域監測.csv 資料完整
    df1 = pd.read_csv('data/River_Monitor_Data/opendata/河川流域監測_update.csv')

    # 資料前處理
    df1.itemvalue = df1.itemvalue.replace('-', np.nan)
    df1['comment']  = df1.itemvalue.apply(process_mdl)
    df1.itemvalue = df1.itemvalue.apply(process_itemvalue)
    df1 = df1.fillna('-')

    # df1['itemvalue'] = pd.to_numeric(df1['itemvalue'], errors='coerce')
    df1['sampledate2'] = pd.to_datetime(pd.to_datetime(df1['sampledate'], format='mixed').dt.strftime('%Y-%m'))
    df1 = df1.sort_values(by=['itemname', 'siteengname', 'sampledate2'])
    df1 = df1.dropna(subset=['itemvalue'])

    geo_df1 = gpd.GeoDataFrame(df1, geometry=gpd.points_from_xy(df1['twd97lon'], df1['twd97lat']))

    return geo_df1


def read_river_monitoring_data_ver2():
    '''
    這筆資料也不完整，時間比較少，但是小於MDL的有標註
    不使用
    '''
    fn = 'data/River_Monitor_Data/1120609水質監測資料整理_提供育蕙.xlsx'
    df = pd.read_excel(fn, sheet_name='河川水質監測資料')
    tmp_zn = df[(df['河川名稱'].str.contains('二仁溪')) & (df['項目名稱'].str.contains('鋅')) & (df['測站名稱'].str.contains('二層橋')) ]
    tmp_pb = df[(df['河川名稱'].str.contains('二仁溪')) & (df['項目名稱'].str.contains('鉛')) & (df['測站名稱'].str.contains('二層橋')) ]

def merge_river_monitoring_history_data():
    pth = 'data/River_Monitor_Data/history'
    fns = os.listdir(pth)
    data = []
    # 將多個ODS讀出，並整合出一個CSV
    for fn in fns:
        if fn.endswith('.ods'):
            df = pd.read_excel(f'{pth}/{fn}', skiprows=6, header=[0,1])
            data.append(df)
    df = pd.concat(data)
    df.to_csv('data/River_Monitor_Data/history/水質監測歷史數據報表_河川_1994-2022.csv', index=False)

def read_river_monitoring_data_ver3(col_name=['鎘', '鋅', '鉛', '導電度', '水溫', '酸鹼值'],read_from_ods=False, time_between=None):
    '''
    從歷史數據來的，格式不同，也沒有座標
    ＃＃＃＃＃＃ 單位有問題 -> 已修正 2023/8/2，但是是條列式，如果有其他側向要另外新增
    '''
    read_from_ods = False
    if read_from_ods:
        # 因為ODS很慢，所以轉成csv改用csv
        fn = 'data/River_Monitor_Data/history/水質監測歷史數據報表_河川_2018_2022_20230717161826.ods'
        # fn = 'data/River_Monitor_Data/水質監測歷史數據報表_河川_2019_2022_20230715053603.ods'
        df = pd.read_excel(fn, skiprows=6, header=[0,1])
        # df.to_csv('data/River_Monitor_Data/水質監測歷史數據報表_河川_2018_2022_20230717161826.csv', index=False)
    else:
        fn = 'data/River_Monitor_Data/水質監測歷史數據報表_河川_1994-2022.csv'
        df = pd.read_csv(fn, header=[0,1])

    df = df.replace('--', np.nan)
    df = df.droplevel(1, axis=1)
    df = df.dropna(how='all')
    column_namemap = {
        '採樣分區': 'basin',
        '採樣日期': 'sampledate2',
        '河川': 'river',
        '測站名稱': 'sitename',
        '縣市': 'county'
    }
    sel_columns = list(column_namemap.keys()) + col_name
    df2 = df[sel_columns].rename(column_namemap, axis=1)
    df_long = df2.melt(id_vars=['basin', 'sampledate2', 'river', 'sitename', 'county'], 
                  value_vars=col_name, 
                  var_name='itemname', 
                  value_name='itemvalue')
    mdl = df_long[['itemname', 'itemvalue']].dropna()
    mdl = mdl[mdl.itemvalue.astype(str).str.contains('<')].drop_duplicates(subset='itemname')
    def process_itemvalue(i):
        if type(i) == str:
            if '<' in i:
                return float(i.replace('<', ''))/2
        return float(i)

    df_long.itemvalue = df_long.itemvalue.apply(process_itemvalue)
    df_long = df_long.assign(itemunit='') # 單位有些會有問題 已修正 2023/8/2，但是是條列式，如果有其他側向要另外新增
    df_long.loc[df_long.itemname == '導電度', 'itemunit'] = 'μmho/cm25°C'
    df_long.loc[df_long.itemname == '酸鹼值', 'itemunit'] = 'pH'
    df_long.loc[df_long.itemname == '水溫', 'itemunit'] = '℃'
    df_long.sampledate2 = pd.to_datetime(df_long.sampledate2)

    if time_between is not None:
        df_long = df_long[(df_long.sampledate2.dt.year >= time_between[0]) & (df_long.sampledate2.dt.year <= time_between[1])]
    return df_long.sort_values(by=['itemname', 'sitename', 'sampledate2'])

def process_data(data, unit, year_limit):
    year0, year1 = year_limit
    if data.sampledate2.min().month != 1:
        append_firstmon = copy.deepcopy(data.iloc[[0]])
        time = f'{data.sampledate2.min().year}-01-{data.sampledate2.min().day}'
        append_firstmon.sampledate2 = pd.to_datetime(time)
        append_firstmon.itemvalue = None
        data = pd.concat([append_firstmon, data])

    # print(data)            
    # print(sitename, df_tmp.sampledate2.dt.strftime('%Y-%m').unique())
    data.set_index('sampledate2', inplace=True)
    # print(data.itemname.iloc[0])
    # print(data)
    if data.itemname.iloc[0] in ['導電度', '水溫', '酸鹼值']:
        time_freq = 'MS'
    else:
        time_freq = '3MS'
    data = data.resample(time_freq).agg({
        'itemvalue': 'mean',
        'itemunit': 'first'
    })
    # print(data)
    new_index = pd.date_range(start=f'{year0}-01-01', end=f'{year1}-12-01', freq=time_freq).rename('sampledate2')
    data = data.reindex(new_index)
    data.reset_index(inplace=True)
    data.itemunit = data.itemunit.fillna(unit)
    # data.sampledate2 = data.sampledate2.dt.strftime('%Y-%m')
    # data['sampledate2'] = data['sampledate2'].apply(lambda x: f"{x.year - 1911}-{x.strftime('%m')}")
    return data


def plot_timeSeries(
        data, 
        chem, 
        basin,
        path=None, 
        FigName_prefix='',
        write_plot_data=False,
        write_plot_data_path=None,
        special_case_ylim=True,
        append_data=None,
        year_limit=(1994, 2022),
        plot_in_one_fig=False,
        ):
    


    def write_plot_data(data, sitename, chem, write_plot_data_path):
        if write_plot_data:
            if write_plot_data_path is not None:
                if os.path.exists(write_plot_data_path) == False:
                    os.makedirs(write_plot_data_path)
                data.to_excel(f'{write_plot_data_path}/{sitename}_{chem}.xlsx', index=False)

    if len(data) == 0:
        return
    year0, year1 = year_limit
    data2 = copy.deepcopy(data)
    data2 = data2.sort_values(by=['sampledate2'])
    max_value = data[(data.itemname == chem) & (data.sampledate2.dt.year>=year0) & (data.sampledate2.dt.year<=year1)].itemvalue.max()
    max_value = max_value + max_value * 0.1
    if special_case_ylim:
        if chem == '鉛':
            max_value = 0.01
        elif chem == '鋅':
            max_value = 0.5
    unit = data[data.itemname == chem].itemunit.iloc[0]

    if plot_in_one_fig:
        plt.close('all')
        fig, ax = plt.subplots(figsize=(8, 2.5))


    colors = generate_randomcolor(20)
    for ii, sitename in enumerate(data2['sitename'].unique()[:]):
        data3 = data2[data2.sitename == sitename]
        data3 = process_data(data3, unit, year_limit=year_limit)

        write_plot_data(data3, sitename, chem, write_plot_data_path)
        

        data3['sampledate_label'] = data3['sampledate2'].apply(lambda x: f"{x.year-1911}-{x.month:02d}")
        
        # 繪圖
        if not plot_in_one_fig:
            plt.close('all')
            fig, ax = plt.subplots(figsize=(8, 3))
            data3.plot.bar(ax=ax, x='sampledate2', y='itemvalue', label=sitename, color=(0.145, 0.145, 0.145, 0.9))
            # ax.bar(data3['sampledate2'], data3['itemvalue'], width=10)
            ax.get_legend().remove()

            for i, v in enumerate(data3['itemvalue']):
                if v > max_value:
                    # 標注文字，並給定背景顏色白色
                    ax.text(i, max_value*0.93, str(v), ha='center', va='top', color='red', fontsize=12, bbox=dict(facecolor='white', edgecolor='None', alpha=0.8))
                    # ax.annotate(f'{max_value}', 
                    #             xy=(i, max_value),  # 這是箭頭指向的座標。
                    #             xytext=(i-i*0.001, max_value-max_value*0.001),  # 這是文字的座標。
                    #             arrowprops=dict(facecolor='white', shrink=0.05)) 
                # else:
                #     ax.text(i, v, str(v), ha='center', va='bottom')

            ax.set_title(f'''{basin.replace('流域','')} {sitename.split('(')[0]}-{chem}時序圖''', fontsize=16)
            ax.tick_params(axis='x', labelrotation=40, labelsize=8)  # 調整x軸刻度的旋轉角度和字體大小
            ax.tick_params(axis='y', labelsize=12)  # 調整y軸刻度的字體大小
            ax.set_xticklabels(data3['sampledate_label'], rotation=20, fontsize=8)            
            ax.set_ylim([0, max_value])
            ax.set_ylabel(data3['itemunit'].iloc[0])

        else:
            data3.plot(ax=ax, x='sampledate2', y='itemvalue', label=sitename.split('(')[0], color=colors[ii], linewidth=.5, marker='o', markersize=1)
            # 將 legend 分成兩欄，並且放在ax外部下方
            if basin == '二仁溪流域':
                ax.legend(ncol=5, bbox_to_anchor=(0.5, -0.2), loc='upper center', fontsize=12, frameon=False)
            elif basin == '老街溪流域':
                ax.legend(ncol=4, bbox_to_anchor=(0.5, -0.2), loc='upper center', fontsize=12, frameon=False)
            ax.set_title(f'''{basin.replace('流域','')}-{chem}時序圖''', fontsize=16)
            if chem == '水溫':
                ax.set_ylim([15, 36])
                # ax.set_yticks(np.arange(6, max_value+1, 1))
                ax.set_ylabel('°C')
            elif chem == '酸鹼值':
                ax.set_ylim([6, max_value])
                ax.set_yticks(np.arange(6, max_value+1, 1))
                ax.yaxis.set_minor_locator(plt.NullLocator())
                ax.set_ylabel('pH')
                # ax.axhline(y=9, color=(.97, 0, 0, .9), linestyle='-', linewidth=.1)
                xlim = (year0-1970)*12, (year1-1970+1)*12-1
                ax.set_xlim(*xlim)
                xlim = ax.get_xlim()
            elif chem == '導電度':
                ax.set_ylim([0, max_value])
                # ax.set_yticks(np.arange(6, max_value+1, 1))
                ax.set_ylabel('μmho/cm25°C')



        ax.set_xlabel('')
        
        

        # ax.xaxis.set_major_locator(mdates.YearLocator(5))  # 3 years
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        # ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))  # 3 months



        #   ------------------------------------------------------------------------------------------------
        # 不要用，畫出來很可怕
        if append_data:

            ax_pos = ax.get_position()


            lines = list(append_data.values())
            labels = list(append_data.keys())
            colors = list(generate_colordict(labels).values())

            # for line_data, color, label in zip(lines, colors, labels):
            #     line_data_2 = line_data[line_data.sitename == sitename]
            #     line_data_2 = process_data(line_data_2, unit='')                
            #     line_data_2.plot(ax=ax, x='sampledate2', y='itemvalue', color=color, label=label)
                
            #     # 在每個點上標記數值
            #     for i, (x, y) in enumerate(zip(line_data_2['sampledate2'], line_data_2['itemvalue'])):
            #         ax.text(x, y, str(y), color=color, fontsize=8)  # 調整字體大小為需要的大小
            for idx, (line_data, color, label) in enumerate(zip(lines, colors, labels)):
                line_data_2 = line_data[line_data.sitename == sitename]
                line_data_2 = process_data(line_data_2, unit='')                

                ax2 = fig.add_axes(ax_pos)
                line_data_2.plot(ax=ax2, x='sampledate2', y='itemvalue', color=color, label=label)

                # 移除所有边框、坐标轴和刻度
                ax2.axis('off')
        #   ------------------------------------------------------------------------------------------------                


        # 繪製 minor tick
        major_ticks = ax.yaxis.get_major_ticks()
        # return ax
        major_tick_spacing = major_ticks[1].get_loc() - major_ticks[0].get_loc()
        if major_tick_spacing > 0:
            ax.yaxis.set_minor_locator(MultipleLocator(major_tick_spacing/5))  # 你需要根據你的主要刻度間距來調整這個值



        mdl_text = {'鉛': '--- MDL', '鎘': '--- MDL'}

        if chem == '鉛':
            ax.axhline(0.003, color='red', linestyle='dashed', linewidth='1')
        elif chem == '鎘':
            ax.axhline(0.001, color='red', linestyle='dashed', linewidth='1')


        if chem in mdl_text.keys():
            size_dict = {'small': 8, 'medium': 10, 'large': 12, 'x-large': 16, 'xx-large': 20}
            title_font_size = size_dict[plt.rcParams['axes.titlesize']]
            ax.text(1.0, 1.0, mdl_text[chem], transform=ax.transAxes, va='bottom', ha='right', fontsize=title_font_size*1, color='red')


        plt.tight_layout()  # 自動調整軸的大小
        ax.grid(True, linewidth=0.5, color='gray')


        # 添加次要的網格線
        ax.minorticks_on()
        ax.yaxis.grid(True, which='minor', linestyle=':', linewidth='0.5', color='gray')


        # 存檔
        if not plot_in_one_fig:
            if path is not None:
                if not os.path.exists(path):
                    os.makedirs(path)
                name = f'{sitename}'
                fullname = f'''{path}/{name}{FigName_prefix}.png'''
                print(fullname)
                plt.savefig(fullname, dpi=300)       

    if plot_in_one_fig:
        if path is not None:
            if not os.path.exists(path):
                os.makedirs(path)
            name = f'{basin}'
            fullname = f'''{path}/{name}{FigName_prefix}.png'''
            print(fullname)
            plt.savefig(fullname, dpi=300)      


def plot_river_time_series():
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.ion()

    # chems = ['鉛', '鎘', '鋅']
    chems = ['導電度', '水溫', '酸鹼值']
    # chems = ['酸鹼值']
    basin_list = ['老街溪流域', '二仁溪流域']
    # basin_list = ['南崁溪流域', '老街溪流域', '鹽水溪流域', '二仁溪流域']

    data_source = 'history_data'
    if data_source == 'open_data':
        monitoring_data_all = read_river_monitoring_data() #沒有座標的資料
    elif data_source == 'history_data':
        monitoring_data_all = read_river_monitoring_data_ver3() #沒有座標的資料

    print('plotting')
    for chem in chems[:]:
        for basin in basin_list[:]:
            print(basin, chem)
            data = monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname==chem)]
            append_data = {
                '導電度': monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname=='導電度')],
                '水溫': monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname=='水溫')],
                '酸鹼值': monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname=='酸鹼值')],
            }
            a = plot_timeSeries(
                data=data,
                # append_data=append_data, # 畫完效果非常可怕，不要用
                chem=chem,
                basin=basin,
                path=f'./images/河川水質/流域分析/{data_source}/{basin}/{chem}', 
                FigName_prefix='_v3_update_MDL_and_mark_out_of_limit',
                write_plot_data=False,
                write_plot_data_path=f'./data/Result_data/River_Monitor_Data/{data_source}/{basin}/{chem}',
                special_case_ylim=True,
                year_limit=(2018, 2022),
                plot_in_one_fig=True
            )


def correlation_matrix(path='images/河川水質/流域分析/河川各測站相關性分析', ignore_MDL=False):
    chems = ['鉛', '鋅']
    # chems = ['鉛']
    # chems = ['導電度', '水溫', '酸鹼值']
    time_between = [2018, 2022]
    # basin_list = ['南崁溪流域', '老街溪流域', '鹽水溪流域', '二仁溪流域']  
    basin_list = ['老街溪流域', '二仁溪流域']  
    monitoring_data_all = read_river_monitoring_data_ver3(time_between=time_between) #沒有座標的資料
    for basin in basin_list[:]:
        for chem in chems[:]:
            data = monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname==chem)]
            df_pivot = data.pivot(index='sampledate2', columns='sitename', values='itemvalue')
            df_pivot = df_pivot.dropna(how='all')
            # 移除 () 內的字
            df_pivot.columns = df_pivot.columns.str.replace(r"\(.*\)","", regex=True)
            if ignore_MDL:
                if chem == '鉛':
                    df_pivot[df_pivot<0.003] = np.nan
            correlation_matrix = df_pivot.corr()

            
            # 存檔
            if path is not None:
                if not os.path.exists(path):
                    os.makedirs(path)
                name = f'{basin}_{chem}'    
                if ignore_MDL:
                    fullname = f'''{path}/{'-'.join(map(str,time_between))}_{name}_忽略MDL.xlsx'''
                else:
                    fullname = f'''{path}/{'-'.join(map(str,time_between))}_{name}.xlsx'''
                correlation_matrix.to_excel(fullname, index=True)

# correlation_matrix(path='images/河川水質/流域分析/河川各測站相關性分析')

def calculate_statistic_table():
    '''
    建立報告上需要的統計表
    '''
    time_between = [2018, 2022]
    monitoring_data_all = read_river_monitoring_data_ver3(time_between=time_between) #沒有座標的資料
    monitoring_data_all = monitoring_data_all[monitoring_data_all.basin.isin(['老街溪流域', '二仁溪流域'])]
    monitoring_data_all = monitoring_data_all[monitoring_data_all.itemname.isin(['鉛', '鋅', '導電度', '水溫', '酸鹼值'])]
    # 依據 basin sitename itemname 群組，計算 itemvalue 的平均值 最大值 最小值
    statistic_table = monitoring_data_all.groupby(['basin', 'sitename', 'itemname']).agg({'itemvalue': ['mean', 'max', 'min']})
    
    # 將 itemvalue，水溫、酸鹼值 精確到小數下一位， 導電度到個位數字， 鉛和鋅到小數下三位， 
    def round_down(x, n):
        itemname = list(x['itemname'])[0]
        # print(x['itemvalue'])
        itemvalue = x['itemvalue']
        if itemname in ['水溫', '酸鹼值']:
            return itemvalue.apply(lambda x: f'{round(x, 1):.1f}')
            # return f'{round(itemvalue, 1):.1f}'
        elif itemname in ['導電度']:
            return itemvalue.apply(lambda x: f'{round(x, 0):.0f}')
            # return f'{round(itemvalue, 0):.0f}'
        elif itemname in ['鉛', '鋅']:
            if itemname == '鉛':
                itemvalue['min'] = '<0.003'
                itemvalue['max'] = f'''{round(itemvalue['max'], 3):.3f}'''
                itemvalue['mean'] = f'''{round(itemvalue['mean'], 3):.3f}'''

                return itemvalue
            else:
                return itemvalue.apply(lambda x: f'{round(x, 3):.3f}')
        
            # return f'{round(itemvalue, 3):.3f}'
    statistic_table = statistic_table.reset_index()
    statistic_table['itemvalue'] = statistic_table.apply(round_down, n=3, axis=1)
    statistic_table.set_index(['basin', 'sitename', 'itemname'], inplace=True)
    statistic_table.columns = ['mean', 'max', 'min']
    # 重新整理，變成單一欄位，欄位內容格式為 mean ( min - max )
    statistic_table = statistic_table.apply(lambda x: f'{x["mean"]} ({x["min"]} - {x["max"]})', axis=1).rename('itemvalue').to_frame()

    # 將 itemname 轉成欄位
    statistic_table = statistic_table.reset_index().pivot(index=['basin', 'sitename'], columns='itemname', values='itemvalue')
    statistic_table = statistic_table[['水溫', '酸鹼值', '導電度', '鉛', '鋅']].rename({
        '水溫': '水溫 (℃)',
        '酸鹼值': '酸鹼值',
        '導電度': '導電度 (μmho/cm25℃	)',
        '鉛': '鉛 (mg/L)*',
        '鋅': '鋅 (mg/L)',
    }, axis=1)
    order = ['南萣橋', '永寧橋', '五空橋', '網寮橋(原為建國村)', '二層行橋', '石安橋', '南雄橋', '崇德橋', '古亭橋', '二層橋'] + ['許厝港一號橋', '中正橋', '公園橋上游(原為青埔橋)', '環鄉橋(原為宋屋)', '北勢橋', '美都麗橋', '平鎮第一號橋']
    statistic_table = statistic_table.reindex(order, level=1)
    statistic_table.to_excel('./data/Result_data/River_Monitor_Data/河川各測站統計表.xlsx', index=True)
    

def statistic_year():
    time_between = [2018, 2022]
    monitoring_data_all = read_river_monitoring_data_ver3(time_between=time_between) #沒有座標的資料
    monitoring_data_all = monitoring_data_all[monitoring_data_all.basin.isin(['老街溪流域', '二仁溪流域'])]
    monitoring_data_all = monitoring_data_all[monitoring_data_all.itemname.isin(['鉛', '鋅', '導電度', '水溫', '酸鹼值'])]    
    monitoring_data_all['year'] = monitoring_data_all.sampledate2.dt.strftime('%Y')
    statistic_table = monitoring_data_all.groupby(['basin', 'sitename', 'itemname', 'year']).agg({'itemvalue': ['mean', 'max', 'min']})
    # statistic_table.to_excel('./data/Result_data/River_Monitor_Data/河川各測站統計表_年.xlsx', index=True)

    # 依據itemname 分成不同的 dataframe，column 為年份，row 為 basin sitename
    statistic_table.columns = ['_'.join(col) for col in statistic_table.columns]
    statistic_table2 = statistic_table.reset_index()
    for itemname in statistic_table2.itemname.unique():
        data = statistic_table2[statistic_table2.itemname == itemname]
        data = data.pivot(index=['basin', 'sitename'], columns='year', values=['itemvalue_mean', 'itemvalue_max', 'itemvalue_min'])
        # 將 itemvalue_mean itemvalue_max itemvalue_min 依據年份 轉成 itemname_mean(itemname_max-itemname_min)
        def process(row, itemname):
            row = row.to_frame().T.stack(level=1)
            if itemname in ['導電度', '水溫', '酸鹼值']:
                row = row.apply(lambda x: f'{x["itemvalue_mean"]:.1f} ({x["itemvalue_min"]:.1f} - {x["itemvalue_max"]:.1f})', axis=1)
            else:
                row = row.apply(lambda x: f'{x["itemvalue_mean"]:.4f} ({x["itemvalue_min"]:.4f} - {x["itemvalue_max"]:.4f})', axis=1)
            
            name = row.index.get_level_values(0)[:2]
            row = row.droplevel([0,1])
            return row
        data2 = data.apply(lambda row: process(row, itemname) , axis=1)#.rename(itemname).to_frame()

        data2.rename_axis(index=['', ''], inplace=True)
        order = ['南萣橋', '永寧橋', '五空橋', '網寮橋(原為建國村)', '二層行橋', '石安橋', '南雄橋', '崇德橋', '古亭橋', '二層橋'] + ['許厝港一號橋', '中正橋', '公園橋上游(原為青埔橋)', '環鄉橋(原為宋屋)', '北勢橋', '美都麗橋', '平鎮第一號橋']
        data2 = data2.reindex(order, level=1)
        # 新增axis=1的 level=0到index為itemname
        data2.columns = pd.MultiIndex.from_product([[itemname + '平均值(最小值-最大值)'], data2.columns])
        data2.to_excel(f'./data/Result_data/River_Monitor_Data/河川各測站統計表_年_{itemname}.xlsx', index=True)

def autocorrelation():
    time_between = [2018, 2022]
    monitoring_data_all = read_river_monitoring_data_ver3(time_between=time_between) #沒有座標的資料
    monitoring_data_all = monitoring_data_all[monitoring_data_all.basin.isin(['老街溪流域', '二仁溪流域'])]
    monitoring_data_all = monitoring_data_all[monitoring_data_all.itemname.isin(['鉛', '鋅', '導電度', '水溫', '酸鹼值'])]    

    year0 = time_between[0]
    year1 = time_between[1]
    for sitename in monitoring_data_all.sitename.unique()[:]:
        # 繪製subplot 3*2
        basin = monitoring_data_all[monitoring_data_all.sitename==sitename].basin.iloc[0]
        plt.ioff()
        plt.close('all')
        fig, axes = plt.subplots(3, 2, figsize=(12, 6))
        fig.suptitle(f'''{basin} {sitename.split('(')[0]} 自相關圖''', fontsize=22)
        axes = axes.flatten()
        # 移除沒有圖的subplot
        for i, itemname in enumerate(['水溫', '鉛', '酸鹼值', '鋅', '導電度']):
        # for i, itemname in enumerate(monitoring_data_all.itemname.unique()):
            data = monitoring_data_all[(monitoring_data_all.itemname == itemname) & (monitoring_data_all.sitename == sitename)].dropna(subset=['itemvalue'])    
            if itemname in ['導電度', '水溫', '酸鹼值']:
                time_freq = 'MS'
            else:
                time_freq = '3MS'
            data.set_index('sampledate2', inplace=True)
            data = data.resample(time_freq).agg({
                'itemvalue': 'mean',
                'itemunit': 'first'
            })
            new_index = pd.date_range(start=f'{year0}-01-01', end=f'{year1}-12-01', freq=time_freq).rename('sampledate2')
            
            data2 = data.reindex(new_index)

            lag_time_max = (12 if itemname in ['導電度', '水溫', '酸鹼值'] else 4 )*(3)
            x_interval = 6
            # x_interval = (6 if itemname in ['導電度', '水溫', '酸鹼值'] else 2 )

            method = 2
            if method == 1:
                # Create a time series
                x = data2.itemvalue.values
                # autocorr, confint = acf(x, nlags=lag_time_max, alpha=0.05, fft=True)            
                #繪製自相關係數圖與信賴區間
                plt.close('all')
                fig, ax = plt.subplots(figsize=(8, 5))
                plot_acf(x, lags=lag_time_max, ax=ax)
                # xtick 距離 n 的倍數，繪製 x major tick
                ax.xaxis.set_major_locator(MultipleLocator(x_interval))
                ax.grid(True)
                ax.set_title(f'{sitename} {itemname} 自相關係數圖', loc='left')
                plt.savefig(f'images/河川水質/自相關/{sitename}_{itemname}_自相關係數圖.png', dpi=300)

            if method == 2:
                autocorr = [data2.itemvalue.autocorr(i) for i in range(0, lag_time_max+1)]

                ax = axes[i]
                # fig, ax = plt.subplots(figsize=(8, 5))
                if itemname in ['鉛', '鋅']:
                    xx = range(0, len(autocorr)*3, 3)
                    xtick = range(0, len(autocorr)*3, x_interval)
                else:
                    xx = range(0, len(autocorr), 1)
                    xtick = range(0, len(autocorr), x_interval)
                print(sitename, itemname, len(xx), len(autocorr))
                ax.scatter(xx, autocorr, marker='o', color=(.1,.1,.1), s=50)  
                ax.bar(xx, autocorr, color=(.1,.1,.1), width=0.1)  
                ax.set_ylim(-1.2, 1.2)
                ax.axhline(0, 0, len(autocorr), color='k', linestyle='-', linewidth=1)
                
                ax.set_xticks(xtick)
                # if itemname in ['鉛', '鋅']:
                #     xticklabel = [i*3 for i in xtick]
                #     ax.set_xticklabels(xticklabel)

                ax.grid(True)
                ax.set_xlabel('自相關遲滯月數', fontsize=12)
                ax.set_title(f'{itemname}', fontsize=14, loc='left')
                ax.set_xlim(-2, xtick[-1]+2)

        # 移除沒有圖的subplot
        for i in range(len(monitoring_data_all.itemname.unique()), len(axes)):
            fig.delaxes(axes[i])
        # layout tight
        fig.tight_layout()
        plt.savefig(f'images/河川水質/自相關_測站/{basin}_{sitename}_自相關係數圖.png', dpi=300)


            

def test():
    # 定義參數
    years = 100
    amplitude = 20
    mean = 20
    noise_std_dev = 1

    # 生成時間點
    num_points = years * 12
    months = np.arange(num_points)

    # 產生具有年週期的cos數據
    data = amplitude * np.cos(2 * np.pi * months / 12)

    # 添加隨機的波動
    noise = np.random.normal(0, noise_std_dev, num_points)
    data += noise

    # 添加平均值
    data += mean

    # 轉換為 pandas DataFrame
    df = pd.DataFrame(data, columns=['Value'])

    # 如果你想為每個月份創建一個時間索引
    date_index = pd.date_range(start='1/1/1920', periods=num_points, freq='M')
    df.set_index(date_index, inplace=True)    

    # Create a time series
    x = df.Value.values
    autocorr, confint = acf(x, nlags=36, alpha=0.05)
    #繪製自相關係數圖與信賴區間
    plt.close('all')
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(autocorr)), autocorr, marker='o')
    plt.fill_between(range(len(confint)), confint[:, 0], confint[:, 1], alpha=0.5)
    plt.xlabel("Lag")


def calculate_statistic():
    items = ['水溫', '導電度', '酸鹼值', '溶氧(電極法)', '溶氧飽和度',
            '氯鹽', '氨氮', '硝酸鹽氮', '總有機碳', '砷',
            '鎘', '鉻', '銅', '鉛', '鋅',
            '錳', '汞', '鎳']
    df = read_river_monitoring_data_update()
    # read method2
    # with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
    #     params = {'basin': '二仁溪流域', 'itemname': '鉛', 'sitename': '二層行橋'}
    #     df = gpd.read_postgis(text('''
    #                         select * from river_monitoring_data_opendata 
    #                         where basin = :basin and itemname = :itemname and sitename = :sitename and itemvalue <> '-'
    #                         '''), con=engine, params=params, geom_col='geometry')
    # df = read_groundwater(basin_name=None, itemname=None)
    # read method3
    df2 = read_river_monitoring_data_ver3()

    # df_2 = df[(df.itemname=='鉛') & (df.basin=='二仁溪流域') & (df.sitename=='二層行橋')]
    # df1_2 = df1[(df1.itemname=='鉛') & (df1.basin=='二仁溪流域') & (df1.sitename=='二層行橋')]
    # df2_2 = df2[(df2.itemname=='鉛') & (df2.basin=='二仁溪流域') & (df2.sitename=='二層行橋')]

    df = df.dropna(subset=['itemvalue'])
    df = df[df.itemvalue != '-']
    df.county = (
        df.county
        .str.replace('桃園縣', '桃園市')
        .str.replace('新竹縣', '新竹市')
        .str.replace('台北', '臺北')
        .str.replace('台南', '臺南')
        .str.replace('台中', '臺中')
        .str.replace('臺中縣', '臺中市')
        .str.replace('臺南縣', '臺南市')
        )
    df['year'] = df.sampledate2.dt.year
    df = df.assign(count=1)
    df_stat1 = df.groupby(['basin', 'sitename', 'itemname', 'county', 'year'], as_index=False)[['count']].count()
    df_stat1 = df_stat1.pivot(index=['basin', 'sitename', 'itemname', 'county'], columns='year', values='count').fillna(0)
    df_stat1 = df_stat1.reset_index()
    df_stat1 = df_stat1.sort_values(['county', 'basin', 'sitename', 'itemname'])
    df_stat1 = df_stat1[df_stat1.itemname.isin(items)]#.set_index(['county', 'basin', 'sitename', 'itemname'])
    df_stat1.to_excel('./data/Result_data/河川水質/河川水質-資料數量年份統計.xlsx')