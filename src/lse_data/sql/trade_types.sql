SELECT TICode, CountryOfRegister, CurrencyCode, TradeTypeInd,
       COUNT(*) AS TradeCount, SUM(TradeSize) AS TotalVolume,
       1.0 * SUM(TradePrice * TradeSize) / NULLIF(SUM(TradeSize), 0) AS VWAP
FROM active_trades
WHERE TradePrice > 0 AND TradeSize > 0
GROUP BY TICode, CountryOfRegister, CurrencyCode, TradeTypeInd
ORDER BY TICode, CountryOfRegister, CurrencyCode, TradeTypeInd;
