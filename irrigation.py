import pandas as pd
import os
import pathlib
import geopandas as gpd
from utils.sql import connPostgreSQL

pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0

pth = 'data/灌溉水'
fns = os.listdir(pth)

dfs = []
for fn in fns[:]:
    fn2 = pathlib.Path(pth, fn)
    print(fn2)
    # 取得所有的sheet
    xl = pd.ExcelFile(fn2)
    sheet_names = xl.sheet_names
    for sheet_name in sheet_names:
        print(sheet_name)
        df = pd.read_excel(fn2, sheet_name=sheet_name, skiprows=2, skipfooter=5)
        df = df.assign(filename=fn2, sheet_name=sheet_name)
        dfs.append(df)
dfs = pd.concat(dfs)
dfs2 = dfs.dropna(subset=['管理處名稱'])  
dfs2['ym'] = pd.to_datetime(dfs2['採樣日期'])#.dt.strftime('%Y-%m')
# dfs3 = dfs2.groupby(['管理處名稱', '監測點名稱'], as_index=False).agg({
#     '採樣日期': lambda i: ','.join(map(str,set(pd.to_datetime(i).dt.strftime('%Y-%m-%d'))))
# })
# dfs3 = dfs3.assign(len=dfs3.採樣日期.str.split(',').str.len())
# dfs3 = dfs3.sort_values('len', ascending=False)


dfs3 = dfs2.groupby(['管理處名稱', '工作站', '監測點名稱', 'TWD97_X座標', 'TWD97_Y座標'], as_index=False).agg({
    'ym': lambda i: ','.join(sorted(list(set(i))))
})
dfs3 = dfs3.assign(len=dfs3.ym.str.split(',').str.len())
dfs4 = gpd.GeoDataFrame(dfs3, geometry=gpd.points_from_xy(dfs3.TWD97_X座標, dfs3.TWD97_Y座標))

with connPostgreSQL(use_ssh_tunnel=True, db='simenvi_postgresql') as engine:
    ###### 讀取圖資
    sql = ''' select * from riverbasin where basin_name in ('老街溪', '二仁溪') '''
    river_basin = gpd.read_postgis(sql, engine, geom_col='geom')
    print(f'完成讀取流域圖資')

# 找出dfs4 point在river_basin的流域
dfs5 = gpd.sjoin(dfs4, river_basin, how='right', op='within').drop(['basin_no', 'area', 'basin_id', 'extent', 'geom', 'gid'], axis=1)
dfs5 = dfs5.rename(columns={'ym': '年月列表', 'len': '時間(年月)筆數', })
dfs5.to_excel('data/Result_data/灌溉水/二仁溪_老街溪_灌溉水統計.xlsx', index=False)
