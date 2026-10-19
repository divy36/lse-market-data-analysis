SELECT od.OrderCode, od.BuySellInd AS Side, od.MarketMechanismType AS OrderType,
       od.Price AS LimitPrice, oh.OrderActionType AS Outcome, oh.TradeSize,
       tr.TradePrice AS ExecutionPrice,
       CASE WHEN od.BuySellInd = 'B' THEN tr.TradePrice - od.Price
            ELSE od.Price - tr.TradePrice END AS ExecutionVsLimit,
       tr.TradeDate, tr.TradeTime, tr.TICode, tr.CurrencyCode,
       oh.MessageSequenceNumber, oh.id AS HistoryRow
FROM order_detail od
JOIN order_history oh ON od.OrderCode = oh.OrderCode
JOIN active_trades tr ON oh.TradeCode = tr.TradeCode
    AND oh.TICode = tr.TICode AND oh.CountryOfRegister = tr.CountryOfRegister
    AND oh.CurrencyCode = tr.CurrencyCode
WHERE oh.OrderActionType IN ('M', 'P') AND tr.TradeTypeInd IN ('AT', 'UT')
    AND od.Price > 0 AND tr.TradePrice > 0 AND tr.TradeSize > 0
ORDER BY tr.TradeDate, tr.TradeTime, tr.TICode, tr.MessageSequenceNumber,
         od.OrderCode, oh.AggregateSize DESC, oh.id;
