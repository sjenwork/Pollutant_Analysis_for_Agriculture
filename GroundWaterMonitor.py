import geopandas as gpd
import matplotlib.dates as mdates
import pandas as pd
from matplotlib.ticker import MultipleLocator
from sqlalchemy import text
import numpy as np
import os 
import copy
import matplotlib.pyplot as plt
from utils.sql import connPostgreSQL
import seaborn as sns


from utils.plot_utils import generate_colordict
from utils.plot_utils import generate_randomcolor

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']



def read_groundwater(basin_name=['二仁溪', '老街溪'], itemname = ['鉛', '鋅', '導電度', '水溫', '酸鹼值']):
    # basin_name=['二仁溪', '老街溪']
    # itemname = ['鉛', '鋅', '導電度', '水溫', '酸鹼值']
    where = ' where '
    wherecmd = []
    params = {}
    if basin_name is not None:
        wherecmd.append("basin_name IN :basin_name")
    if itemname is not None:
        wherecmd.append("itemname IN :itemname")
    where = where + ' and '.join(wherecmd)
    if where.strip() == 'where':
        where = ''
    else:
        params = {'basin_name': tuple(basin_name), 'itemname': tuple(itemname)}
    sql = text(''' 
            SELECT a.sitename, a.ugwdistname, a.county, a.itemname, a.itemvalue, a.itemunit, a.sampledate2, a.geometry, a.comment, b.basin_name    
            FROM ground_water_monitor_data a
            inner join riverbasin as b ON ST_Contains(b.geom , ST_Transform(a.geometry, 3826))
            ''' + where )
    with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
        df = gpd.read_postgis(sql, engine, geom_col='geometry', params=params)
    return df


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
        time_freq = '3MS'
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
        plot_line=False,
        ):
    


    def write_plot_data(data, sitename, chem, write_plot_data_path):
        if write_plot_data:
            if write_plot_data_path is not None:
                if os.path.exists(write_plot_data_path) == False:
                    os.makedirs(write_plot_data_path)
                data.to_excel(f'{write_plot_data_path}/{sitename}_{chem}.xlsx', index=False)

    if len(data) == 0:
        return
    
    mdl = {'鉛': 0.003, '鎘': 0.001, '鋅': 0.002}

    year0, year1 = year_limit
    data2 = copy.deepcopy(data)
    data2 = data2.sort_values(by=['sampledate2'])
    max_value = data[(data.itemname == chem) & (data.sampledate2.dt.year>=year0) & (data.sampledate2.dt.year<=year1)].itemvalue.max()
    if max_value < mdl[chem]:
        max_value = mdl[chem]
    max_value = max_value + max_value * 0.1
    if special_case_ylim:
        if chem == '鉛':
            max_value = 0.01
        elif chem == '鋅':
            max_value = 0.5
    unit = data[data.itemname == chem].itemunit.iloc[0]

    if not plot_line:
        def process_data2(data2, unit, year_limit):
            sitenames = data2.sitename.unique()
            res = []
            for sitename in sitenames:
                tmp = data2[data2.sitename == sitename]
                tmp2 = process_data(tmp, unit, year_limit)
                res.append(tmp2.assign(sitename=sitename))
            return pd.concat(res)
        
        plt.close('all')
        fig, ax = plt.subplots(figsize=(8, 2.5))
        data3 = process_data2(data2, unit, year_limit)
        data3.sitename = data3.sitename.apply(lambda i: i.split('(')[0])
        data3['sampledate3'] = data3['sampledate2'].dt.strftime('%Y-%m')


        # sns.catplot(data=data3, x='sampledate2', y='itemvalue', hue='sitename', kind='bar', ax=ax, palette='dark', legend=False)
        sns.barplot(data=data3, x='sampledate3', y='itemvalue', hue='sitename', ax=ax,)
        ax.set_ylim([0, max_value])


        ax.set_title(f'''地下水（{basin}流域） - {chem}時序圖''', fontsize=16)
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.tick_params(axis='x', labelrotation=90, labelsize=8)  
        # 繪製 minor tick
        major_ticks = ax.yaxis.get_major_ticks()
        # return ax
        major_tick_spacing = major_ticks[1].get_loc() - major_ticks[0].get_loc()
        if major_tick_spacing > 0:
            ax.yaxis.set_minor_locator(MultipleLocator(major_tick_spacing/5))  # 你需要根據你的主要刻度間距來調整這個值
        

        ax.axhline(mdl[chem], color='red', linestyle='dashed', linewidth=.5)
        size_dict = {'small': 8, 'medium': 10, 'large': 12, 'x-large': 16, 'xx-large': 20}
        title_font_size = size_dict[plt.rcParams['axes.titlesize']]
        ax.text(1.0, 1.0, '--- MDL', transform=ax.transAxes, va='bottom', ha='right', fontsize=title_font_size*1, color='red')

        plt.tight_layout()  # 自動調整軸的大小
        ax.grid(True, linewidth=0.5, color='gray')
        ax.set_xlabel('')
        ax.set_ylabel(data3.itemunit.iloc[0])
        ax.legend(ncol=5, bbox_to_anchor=(0, -.7), loc='lower left', fontsize=10, frameon=False)

        # xticklabels = ax.xaxis.get_ticklabels()
        # xticklabels = [j if i%2==0 else '' for i,j in enumerate(xticklabels)]
        # ax.xaxis.set_ticklabels(xticklabels)
        # ax.set_xticklabels(xticklabels, ha='right')  # 右对齐


    if plot_line:
        colors = generate_randomcolor(20)
        for ii, sitename in enumerate(data2['sitename'].unique()[:]):
            data3 = data2[data2.sitename == sitename]
            data3 = process_data(data3, unit, year_limit=year_limit)

            write_plot_data(data3, sitename, chem, write_plot_data_path)
            

            data3['sampledate_label'] = data3['sampledate2'].apply(lambda x: f"{x.year-1911}-{x.month:02d}")
            

            
            npermon = 4
            data3.plot(ax=ax, x='sampledate2', y='itemvalue', label=sitename.split('(')[0], color=colors[ii], linewidth=.5, marker='o', markersize=1)
            print(data3)
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
                xlim = (year0-1970)*npermon, (year1-1970+1)*npermon-1
                ax.set_xlim(*xlim)
                xlim = ax.get_xlim()                
            elif chem == '酸鹼值':
                ax.set_ylim([6, max_value])
                ax.set_yticks(np.arange(6, max_value+1, 1))
                ax.yaxis.set_minor_locator(plt.NullLocator())
                ax.set_ylabel('pH')
                # ax.axhline(y=9, color=(.97, 0, 0, .9), linestyle='-', linewidth=.1)
                xlim = (year0-1970)*npermon, (year1-1970+1)*npermon-1
                ax.set_xlim(*xlim)
                xlim = ax.get_xlim()
            elif chem == '導電度':
                ax.set_ylim([0, max_value])
                # ax.set_yticks(np.arange(6, max_value+1, 1))
                ax.set_ylabel('μmho/cm25°C')
                xlim = (year0-1970)*npermon, (year1-1970+1)*npermon-1
                ax.set_xlim(*xlim)
                xlim = ax.get_xlim()                



            ax.set_xlabel('')
            
            

            # ax.xaxis.set_major_locator(mdates.YearLocator(5))  # 3 years
            # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

            # ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))  # 3 months



            # 繪製 minor tick
            major_ticks = ax.yaxis.get_major_ticks()
            # return ax
            major_tick_spacing = major_ticks[1].get_loc() - major_ticks[0].get_loc()
            if major_tick_spacing > 0:
                ax.yaxis.set_minor_locator(MultipleLocator(major_tick_spacing/5))  # 你需要根據你的主要刻度間距來調整這個值



            

            ax.axhline(mdl[chem], color='red', linestyle='dashed', linewidth='1')
            size_dict = {'small': 8, 'medium': 10, 'large': 12, 'x-large': 16, 'xx-large': 20}
            title_font_size = size_dict[plt.rcParams['axes.titlesize']]
            ax.text(1.0, 1.0, '--- MDL', transform=ax.transAxes, va='bottom', ha='right', fontsize=title_font_size*1, color='red')


            plt.tight_layout()  # 自動調整軸的大小
            ax.grid(True, linewidth=0.5, color='gray')


            # 添加次要的網格線
            ax.minorticks_on()
            ax.yaxis.grid(True, which='minor', linestyle=':', linewidth='0.5', color='gray')


        # 存檔

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

    chems = ['鉛', '鋅']
    # chems = ['導電度', '水溫', '酸鹼值']
    # chems = ['酸鹼值']
    basin_list = ['老街溪', '二仁溪']
    # basin_list = ['南崁溪流域', '老街溪流域', '鹽水溪流域', '二仁溪流域']

    data_source = 'open_data'
    if data_source == 'open_data':
        monitoring_data_all = read_groundwater()

    # chem = '水溫'
    # basin = '老街溪'
    print('plotting')
    for chem in chems[:]:
        for basin in basin_list[:]:
            print(basin, chem)
            data = monitoring_data_all[(monitoring_data_all.basin_name==basin) & (monitoring_data_all.itemname==chem)]
            # append_data = {
            #     '導電度': monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname=='導電度')],
            #     '水溫': monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname=='水溫')],
            #     '酸鹼值': monitoring_data_all[(monitoring_data_all.basin==basin) & (monitoring_data_all.itemname=='酸鹼值')],
            # }
            a = plot_timeSeries(
                data=data,
                # append_data=append_data, # 畫完效果非常可怕，不要用
                chem=chem,
                basin=basin,
                path=f'./images/區域性地下水/流域分析/{data_source}/{basin}/{chem}', 
                FigName_prefix='_v4_update_MDL_and_mark_out_of_limit_season',
                write_plot_data=False,
                write_plot_data_path=f'./data/Result_data/River_Monitor_Data/{data_source}/{basin}/{chem}',
                special_case_ylim=False,
                year_limit=(2014, 2022),
                plot_line=False
            )


