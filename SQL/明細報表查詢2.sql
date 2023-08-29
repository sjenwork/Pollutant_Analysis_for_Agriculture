SELECT T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.TempTableName, 
    T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr, 
    T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev, 
    T2.DeclareYearS, T2.DeclareMonthS, T2.DeclareSeasonS, T2.QuantityUnit, T3.DeptName, T3.SystemName
    -- , 
    -- CAST(SUM(ISNULL(TRY_CAST(T2.RestAmount AS DECIMAL(25, 12)),0)) AS VARCHAR) AS RestAmount 
FROM ChemiComMapping AS T1 
LEFT JOIN SupplierCustomerInfo AS T2 ON T1.MappingSN = T2.MappingSN 
LEFT JOIN DepartmentMapping AS T3 ON T1.TempTableName = T3.TempTableName 
LEFT JOIN ComFacBizMappingInfo AS T4 ON T1.ComFacBizType = T4.ComFacBizType AND T1.AdminNo = T4.AdminNo 
LEFT JOIN ChemicalData AS T5 ON T1.ChemicalSN = T5.ChemicalSN 
WHERE 
    -- T1.ComFacBizType = ? AND T1.AdminNo = ? AND T1.ChemicalSN = ?
    -- T1.ChemicalSN = 4992
    -- AND T1.IsValid = 1
    -- AND 
    CONCAT(T2.DeclareYearS, T2.DeclareSeasonS) >= 1081 AND CONCAT(T2.DeclareYearS, T2.DeclareSeasonS) <= 1104
    AND T1.TempTableName in ('TToxChemiRestAmount','TConcernOperationR') 
    AND CAST(CONCAT(T2.DeclareYearS, T2.DeclareMonthS) AS INT) = 
        (
            SELECT MAX(CAST(CONCAT(S2.DeclareYearS, S2.DeclareMonthS) AS INT)) AS DeclareDate 
            FROM ChemiComMapping AS S1 
            LEFT JOIN SupplierCustomerInfo AS S2 ON S1.MappingSN = S2.MappingSN 
            WHERE S1.TempTableName = T1.TempTableName AND S1.ComFacBizType = T1.ComFacBizType AND S1.AdminNo = T1.AdminNo AND S1.ChemicalSN = T1.ChemicalSN 
            AND S1.TempTableName in ('TToxChemiRestAmount','TConcernOperationR') 
            AND S1.IsValid = 1 
            AND CONCAT(T2.DeclareYearS, T2.DeclareSeasonS) >= 1081 AND CONCAT(T2.DeclareYearS, T2.DeclareSeasonS) <= 1104
            GROUP BY S1.ChemicalSN, S1.ComFacBizType, S1.AdminNo, S1.TempTableName
        ) 
GROUP BY T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.TempTableName, 
    T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr, 
    T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev, 
    T2.DeclareYearS, T2.DeclareMonthS, T2.DeclareSeasonS, T2.QuantityUnit, T3.DeptName, T3.SystemName 
ORDER BY T2.DeclareYearS DESC, T2.DeclareSeasonS DESC, T5.ChemiChnNameRev, T4.ComFacBizName 

select top 10 * from SupplierCustomerInfo
where CONCAT(DeclareYearS, DeclareSeasonS) >= 1081 AND CONCAT(DeclareYearS, DeclareSeasonS) <= 1104

// select * from ChemicalData  
// where CASNo='7440-66-6' and IsMatched=0 and IsValid = 1

// // // // // // // // // // // // // // // // 
SELECT T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.TempTableName, 
    T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr, 
    T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev, 
    T3.DeptName, T3.SystemName, T2.DeclareYearS, T2.DeclareSeasonS, 
    T2.SupplierCustomerType, T2.SCComFacBizType, T2.SCAdminNo, T2.QuantityUnit, 
    CASE T2.SCComFacBizType WHEN '-' THEN '-' ELSE (SELECT ISNULL(ComFacBizAdminNo,ComFacBizFactoryRegNo) FROM ComFacBizSearchInfo WHERE ComFacBizType = T2.SCComFacBizType  AND AdminNo  = T2.SCAdminNo) END AS SCComFacBizAdminNo, 
    CASE T2.SCComFacBizType WHEN '-' THEN '-' ELSE (SELECT ComFacBizName FROM ComFacBizSearchInfo WHERE ComFacBizType = T2.SCComFacBizType  AND AdminNo  = T2.SCAdminNo) END AS SCComFacBizName, 
    CAST(SUM(ISNULL(TRY_CAST(T2.PurchaseQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS PurchaseQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.SellingQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS SellingQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.ProductionQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS ProductionQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.UseageQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS UseageQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.StorageQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS StorageQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.ImportQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS ImportQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.QtyExport AS DECIMAL(25, 12)),0)) AS VARCHAR) AS QtyExport, 
    CAST(SUM(ISNULL(TRY_CAST(T2.QtyTransAdd AS DECIMAL(25, 12)),0)) AS VARCHAR) AS QtyTransAdd, 
    CAST(SUM(ISNULL(TRY_CAST(T2.QtyTransSub AS DECIMAL(25, 12)),0)) AS VARCHAR) AS QtyTransSub, 
    CAST(SUM(ISNULL(TRY_CAST(T2.StorageQuantityAdd AS DECIMAL(25, 12)),0)) AS VARCHAR) AS StorageQuantityAdd, 
    CAST(SUM(ISNULL(TRY_CAST(T2.StorageQuantitySub AS DECIMAL(25, 12)),0)) AS VARCHAR) AS StorageQuantitySub, 
    CAST(SUM(ISNULL(TRY_CAST(T2.DisposalQuantity AS DECIMAL(25, 12)),0)) AS VARCHAR) AS DisposalQuantity, 
    CAST(SUM(ISNULL(TRY_CAST(T2.QtyOtherAdd AS DECIMAL(25, 12)),0)) AS VARCHAR) AS QtyOtherAdd, 
    CAST(SUM(ISNULL(TRY_CAST(T2.QtyOtherSub AS DECIMAL(25, 12)),0)) AS VARCHAR) AS QtyOtherSub, 
    CAST(SUM(ISNULL(TRY_CAST(T2.ResidualIn AS DECIMAL(25, 12)),0)) AS VARCHAR) AS ResidualIn, 
    CAST(SUM(ISNULL(TRY_CAST(T2.ResidualOut AS DECIMAL(25, 12)),0)) AS VARCHAR) AS ResidualOut 
FROM ChemiComMapping AS T1 
LEFT JOIN SupplierCustomerInfo AS T2 ON T1.MappingSN = T2.MappingSN 
LEFT JOIN DepartmentMapping AS T3 ON T1.TempTableName = T3.TempTableName 
LEFT JOIN ComFacBizMappingInfo AS T4 ON T1.ComFacBizType = T4.ComFacBizType AND T1.AdminNo = T4.AdminNo 
LEFT JOIN ChemicalData AS T5 ON T1.ChemicalSN = T5.ChemicalSN 
WHERE 
strShareSql;
strCondiSql;
systemSql;
declareDateSql;
sltIsValidSql;
strCityCmd;
GROUP BY T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.TempTableName, 
T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr, 
T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev, 
T2.DeclareYearS, T2.DeclareSeasonS, T2.SupplierCustomerType, T2.SCComFacBizType, T2.SCAdminNo, T2.QuantityUnit, T3.DeptName, T3.SystemName 
ORDER BY T2.DeclareYearS DESC, T2.DeclareSeasonS DESC 
				