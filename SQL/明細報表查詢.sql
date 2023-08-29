--  DataSearchDetailRepository //


-- 毒化物系統要先加結餘量

SELECT T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.TempTableName, 
    T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr, 
    T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev, 
    T3.DeptName, T3.SystemName, T2.DeclareYearS, T2.DeclareSeasonS, T2.DeclareMonthS,
    T2.QuantityUnit
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


-- //組核心SQL用
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
-- strShareSql
T1.ChemicalSN = 4992
-- systemSql
-- AND CONCAT(T2.DeclareYearS, T2.DeclareSeasonS) > 108 
-- AND CONCAT(T2.DeclareYearS, T2.DeclareSeasonS) <= 109
-- declareDateSql
-- sltIsValidSql
AND T1.IsValid = 1
-- strCityCmd
GROUP BY T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.TempTableName, 
T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr, 
T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev, 
T2.DeclareYearS, T2.DeclareSeasonS, T2.SupplierCustomerType, T2.SCComFacBizType, T2.SCAdminNo, T2.QuantityUnit, T3.DeptName, T3.SystemName 
ORDER BY T2.DeclareYearS DESC, T2.DeclareSeasonS DESC 

-- 特例運作

-- SELECT DISTINCT T3.DeptName, T3.SystemName
SELECT DISTINCT T1.TempTableName, T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T3.DeptName, T3.SystemName,  
    T4.ComFacBizAdminNo, T4.ComFacBizFactoryRegNo, T4.ComFacBizName, T4.ComFacBizBusinessName, T4.BusinessItem, T4.ZipCode, T4.County, T4.RegularAddr,  
    T5.CASNo, T5.ChemiChnNameRev, T5.ChemiEngNameRev  
FROM ChemiComMapping AS T1  
LEFT JOIN DepartmentMapping AS T3 ON T1.TempTableName = T3.TempTableName  
LEFT JOIN ComFacBizMappingInfo AS T4 ON T1.ComFacBizType = T4.ComFacBizType AND T1.AdminNo = T4.AdminNo  
LEFT JOIN ChemicalData AS T5 ON T1.ChemicalSN = T5.ChemicalSN  
WHERE   
-- strShareSql  
T1.ChemicalSN = 4992
-- systemSql
AND 
T1.IsValid = 1
    -- strCityCmd 
AND EXISTS (SELECT * FROM OperationAmtField AS S1 WHERE S1.TempTableName = T1.TempTableName)


-- tagCount
-- 內政部消防署	消防安全檢查列管系統
-- 桃園市政府消防局	消防安全檢查列管系統
-- 國家科學及技術委員會中部科學園區管理局	化學品自主申報平台
-- 國家科學及技術委員會南部科學園區管理局	化學品自主申報平台
-- 國家科學及技術委員會新竹科學園區管理局	化學品自主申報平台
-- 勞動部職業安全衛生署	化學品報備與許可平台(優先管理化學品)
-- 新北市政府消防局	消防安全檢查列管系統
-- 臺中市政府消防局	消防安全檢查列管系統
-- 臺北市政府消防局	消防安全檢查列管系統
-- 臺灣港務股份有限公司	危險品申報系統
-- 衛生福利部食品藥物管理署食品組	食品追溯追蹤管理資訊系統
-- 環境保護署土壤及地下水污染整治基金管理會	土壤及地下水資訊管理系統
-- 環境保護署毒物及化學物質局	801通關簽審資料
-- 環境保護署毒物及化學物質局	環境用藥紀錄流向資訊
-- 環境保護署毒物及化學物質局	環境用藥管理資訊系統


SELECT COUNT(*) as size FROM (  
SELECT DISTINCT T1.EnglishField, T1.ChineseField, T1.Type, T1.Seq FROM OperationAmtField AS T1
INNER JOIN DepartmentMapping AS T2 ON T1.TempTableName = T2.TempTableName   
WHERE T2.DeptName + T2.SystemName = '勞動部職業安全衛生署化學品報備與許可平台(優先管理化學品)' ) Final


SELECT DISTINCT T1.TargetTable, T1.EnglishField, T1.ChineseField, T1.Type, T1.Seq, 
    (
        SELECT TOP 1 T1.TempTableName 
        FROM OperationAmtField AS T1 
        INNER JOIN DepartmentMapping AS T2 ON T1.TempTableName = T2.TempTableName 
        WHERE T2.DeptName + T2.SystemName = '國家科學及技術委員會中部科學園區管理局化學品自主申報平台'
    ) AS TempTableName 
FROM OperationAmtField AS T1 
INNER JOIN DepartmentMapping AS T2 ON T1.TempTableName = T2.TempTableName  
WHERE T2.DeptName + T2.SystemName = '國家科學及技術委員會中部科學園區管理局化學品自主申報平台' 
ORDER BY T1.Seq

-- 

SELECT T1.TempTableName ,
T3.DeptName,
T3.SystemName,
T2.DeclareYearS,
T2.DeclareSeasonS,
T2.Chem_TYPE,
T2.Chem_Proportion,
T2.Chem_Sloc,
T2.Chem_Uloc,
CAST(SUM( CASE isNumeric(T2.Chem_UMaxQ ) WHEN 1 THEN TRY_CAST(REPLACE(T2.Chem_UMaxQ  , ',', '') AS DECIMAL(25, 12)) ELSE 0 END) AS VARCHAR) AS Chem_UMaxQ,
CAST(SUM( CASE isNumeric(T2.Chem_SOfnQ ) WHEN 1 THEN TRY_CAST(REPLACE(T2.Chem_SOfnQ  , ',', '') AS DECIMAL(25, 12)) ELSE 0 END) AS VARCHAR) AS Chem_SOfnQ,
CAST(SUM( CASE isNumeric(T2.Chem_UOfnQ ) WHEN 1 THEN TRY_CAST(REPLACE(T2.Chem_UOfnQ  , ',', '') AS DECIMAL(25, 12)) ELSE 0 END) AS VARCHAR) AS Chem_UOfnQ
FROM ChemiComMapping AS T1 
INNER JOIN MOSTSupplierCustomerInfo AS T2 ON T1.MappingSN = T2.MappingSN 
INNER JOIN DepartmentMapping AS T3 ON T1.TempTableName = T3.TempTableName 
WHERE T1.ComFacBizType = 0 AND T1.AdminNo = 23019109 AND T1.ChemicalSN = 4992
AND T3.DeptName + T3.SystemName = '國家科學及技術委員會中部科學園區管理局化學品自主申報平台' AND T2.SupplierCustomerType = '0' 
GROUP BY T1.TempTableName ,T3.DeptName, T3.SystemName, T2.DeclareYearS, T2.DeclareSeasonS, T2.Chem_TYPE, T2.Chem_Proportion, T2.Chem_Sloc, T2.Chem_Uloc