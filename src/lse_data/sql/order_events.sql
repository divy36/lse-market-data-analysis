SELECT OrderActionType,
       CASE OrderActionType WHEN 'D' THEN 'Deletion' WHEN 'E' THEN 'Expiry'
            WHEN 'P' THEN 'Partial Match' WHEN 'M' THEN 'Full Match'
            WHEN 'T' THEN 'Transaction Limit' ELSE 'Unknown' END AS Description,
       COUNT(*) AS EventCount
FROM order_history
GROUP BY OrderActionType
ORDER BY OrderActionType;
