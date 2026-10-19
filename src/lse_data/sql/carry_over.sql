SELECT TICode, CountryOfRegister, CurrencyCode, BroadcastUpdateAction,
       COUNT(*) AS OrderCount, AVG(AggregateSize) AS AvgRemainingSize
FROM order_detail
GROUP BY TICode, CountryOfRegister, CurrencyCode, BroadcastUpdateAction
ORDER BY TICode, CountryOfRegister, CurrencyCode, BroadcastUpdateAction;
