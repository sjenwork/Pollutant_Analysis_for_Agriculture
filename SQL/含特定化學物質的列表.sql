    select chem.chemicalSN, chem.CASNo 原系統CasNo , chem.ChemicalChnName 原系統中文名, chem.ChemicalEngName 原系統英文文名,  map.ChemiChnNameMatch from (
        select distinct value chemicalsn
        from ChemiAutoData
        WHERE data LIKE '%鋅%'
    ) selchem
    LEFT JOIN ChemicalData chem
    ON selchem.chemicalsn = chem.ChemicalSN
    LEFT JOIN ChemiMatchMapping map
    on map.CASNoMatch = chem.CASNo
    order by ChemicalChnName

    -- WHERE chem.ChemiChnNameRev LIKE '%鋅%'

    -- select  * from ChemicalData where transid = 'MOEA000012181203202236906'
    -- select  * from ChemicalData where transid = 'MOEA000012181203202039367'

-- select * from chemicalData_For_Analysis