def calculate_statistic():
    items = ['水溫', '導電度', '酸鹼值', '溶氧(電極法)', '溶氧飽和度',
            '氯鹽', '氨氮', '硝酸鹽氮', '總有機碳', '砷',
            '鎘', '鉻', '銅', '鉛', '鋅',
            '錳', '汞', '鎳']
    df = read_groundwater(basin_name=None, itemname=None)
    df = df.dropna(subset=['itemvalue'])
    df.county = (
        df.county
        .str.replace('桃園縣', '桃園市')
        .str.replace('新竹縣', '新竹市')
        .str.replace('台北', '臺北')
        .str.replace('台南', '臺南')
        .str.replace('台中', '臺中')
        .str.replace('臺中縣', '臺中市')
        .str.replace('台東', '臺東')
        .str.replace('臺南縣', '臺南市')
        )
    df['year'] = df.sampledate2.dt.year
    df = df.assign(count=1)
    df_stat1 = df.groupby(['basin_name', 'sitename', 'itemname', 'county', 'year'], as_index=False)[['count']].count()
    df_stat1 = df_stat1.pivot(index=['basin_name', 'sitename', 'itemname', 'county'], columns='year', values='count').fillna(0)
    df_stat1 = df_stat1.reset_index()
    df_stat1 = df_stat1.sort_values(['county', 'basin_name', 'sitename', 'itemname'])
    df_stat1 = df_stat1[df_stat1.itemname.isin(items)]
    df_stat1.to_excel('./data/Result_data/區域性地下水/區域性地下水-資料數量年份統計-行政區修正版.xlsx')