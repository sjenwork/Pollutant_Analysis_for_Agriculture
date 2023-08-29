select chem.*, map.SourceUnit, dept.DataId, dept.SystemName, map.AdminNo, map.ComFacBizType, com.ComFacBizName, 
sup.DeclareYearS, sup.DeclareMonthS, sup.DeclareSeasonS, 
SUM(TRY_CONVERT(float, sup.QuantityUnit)) as QuantityUnit, 
SUM(TRY_CONVERT(float, sup.QuantityScale)) as QuantityScale, 
SUM(TRY_CONVERT(float, sup.OtherQuantityDesc)) as OtherQuantityDesc, 
SUM(TRY_CONVERT(float, sup.PercentageUnit)) as PercentageUnit, 
SUM(TRY_CONVERT(float, sup.ProductionQuantity)) as ProductionQuantity, 
SUM(TRY_CONVERT(float, sup.ImportQuantity)) as ImportQuantity, 
SUM(TRY_CONVERT(float, sup.PurchaseQuantity)) as PurchaseQuantity, 
SUM(TRY_CONVERT(float, sup.SellingQuantity)) as SellingQuantity, 
SUM(TRY_CONVERT(float, sup.UseageQuantity)) as UseageQuantity,
SUM(TRY_CONVERT(float, sup.StorageQuantity)) as StorageQuantity, 
SUM(TRY_CONVERT(float, sup.StorageQuantityAdd)) as StorageQuantityAdd, 
SUM(TRY_CONVERT(float, sup.StorageQuantitySub)) as StorageQuantitySub, 
SUM(TRY_CONVERT(float, sup.DisposalQuantity)) as DisposalQuantity, 
SUM(TRY_CONVERT(float, sup.RestAmount)) as RestAmount,
SUM(TRY_CONVERT(float, sup.TransportQuantity)) as TransportQuantity, 
SUM(TRY_CONVERT(float, sup.ProductUseQuantity)) as ProductUseQuantity, 
SUM(TRY_CONVERT(float, sup.QtyExport)) as QtyExport, 
SUM(TRY_CONVERT(float, sup.QtyTransAdd)) as QtyTransAdd, 
SUM(TRY_CONVERT(float, sup.QtyTransAdd)) as QtyTransAdd, 
SUM(TRY_CONVERT(float, sup.QtyTransSub)) as QtyTransSub, 
SUM(TRY_CONVERT(float, sup.QtyOtherSub)) as QtyOtherSub,
SUM(TRY_CONVERT(float, sup.ResidualIn)) as ResidualIn,
SUM(TRY_CONVERT(float, sup.ResidualOut)) as ResidualOut

from chemicalData_For_Analysis chem
left join chemicaldata chemall
on chem.chemicalsn = chemall.ChemicalSN
left join ChemiComMapping map
on chem.chemicalSN = map.ChemicalSN
left join DepartmentMapping dept
on dept.TempTableName = map.TempTableName
left join ComFacBizSearchInfo com
on com.AdminNo = map.AdminNo and com.ComFacBizType = map.ComFacBizType
left join SupplierCustomerInfo sup
on sup.MappingSN = map.MappingSN
where 
    TRY_CONVERT(float, ProductionQuantity) >0.0 or 
    TRY_CONVERT(float, ImportQuantity) >0.0 or 
    TRY_CONVERT(float, PurchaseQuantity) >0.0 or 
    TRY_CONVERT(float, SellingQuantity) >0.0 or 
    TRY_CONVERT(float, UseageQuantity) >0.0 or 
    TRY_CONVERT(float, StorageQuantity) >0.0 or 
    TRY_CONVERT(float, StorageQuantityAdd) >0.0 or 
    TRY_CONVERT(float, StorageQuantitySub) >0.0 or 
    TRY_CONVERT(float, DisposalQuantity) >0.0 or 
    TRY_CONVERT(float, RestAmount) >0.0 or 
    TRY_CONVERT(float, TransportQuantity) >0.0 or 
    TRY_CONVERT(float, ProductUseQuantity) >0.0 or 
    TRY_CONVERT(float, QtyExport) >0.0 or 
    TRY_CONVERT(float, QtyTransAdd) >0.0 or 
    TRY_CONVERT(float, QtyTransAdd) >0.0 or 
    TRY_CONVERT(float, QtyTransSub) >0.0 or 
    TRY_CONVERT(float, QtyOtherSub) >0.0 or 
    TRY_CONVERT(float, ResidualIn) >0.0 or 
    TRY_CONVERT(float, ResidualOut)>0.0 
group by chem.chemicalsn, chem.CasNO, chem.ChnName, chem.EngName, map.SourceUnit, dept.DataId, dept.SystemName, map.AdminNo, map.ComFacBizType, com.ComFacBizName, 
sup.DeclareYearS, sup.DeclareMonthS, sup.DeclareSeasonS
order by chem.chemicalsn