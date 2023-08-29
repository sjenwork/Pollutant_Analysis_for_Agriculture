SELECT '全部' AS SysNM, COUNT(*) AS Cnt, '1' AS Priority, '0' AS SystemSeq 
FROM ( 
    SELECT DISTINCT  S1.ComFacBizType, S1.AdminNo 
    FROM ChemiComMapping AS S1 
    LEFT JOIN ComFacBizSearchInfo AS D1 
    ON S1.ComFacBizType = D1.ComFacBizType AND S1.AdminNo = D1.AdminNo 
    LEFT JOIN SupplierCustomerInfo AS S2 ON S1.MappingSN = S2.MappingSN 
    WHERE ChemicalSN = 35043 AND S1.IsValid = 1 
    ) AS T7 
UNION 
SELECT DISTINCT T3.SysNM, (
    SELECT COUNT(*) 
    FROM ( 
        SELECT DISTINCT T4.ComFacBizType, T4.AdminNo 
        FROM ChemiComMapping AS T4 
        LEFT JOIN DepartmentMapping AS T5 ON T5.TempTableName = T4.TempTableName 
        LEFT JOIN ComFacBizSearchInfo AS D1 ON T4.ComFacBizType = D1.ComFacBizType AND T4.AdminNo = D1.AdminNo 
        LEFT JOIN SupplierCustomerInfo AS TT ON TT.MappingSN = T4.MappingSN 
        WHERE T4.ChemicalSN = 35043 AND T3.SysNM = CONCAT(T5.DeptName, T5.SystemName)  AND T4.IsValid = 1 
    ) AS T6 ) AS Cnt, 
    '2' AS Priority, T3.SystemSeq 
    FROM ( 
        SELECT DISTINCT T1.ComFacBizType, T1.AdminNo, CONCAT(T2.DeptName, T2.SystemName) AS SysNM, T2.SystemSeq, D1.RegularAddr 
        FROM ChemiComMapping AS T1 
        LEFT JOIN DepartmentMapping AS T2 ON T2.TempTableName = T1.TempTableName 
        LEFT JOIN ComFacBizSearchInfo AS D1 ON T1.ComFacBizType = D1.ComFacBizType AND T1.AdminNo = D1.AdminNo 
        LEFT JOIN SupplierCustomerInfo AS TT2 ON TT2.MappingSN = T1.MappingSN WHERE T1.ChemicalSN = 35043 AND T1.IsValid = 1 
        ) AS T3 ORDER BY Priority, SystemSeq

