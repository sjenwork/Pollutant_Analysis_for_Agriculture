from RiverBasinPolyData import read_river_basin, read_river_poly
from RiverMonitor import read_river_monitoring_data
import pandas as pd

poly = read_river_poly()
basin = read_river_basin()
basin_list = basin.BASIN_NAME.to_list()

river_obs = read_river_monitoring_data()
river_obs_unique = river_obs.drop_duplicates(subset=['basin'])['basin'].to_list()
river_obs_unique = [i.replace("流域", "") for i in river_obs_unique]

obs_not_in_basin = [i for i in river_obs_unique if i not in basin_list] #['鹽港溪', '新豐溪', '吉安溪', '福興溪']
basin_not_in_obs = [i for i in basin_list if i not in river_obs_unique]


df = pd.read_excel('data/Result_data/Data_for_mapping_overlap/法定農業用地佔各流域的面積比.xlsx', index_col=0)
df['無河川監測資料'] = False
df.loc[df.河川流域.isin(basin_not_in_obs), '無河川監測資料'] = True
df.to_excel('data/Result_data/Data_for_mapping_overlap/法定農業用地佔各流域的面積比_附加無監測資訊.xlsx', index=False)

df = pd.read_excel('data/Result_data/Data_for_mapping_overlap/農糧作物佔各流域的面積比.xlsx', index_col=0)
df['無河川監測資料'] = False
df.loc[df.河川流域.isin(basin_not_in_obs), '無河川監測資料'] = True
df.to_excel('data/Result_data/Data_for_mapping_overlap/農糧作物佔各流域的面積比_附加無監測資訊.xlsx', index=False)

with open('data/Result_data/Basin_data/流域無監測資料.txt', 'w') as f:
    f.write('\n'.join(basin_not_in_obs))