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
    MessageSequenceNumber BIGINT NOT NULL,
    INDEX idx_order_time (OrderDate, OrderTime, TICode, MessageSequenceNumber, OrderCode)
) ENGINE=InnoDB;

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
    FOREIGN KEY (OrderCode) REFERENCES order_detail(OrderCode),
    INDEX idx_history_order (OrderCode),
    INDEX idx_history_trade (TradeCode, TICode, CountryOfRegister, CurrencyCode),
    INDEX idx_history_time (EventDate, EventTime, TICode, MessageSequenceNumber, OrderCode, AggregateSize)
) ENGINE=InnoDB;

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
    PublicationTime TIME(6) NOT NULL,
    INDEX idx_trade_identity (TradeCode, TICode, CountryOfRegister, CurrencyCode, BroadcastUpdateAction),
    INDEX idx_trade_time (PublicationDate, PublicationTime, TICode, MessageSequenceNumber),
    INDEX idx_trade_date (TradeDate, TradeTypeInd)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staging_rows (dataset VARCHAR(32) NOT NULL, line_number BIGINT NOT NULL, raw_json TEXT NOT NULL, PRIMARY KEY(dataset, line_number)) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rejected_rows (dataset VARCHAR(32) NOT NULL, line_number BIGINT NOT NULL, reason TEXT NOT NULL, PRIMARY KEY(dataset, line_number)) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS imports (dataset VARCHAR(32) PRIMARY KEY, sha256 VARCHAR(64) NOT NULL, input_rows BIGINT NOT NULL, accepted_rows BIGINT NOT NULL, rejected_rows BIGINT NOT NULL) ENGINE=InnoDB;

CREATE OR REPLACE VIEW active_trades AS
SELECT t.* FROM trade_report t
WHERE t.BroadcastUpdateAction <> 'D'
AND NOT EXISTS (
    SELECT 1 FROM trade_report c
    WHERE c.BroadcastUpdateAction = 'D' AND c.TradeCode = t.TradeCode
      AND c.TICode = t.TICode AND c.CountryOfRegister = t.CountryOfRegister
      AND c.CurrencyCode = t.CurrencyCode
);
