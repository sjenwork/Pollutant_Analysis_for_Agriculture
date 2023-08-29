import requests
# https://geoser.epa.gov.tw/sgwdm/index.html


data = requests.get( 'https://services7.arcgis.com/tVmMUEViFfyHBZvj/arcgis/rest/services/%E5%9C%9F%E5%A3%A4%E5%8F%8A%E5%9C%B0%E4%B8%8B%E6%B0%B4%E6%B1%A1%E6%9F%93%E5%A0%B4%E5%9D%80%E5%9F%BA%E6%9C%AC%E8%B3%87%E6%96%991111122/FeatureServer/0/query?f=json&where=(1%3D1)&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=POLLUTANT&returnDistinctValues=true&orderByFields=POLLUTANT&outSR=102100&resultOffset=0' )
res = data.json()['features']
