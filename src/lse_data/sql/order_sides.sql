SELECT TICode, CountryOfRegister, CurrencyCode, BuySellInd, MarketMechanismType,
       COUNT(*) AS OrderCount, AVG(Price) AS AvgLimitPrice, SUM(AggregateSize) AS TotalSize
FROM order_detail
WHERE Price > 0
GROUP BY TICode, CountryOfRegister, CurrencyCode, BuySellInd, MarketMechanismType
ORDER BY TICode, CountryOfRegister, CurrencyCode, BuySellInd, MarketMechanismType;
