"""Column order follows the supplied 17/15/17-field MIDAS exports."""

FILES = {
    "order_detail": "allGlaxoOrderDetail.CSV",
    "order_history": "allGlaxoOrderHistory.CSV",
    "trade_report": "allGlaxoTradeReport.CSV",
}
COLUMNS = {
    "order_detail": "OrderCode MarketSegmentCode MarketSectorCode TICode CountryOfRegister CurrencyCode ParticipantCode BuySellInd MarketMechanismGroup MarketMechanismType Price AggregateSize SingleFillInd BroadcastUpdateAction OrderDate OrderTime MessageSequenceNumber".split(),
    "order_history": "OrderCode OrderActionType MatchingOrderCode TradeSize TradeCode TICode CountryOfRegister CurrencyCode MarketSegmentCode AggregateSize BuySellInd MarketMechanismType MessageSequenceNumber EventDate EventTime".split(),
    "trade_report": "MessageSequenceNumber TICode MarketSegmentCode CountryOfRegister CurrencyCode TradeCode TradePrice TradeSize TradeDate TradeTime BroadcastUpdateAction TradeTypeInd TradeTimeInd BargainConditions ConvertedPriceInd PublicationDate PublicationTime".split(),
}
LENGTHS = {
    "OrderCode": 10,
    "MarketSegmentCode": 4,
    "MarketSectorCode": 4,
    "TICode": 12,
    "CountryOfRegister": 2,
    "CurrencyCode": 3,
    "ParticipantCode": 11,
    "BuySellInd": 1,
    "MarketMechanismGroup": 1,
    "MarketMechanismType": 2,
    "SingleFillInd": 1,
    "BroadcastUpdateAction": 1,
    "OrderActionType": 1,
    "MatchingOrderCode": 10,
    "TradeCode": 10,
    "TradeTypeInd": 2,
    "TradeTimeInd": 1,
    "BargainConditions": 1,
    "ConvertedPriceInd": 1,
}
NULLABLE = {"ParticipantCode", "MatchingOrderCode", "BargainConditions"}
PRICES = {"Price", "TradePrice"}
INTEGERS = {"AggregateSize", "TradeSize", "MessageSequenceNumber"}


def nullable(table, name):
    return name in NULLABLE or (
        table == "order_history" and name in {"TradeCode", "TradeSize"}
    )
