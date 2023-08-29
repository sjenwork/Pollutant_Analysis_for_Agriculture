import pathlib
import os
import pandas as pd
import geopandas as gpd
from utils.sql import connSQL
from sqlalchemy import text
import re
import copy
from shapely.geometry import Point

from RiverBasinPolyData import read_river_basin
from TaiwanCounty import read_taiwan_admin_map

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0

def compare_data():
    engine = connSQL('chemiPrim_Test_ssh')
        
    path_1 = pathlib.Path('data/化學物質廠商運作明細/API')
    path_2 = pathlib.Path('data/化學物質廠商運作明細/API_v2')
    chems = ["鉛", "鋅", "鎘"]
    for chem in chems:
        chem_item_1 = os.listdir(path_1/chem)
        chem_item_2 = os.listdir(path_2/chem)
        # Step1: 比較兩個資料夾的檔案列表確認是否相同，結果顯示兩個資料夾的檔案列表相同
        confirm = False
        if confirm:
            not_in_1 = [i for i in chem_item_2 if i not in chem_item_1]
            not_in_2 = [i for i in chem_item_1 if i not in chem_item_2]
            print(not_in_1, not_in_2)
        for chem_item in chem_item_1:
            df1 = pd.read_csv(path_1/chem/chem_item)
            df2 = pd.read_csv(path_2/chem/chem_item)
            # 合并 df1 和 df2
            merged = pd.merge(df1, df2, how='outer', indicator=True)

            # 找出只在 df1 中出现的行
            only_df1 = merged[merged['_merge'] == 'left_only']

            # 找出只在 df2 中出现的行
            only_df2 = merged[merged['_merge'] == 'right_only']
            print('-------------------')
            # print(f'{chem_item} 只在舊的有的：',only_df1.申報日期.unique())
            # print(f'{chem_item} 只在新的有的：',only_df2.申報日期.unique())
            # print(only_df2.申報日期.unique())
            res = only_df2.drop('_merge', axis=1).to_sql('Chemical_River_Analysis', con=engine, index=False, if_exists='append', chunksize=1000)
            print(res)



def prepare_data():
    '''
    將化學雲下載的資料寫入測試資料庫
    '''
    engine = connSQL('chemiPrim_Test_ssh')
    path = pathlib.Path('data/化學物質廠商運作明細/API_v2')
    columns = ['Cas No.', '化學物質中文名稱', '化學物質英文名稱', '公司統編/廠編', '申報公司名稱', '行業別', '營業項目', '郵遞區號',
        '縣市別', '地址', '來源單位', '來源系統', '申報日期', '運作行為', '運作量', '運作量單位', '上游公司統編/廠編',
        '上游公司名稱', '下游公司統編/廠編', '下游公司名稱']
    chems = ['鉛', '鋅', '鎘']
    for chem in chems[0:1]:
        path_chem = path/chem
        fns = os.listdir(path_chem)
        comFacBizs = []
        for fn in fns:
            tmp = pd.read_csv(path_chem/fn)
            tmp.columns = columns
            tmp = tmp.assign(Main_Chem=chem)
            comFacBizs.append(tmp)
        comFacBizs = pd.concat(comFacBizs)
        print(len(comFacBizs))
        comFacBizs.to_sql('Chemical_River_Analysis', con=engine, index=False, if_exists='append')


def getComFacBiz_location(chem):
    '''
    繪圖用，取得不重複的廠商與座標
    '''    
    engine = connSQL('chemiPrim_Test_ssh')
    sql = text(''' 
    select distinct [公司統編/廠編] as adminno, 申報公司名稱 as comName, 地址 as addr, b.TWD97TM2X, b.TWD97TM2Y
    from Chemical_River_Analysis a
    left join GISMappingTWD97 b
    on a.[公司統編/廠編] = b.AdminNo
    where Main_Chem=:chem and TWD97TM2Y is not null and TWD97TM2Y <> '-'  and 運作量 <> '無'
    ''')
    params = {'chem': chem}
    data1 = pd.read_sql(sql, params=params, con=engine)
    use = False
    if use:
        sql = text(''' 
        select distinct [公司統編/廠編] as adminno, 申報公司名稱 as comName, 地址 as addr, b.TWD97TM2X, b.TWD97TM2Y
        from Chemical_River_Analysis a
        left join GISMappingTWD97 b
        on a.地址 = b.[RegularAddress]
        where Main_Chem=:chem and TWD97TM2Y is not null and TWD97TM2Y <> '-'  and 運作量 <> '無'
        ''')
        params = {'chem': chem}
        data2 = pd.read_sql(sql, params=params, con=engine)
        data = pd.concat([data1, data2]).drop_duplicates(subset=data1.columns)
    
    data = data1
    data = data.assign(city=data.addr.apply(findCity))
    data_gpd = twd97_to_wgs84(data)
    return data_gpd

