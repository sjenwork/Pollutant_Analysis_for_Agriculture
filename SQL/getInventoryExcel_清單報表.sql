SELECT T6.CASNo, T6.ChemiChnNameRev, T6.ChemiEngNameRev, T7.ComFacBizAdminNo, 
    T7.ComFacBizFactoryRegNo, T7.ComFacBizName, T7.ComFacBizBusinessName, T7.BusinessItem, 
    T7.ZipCode, T7.County, T7.RegularAddr, T5.DeptName, T5.SystemName, T5.HasDeclareDate,
    (CASE T5.ComFacBizType 
        WHEN '0' THEN 'B' 
        WHEN '1' THEN 'A' 
        WHEN '2' THEN 'C' 
        WHEN '3' THEN 'D' 
    END ) AS Priority, T5.ComFacBizType, T5.AdminNo, T5.ChemicalChnName,T5.ChemicalEngName 
FROM (
    SELECT T3.ChemicalSN, T3.ComFacBizType, T3.AdminNo, MAX(T3.HasDeclareDate) AS HasDeclareDate, 
        T3.DeptName, T3.SystemName, T3.OldChemicalSN, T4.ChemicalChnName, T4.ChemicalEngName 
    FROM ( 
        SELECT DISTINCT T1.ChemicalSN, T1.ComFacBizType, T1.AdminNo, T1.OldChemicalSN, T2.DeptName, 
            T2.SystemName, 'T' AS HasDeclareDate 
        FROM ChemiComMapping T1 LEFT JOIN SupplierCustomerInfo TT ON TT.MappingSN = T1.MappingSN 
        LEFT JOIN DepartmentMapping T2 ON T1.TempTableName = T2.TempTableName 
        WHERE 
        -- strShareSql + 
        T1.IsValid = 1 AND
        -- strWhereSql + 
        -- (TT.DeclareYearS >= ? AND  TT.DeclareYearS <= ?) 
        T1.ChemicalSN=4992
    UNION 
    SELECT DISTINCT C1.ChemicalSN, C1.ComFacBizType, C1.AdminNo, C1.OldChemicalSN, C3.DeptName, 
        C3.SystemName, 'F' AS HasDeclareDate 
    FROM ChemiComMapping C1 
    LEFT JOIN SupplierCustomerInfo C2 ON C1.MappingSN = C2.MappingSN 
    LEFT JOIN DepartmentMapping C3 ON C1.TempTableName = C3.TempTableName 
    WHERE 
    -- strShareSql3 + 
    C1.IsValid = 1 AND
    C1.ChemicalSN = 4992
    AND (C2.DeclareYearS IS NULL OR C2.DeclareYearS ='-') 
    -- strWhereSql3 
    ) T3 
    LEFT JOIN ChemicalData T4 
    on (T3.OldChemicalSN is null AND T3.ChemicalSN=T4.ChemicalSN) 
    or (T3.OldChemicalSN is not null AND T3.OldChemicalSN=T4.ChemicalSN) 
GROUP BY T3.ChemicalSN, T3.ComFacBizType, T3.AdminNo, T3.DeptName, T3.SystemName,T3.OldChemicalSN,T4.ChemicalChnName, T4.ChemicalEngName) T5 
INNER JOIN ChemicalData T6 
    ON T5.ChemicalSN = T6.ChemicalSN 
INNER JOIN ComFacBizMappingInfo T7 
    ON T5.ComFacBizType = T7.ComFacBizType AND T5.AdminNo = T7.AdminNo  
-- strCityCmd
ORDER BY T5.HasDeclareDate DESC, Priority, T7.ComFacBizName;