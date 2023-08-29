-- select distinct chemichnnamerev from (
select map.TempTableName, dept.SDeptName, SystemName
        ,selchem.chemicalSN, selchem.ChemiChnNameRev
        ,sup.DeclareYearS, sup.DeclareMonthS
        ,sup.DeclareNumber, sup.DeclareStatus  ,sup.ApplicationInfo
        ,sup.DeclareValue ,sup.ProductionQuantity ,sup.UseageQuantity ,sup.ProductUseQuantity
        ,com.ComFacBizName, com.ComFacBizAddr
        ,map.MappingSN
from (
    select chem.chemicalSN, chem.ChemiChnNameRev from (
        select distinct value chemicalsn
        from ChemiAutoData
        WHERE data LIKE '%鋅%'
    ) selchem
    LEFT JOIN ChemicalData chem
    ON selchem.chemicalsn = chem.ChemicalSN
    WHERE chem.ChemiChnNameRev LIKE '%鋅%'
) selchem
LEFT JOIN ChemiComMapping map
ON selchem.ChemicalSN = map.ChemicalSN
LEFT JOIN SupplierCustomerInfo sup
ON map.MappingSN = sup.MappingSN
LEFT JOIN ComFacBizSearchInfo com
ON com.AdminNo = map.AdminNo and com.ComFacBizType = map.ComFacBizType
LEFT JOIN DepartmentMapping dept 
ON map.TempTableName = dept.TempTableName

WHERE
    (sup.ProductionQuantity is not null and sup.ProductionQuantity <> '-' and cast(sup.ProductionQuantity as float)>0)
    or (sup.UseageQuantity is not null and sup.UseageQuantity <> '-' and cast(sup.UseageQuantity as float)>0)
    -- and  
    -- DeclareYearS > 108

ORDER BY TempTableName, ChemicalSN, DeclareYearS, DeclareMonthS
-- ) a

-- select top 10 * from ChemiComMapping
-- select * from DepartmentMapping where TempTableName='TSgwRemediationFee'

-- select * from 
select top 10 * from ChemicalData
select top 1000 * from ChemiComMapping 
where MappingSN = 'EPA000013160121163209057274898'

select * from SupplierCustomerInfo where MappingSN = 'EPA000013160121163209057274898'
-- where chemicalsn = 4992
-- order by MappingSN desc

select MappingSN, chemicalsn, count(*) as cnt from chemicommapping 
-- where MappingSN = 'MOTC0000022101082012224324720'
where AdminNo = '15458455'
group by MappingSN, chemicalsn

order by cnt desc