def getComFacBiz_location_v2(chem, time_between):
    '''
    繪圖用，取得不重複的廠商與座標
    '''
    
    df = find_comfacbiz_fit(chem, time_between)
    columns = ['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y']
    df2 = df[columns].drop_duplicates()
    df2 = df2.assign(city=df2.addr.apply(findCity))
    df2_gpd = twd97_to_wgs84(df2)
    return df2_gpd

def twd97_to_wgs84(df):
    df_gpd = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.TWD97TM2X, df.TWD97TM2Y) )
    df_gpd = df_gpd.set_crs(epsg=3826)
    df_gpd = df_gpd.to_crs(epsg=4326)
    df_gpd['twd97lon'] = df_gpd.geometry.x
    df_gpd['twd97lat'] = df_gpd.geometry.y
    return df_gpd

def findCity(i):
    try:
        i = i.replace('新竹科學園區', '')
        i = i.replace('中部科學園區', '')
        i = i.replace('臺南科學園區', '')
        i = i.replace('南科高雄園區', '')
        return re.findall('^.{0,3}[縣市]', i)[0]
    except:
        return i
        
def read_confrim_operation():
    '''
    整理符合的運作廠商條件，輸出
    1. 系統與運作行為關係
    2. 系統與備註關係
    '''
    df = pd.read_excel('data/Result_data/來源系統運作行為YH.xlsx',index_col=[0])
    df = df.reset_index()
    df['備註'] = df['備註'].fillna('')
    df1 = df[df['使用'].apply(lambda x: True if x == 1 else False)]
    df1 = df1.fillna('')

    df2 = df[['來源系統', '備註']]
    df2 = df2[df2.備註!='']

    return df1[['來源系統', '運作行為']].to_dict('records'), df2.to_dict('records')

def find_comfacbiz_fit(chem, time_between):
    '''
    找出所有資料中，符合我們所要「系統來源的運作行為」(整理在 data/Result_data/來源系統運作行為YH.xlsx 的檔案)
    而且要有座標、要有運作量、申報時間
    '''
    data, comment = read_confrim_operation()

    engine = connSQL('chemiPrim_Test_ssh')
    WHERE = []
    for i in data[:]:
        WHERE.append (f'''(來源系統 = '{i['來源系統']}' and 運作行為 = '{i['運作行為']}')''')
    WHERE = ' AND (' + ' OR '.join(WHERE) + ')'

    T0 = f'''{str(time_between[0])[:3]}年第{str(time_between[0])[3:4]}季'''
    T1 = f'''{str(time_between[1])[:3]}年第{str(time_between[1])[3:4]}季'''
    sql = f'''
    SELECT [公司統編/廠編] as adminno, 申報公司名稱 as comName, 地址 as addr, try_cast(b.TWD97TM2X as float) TWD97TM2X, try_cast(b.TWD97TM2Y as float) TWD97TM2Y, 來源系統 as system, 申報日期 as time, 運作行為 as operation, TRY_CAST(運作量 as float) as amount, 運作量單位 as unit
    FROM Chemical_River_Analysis a
    left join GISMappingTWD97 b
    on a.[公司統編/廠編] = b.AdminNo
    WHERE 
    Main_Chem = '{chem}' AND 
    TWD97TM2Y is NOT NULL AND TWD97TM2Y <> '-'  AND 
    運作量 <> '無' AND 
    TRY_CAST(運作量 as float)>0 AND 
    申報日期 <> '-' AND 申報日期>='{T0}' and 申報日期<='{T1} '
    ''' + WHERE

    df = pd.read_sql(sql, engine)
    return df




