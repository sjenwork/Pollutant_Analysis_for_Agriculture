import pandas as pd
import requests
import os
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 400)
pd.options.display.width = 0


# chems = pd.read_csv('化學物質廠商運作明細/API/chem.txt', index_col=0)
# 化學物質廠商運作明細 API
# https://chemicloud.epa.gov.tw/ChemiCloud/WS/DataSearchDetail/GetOpAmtXls?ChemicalSN=504696&SessionToken=6e91a252cca042f321&accountId=jen2&sltSourceSystem=All&sltIsValid=1&CityName=All&District=null&fileType=json&txtStartDate=1081&txtEndDate=1124

# 廠商查化學物質運作明細 API
# https://chemicloud.epa.gov.tw/ChemiCloud/WS/DataSearchDetail/GetOpAmtXls?ComFacBizType=0&AdminNo=23526610&SessionToken=6e91a252cca042f321&accountId=jen2&sltSourceSystem=All&sltIsValid=1&fileType=json&txtStartDate=1091&txtEndDate=1094

chem_list = ['鉛', '鎘', '鋅']
SESSION = 'd5093aeb562ed16392'

for chem in chem_list:
    fn = f'data/化學物質廠商運作明細/API/chem_{chem}.xlsx'
    chem_detail = pd.read_excel(fn)
    chem_detail = chem_detail.drop_duplicates()

    url = 'https://chemicloud.epa.gov.tw/ChemiCloud/WS/DataSearchDetail/GetOpAmtXls?ChemicalSN=CHEMSN&SessionToken=SESSION&accountId=jen2&sltSourceSystem=All&sltIsValid=1&CityName=All&District=null&fileType=csv&txtStartDate=1071&txtEndDate=1124'

    for i, ichem in chem_detail.iterrows():
        # if i>0:continue
        iurl = url.replace('CHEMSN', str(ichem['chemicalSN'])).replace('SESSION', str(SESSION))
        print(iurl)
        x = requests.get(iurl)
        path = f'data/化學物質廠商運作明細/API_v2/{chem}'
        if os.path.exists(path) is False:
            os.makedirs(path)
        with open(f'''{path}/{ichem['ChnName']}.txt''', 'w') as f:
            f.write(x.text)



    
