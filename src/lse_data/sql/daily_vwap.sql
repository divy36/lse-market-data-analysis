SELECT TICode, CountryOfRegister, CurrencyCode, TradeDate,
       COUNT(*) AS NumTrades, SUM(TradeSize) AS TotalVolume,
       1.0 * SUM(TradePrice * TradeSize) / NULLIF(SUM(TradeSize), 0) AS VWAP,
       MIN(TradePrice) AS DayLow, MAX(TradePrice) AS DayHigh
FROM active_trades
WHERE TradeTypeInd = 'AT' AND TradePrice > 0 AND TradeSize > 0
GROUP BY TICode, CountryOfRegister, CurrencyCode, TradeDate
ORDER BY TICode, CountryOfRegister, CurrencyCode, TradeDate;