def confirm_data_time(chem='鉛', time_between=[1071, 1114]):
    '''
    需要整理

    Step1: 先找出所有資料中，符合我們所要「系統來源的運作行為」，而且要有座標、要有運作量、申報時間
    Step2: 把這些符合的資料，關聯回原來系統的表格，找出各系統所有不重複的申報時間。
    Step3: 將資料一來源系統為單位，確認是要使用哪種類型的時間（如：季、年、半年）
    '''

    #Step1
    df = find_comfacbiz_fit(chem, time_between)    
    df.time = df.time.astype(str).str.replace('年第', 'Q').str.replace('年', '').str.replace('', '').str.replace('季', '')

    df_time_by_system = df[['system', 'time']].drop_duplicates().groupby('system').agg({'time': lambda x: ','.join(sorted(set(x)))})

    df_all = pd.read_excel('data/Result_data/來源系統運作行為YH.xlsx',index_col=[0]).reset_index()
    df_all['備註'] = df_all['備註'].fillna('')
    df_all_2 = df_all.merge(df_time_by_system, left_on='來源系統', right_index=True, how='left')
    df_all_2.time = df_all_2.time.fillna('')
    df_all_2 = df_all_2.set_index(['來源系統', 'time', 'id'])
    df_all_2 = df_all_2.sort_index(level=['time', '來源系統'], ascending=False)
    df_all_2 = df_all_2.rename_axis(index={'time': '符合的運作行為，運作量經過篩選(>0)、有座標的不重複時間'})

    df_all_2.to_excel('data/Result_data/來源系統運作行為YH_申報期別確認.xlsx', index=True)

    # Step2
    time = pd.DataFrame(list(df_all_2.index), columns=['來源系統', 'time', 'id']).drop('id', axis=1).drop_duplicates()
    def find_uniuqe_season(i):
        i_list = i.split(',')
        res = []
        for elem in i_list:
            cond = re.findall('.*(Q[1-4])', elem)
            if cond:
                res.append(cond[0])
            else:
                if i != '':
                    res.append('Year')
                else: 
                    res.append('')
        res = list(set(res))
        if 'Q2' in res or 'Q4' in res:
            return 'season'
        elif 'Year' in res:
            return 'year'
        elif 'Q1' in res or 'Q3' in res:
            return 'half_year'
        else:
            return ''

    # Step3
    time['頻率'] = time.time.apply(find_uniuqe_season)
    time = time[time.頻率 != '']
    time2 = time.groupby('頻率', as_index=False).agg({'來源系統': list}).set_index('頻率', drop=True)
    return time2

def get_freq():
    '''
    將所有化學物質 對應的系統 的頻率 整理出來
    '''
    data_pb = confirm_data_time(chem = '鉛').assign(chem = '鉛')
    data_zn = confirm_data_time(chem = '鋅').assign(chem = '鋅')
    data_cd = confirm_data_time(chem = '鎘').assign(chem = '鎘')
    data = pd.concat([data_pb, data_zn, data_cd]).reset_index().rename(columns={'index': '頻率'})
    data.to_excel('data/Result_data/三種化學物質系統與頻率確認.xlsx', index=False)

    return data

def get_distinct_operation_by_source():
    engine = connSQL('chemiPrim_Test_ssh')
    sql = text('''
            SELECT distinct 來源系統 ,運作行為 FROM Chemical_River_Analysis order by 來源系統
               ''')
    params = {}
    data = pd.read_sql(sql, params=params, con=engine)
    data = data.reset_index().rename({'index': 'id'}, axis=1).set_index(['來源系統', 'id'])
    data.to_excel('data/Result_data/來源系統運作行為.xlsx',index=True)
    return data

