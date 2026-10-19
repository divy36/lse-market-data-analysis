CREATE TABLE IF NOT EXISTS order_detail (
    OrderCode VARCHAR(10) NOT NULL PRIMARY KEY,
    MarketSegmentCode VARCHAR(4) NOT NULL,
    MarketSectorCode VARCHAR(4) NOT NULL,
    TICode VARCHAR(12) NOT NULL,
    CountryOfRegister VARCHAR(2) NOT NULL,
    CurrencyCode VARCHAR(3) NOT NULL,
    ParticipantCode VARCHAR(11),
    BuySellInd VARCHAR(1) NOT NULL,
    MarketMechanismGroup VARCHAR(1) NOT NULL,
    MarketMechanismType VARCHAR(2) NOT NULL,
    Price DECIMAL(18,8) NOT NULL,
    AggregateSize BIGINT NOT NULL,
    SingleFillInd VARCHAR(1) NOT NULL,
    BroadcastUpdateAction VARCHAR(1) NOT NULL,
    OrderDate DATE NOT NULL,
    OrderTime TIME(6) NOT NULL,
    MessageSequenceNumber BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_time ON order_detail (OrderDate, OrderTime, TICode, MessageSequenceNumber, OrderCode);

CREATE TABLE IF NOT EXISTS order_history (
    id BIGINT PRIMARY KEY,
    OrderCode VARCHAR(10) NOT NULL,
    OrderActionType VARCHAR(1) NOT NULL,
    MatchingOrderCode VARCHAR(10),
    TradeSize BIGINT,
    TradeCode VARCHAR(10),
    TICode VARCHAR(12) NOT NULL,
    CountryOfRegister VARCHAR(2) NOT NULL,
    CurrencyCode VARCHAR(3) NOT NULL,
    MarketSegmentCode VARCHAR(4) NOT NULL,
    AggregateSize BIGINT NOT NULL,
    BuySellInd VARCHAR(1) NOT NULL,
    MarketMechanismType VARCHAR(2) NOT NULL,
    MessageSequenceNumber BIGINT NOT NULL,
    EventDate DATE NOT NULL,
    EventTime TIME(6) NOT NULL,
    FOREIGN KEY (OrderCode) REFERENCES order_detail(OrderCode)
);

CREATE INDEX IF NOT EXISTS idx_history_order ON order_history (OrderCode);

CREATE INDEX IF NOT EXISTS idx_history_trade ON order_history (TradeCode, TICode, CountryOfRegister, CurrencyCode);

CREATE INDEX IF NOT EXISTS idx_history_time ON order_history (EventDate, EventTime, TICode, MessageSequenceNumber, OrderCode, AggregateSize);

CREATE TABLE IF NOT EXISTS trade_report (
    id BIGINT PRIMARY KEY,
    MessageSequenceNumber BIGINT NOT NULL,
    TICode VARCHAR(12) NOT NULL,
    MarketSegmentCode VARCHAR(4) NOT NULL,
    CountryOfRegister VARCHAR(2) NOT NULL,
    CurrencyCode VARCHAR(3) NOT NULL,
    TradeCode VARCHAR(10) NOT NULL,
    TradePrice DECIMAL(18,8) NOT NULL,
    TradeSize BIGINT NOT NULL,
    TradeDate DATE NOT NULL,
    TradeTime TIME(6) NOT NULL,
    BroadcastUpdateAction VARCHAR(1) NOT NULL,
    TradeTypeInd VARCHAR(2) NOT NULL,
    TradeTimeInd VARCHAR(1) NOT NULL,
    BargainConditions VARCHAR(1),
    ConvertedPriceInd VARCHAR(1) NOT NULL,
    PublicationDate DATE NOT NULL,
    PublicationTime TIME(6) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_identity ON trade_report (TradeCode, TICode, CountryOfRegister, CurrencyCode, BroadcastUpdateAction);

CREATE INDEX IF NOT EXISTS idx_trade_time ON trade_report (PublicationDate, PublicationTime, TICode, MessageSequenceNumber);

CREATE INDEX IF NOT EXISTS idx_trade_date ON trade_report (TradeDate, TradeTypeInd);

CREATE TABLE IF NOT EXISTS staging_rows (dataset VARCHAR(32) NOT NULL, line_number BIGINT NOT NULL, raw_json TEXT NOT NULL, PRIMARY KEY(dataset, line_number));

CREATE TABLE IF NOT EXISTS rejected_rows (dataset VARCHAR(32) NOT NULL, line_number BIGINT NOT NULL, reason TEXT NOT NULL, PRIMARY KEY(dataset, line_number));

CREATE TABLE IF NOT EXISTS imports (dataset VARCHAR(32) PRIMARY KEY, sha256 VARCHAR(64) NOT NULL, input_rows BIGINT NOT NULL, accepted_rows BIGINT NOT NULL, rejected_rows BIGINT NOT NULL);

CREATE VIEW IF NOT EXISTS active_trades AS
SELECT t.* FROM trade_report t
WHERE t.BroadcastUpdateAction <> 'D'
AND NOT EXISTS (
    SELECT 1 FROM trade_report c
    WHERE c.BroadcastUpdateAction = 'D' AND c.TradeCode = t.TradeCode
      AND c.TICode = t.TICode AND c.CountryOfRegister = t.CountryOfRegister
      AND c.CurrencyCode = t.CurrencyCode
);