def export_ComFacBiz_Statistic_Data(chem, time_between):
    '''
    將符合運作行為的資料，依據需求（不同系統資料特性，詳見 data/Result_data/來源系統運作行為YH.xlsx 檔案說明）
    進行統計加總，取得年、季的統計資料
    '''
    # chem = '鉛'

    # 取得符合的資料
    comfacbiz = find_comfacbiz_fit(chem, time_between) # 12290

    # 資料處理

    # 先處理單位，有些單位寫在 operation ，如 公斤，需要檢查確認
    comfacbiz.loc[comfacbiz.unit=='-', 'unit'] = '公斤'
    # 把 '頓', '公噸', '噸' -> '公斤'
    comfacbiz.loc[comfacbiz.unit.isin(['頓', '公噸', '噸']), 'amount'] = comfacbiz.loc[comfacbiz.unit.isin(['頓', '公噸', '噸']), 'amount']*1000
    comfacbiz.loc[comfacbiz.unit.isin(['頓', '公噸', '噸']), 'unit'] = '公斤'
    # 把 '公斤', '.公斤' -> '公斤'
    comfacbiz.loc[comfacbiz.unit.isin(['公斤', '.公斤']), 'unit'] = '公斤'
    # 把 '.公升', '公升' -> '公斤' ****** 公升 直接 轉成 公斤
    comfacbiz.loc[comfacbiz.unit.isin(['.公升', '公升']), 'unit'] = '公斤' 


    # 依據系統進行各自的處理
    res = ''
    res_all = []
    systems = get_distinct_operation_by_source().reset_index().來源系統.unique()
    for system in systems:
        print(system)
        if system == '危險品申報系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )

        elif system == '化學品自主申報平台':
            data = comfacbiz[comfacbiz.system == system]
            # 將 '月' 的數量乘以 12 變成年
            data.loc[data.operation.str.contains('月'), 'amount'] = data.loc[data.operation.str.contains('月'), 'amount']*12
            # 取最大
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'max', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )        
        elif system == '水污染源管制資料管理系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )
            
        elif system == '土壤及地下水污染整治費網路申報及查詢系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )        
        elif system == '生產選定化學物質工廠申報系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )        
                    
        elif system == '工廠危險物品申報網':
            data = copy.deepcopy(comfacbiz[comfacbiz.system == system])
            data.loc[:, 'time'] = copy.deepcopy(data.time.str.replace('年.*季', '',regex=True))
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )        

        elif system == '事業廢棄物申報及管理資訊系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )      

        elif system == '毒性及關注化學物質登記申報系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )      

        elif system == '固定空氣污染源管理資訊系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )     

        elif system == '化學品報備與許可平台(優先管理化學品)':
            data = comfacbiz[comfacbiz.system == system]
            data.loc[:, 'time'] = copy.deepcopy(data.time.str.replace('年', '',regex=True))
            # max
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'max', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )     
            
        elif system == '飼料管理系統': #不應該有
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '食品追溯追蹤管理資訊系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'max', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )     

        elif system == '食品業者登錄平台':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '邊境查驗自動化管理資訊系統':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '資源再利用管理資訊系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )     
            
        elif system == '藥證業務管理資訊系統':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '菸品成分資料網':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '消防安全檢查列管系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )     
                    
        elif system == '土壤及地下水資訊管理系統':
            data = comfacbiz[comfacbiz.system == system]
            res = (data
                .groupby(['adminno', 'comName', 'addr', 'TWD97TM2X', 'TWD97TM2Y', 'system', 'time'], as_index=False)
                .agg({'amount': 'sum', 'unit': 'first'})
                .sort_values(by=['adminno', 'time'])
                )     
                    
        elif system == '危險物品臨時通行證系統':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '化粧品產品登錄平台系統':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '化工原料行輔導訪查資料':
            # data = comfacbiz[comfacbiz.system == system]
            continue
        elif system == '化學物質登錄平台(既有化學物質)':
            # data = comfacbiz[comfacbiz.system == system]
            continue


        # print(f'{system} 有 {len(data)} 筆資料')
        if type(res) != str:
            res_all.append(res)

    res_all = pd.concat(res_all)

    res_all2 = gpd.GeoDataFrame(res_all, geometry=gpd.points_from_xy(res_all.TWD97TM2X, res_all.TWD97TM2Y), crs='EPSG:3826')
    taiwan = read_taiwan_admin_map()
    taiwan = taiwan.to_crs(epsg=3826)

    res_all3 = (
        gpd
        .sjoin(res_all2, taiwan[['geom', 'countyname']], how="left", op='within')
        .drop(columns=['index_right'])
        .rename({'countyname': '縣市(從座標)'}, axis=1)
    )
    res_all3['縣市(從地址)'] = res_all3.addr.apply(lambda x: re.match(r'^.+?[縣市]', x)[0] if re.match(r'.+?[縣市]', x) else None)
    res_all3 = res_all3.drop(['geometry'], axis=1)
    res_all3.to_excel(f'data/Result_data/運作清單/{chem}_依系統來源計算的運作明細清單統計_v3.xlsx', index=False)

    # 新增篩選在 老街溪 以及 二仁溪 流域的資料
    river_basin = read_river_basin()
    river_basin.to_crs(epsg=3826, inplace=True)
    river_basin = river_basin[river_basin.BASIN_NAME.isin(['老街溪', '二仁溪'])]

    for i, basin in river_basin.iterrows():
        print(f'篩選 {river_basin} 流域的資料')
        res_all_sub = res_all3[res_all3.apply(lambda x: Point(x['TWD97TM2X'], x['TWD97TM2Y']).within(basin.geometry), axis=1)]
        res_all_sub.to_excel(f'data/Result_data/運作清單/{chem}_依系統來源計算的運作明細清單統計_{basin.BASIN_NAME}_v3_更新遺失的107Q1_111Q4.xlsx', index=False)
    return res_all


if __name__ == '__main__':
    chem_list = ['鉛', '鋅', '鎘' ]
    for chem in chem_list[:2]:
        res_all = export_ComFacBiz_Statistic_Data(chem, time_between=[1071, 1114])