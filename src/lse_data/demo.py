"""Small invented dataset with cancellations, partial fills and carry-over orders."""

import csv
from pathlib import Path

from .schema import COLUMNS, FILES


def sample_rows():
    common = {
        "TICode": "SYNTHETIC001",
        "CountryOfRegister": "GB",
        "CurrencyCode": "GBX",
        "MarketSegmentCode": "DEMO",
        "MessageSequenceNumber": "1",
    }
    order = dict(
        common,
        MarketSectorCode="DEMO",
        ParticipantCode="NULL",
        BuySellInd="B",
        MarketMechanismGroup="O",
        MarketMechanismType="LO",
        Price="105",
        AggregateSize="40",
        SingleFillInd="N",
        BroadcastUpdateAction="A",
        OrderDate="01032007",
        OrderTime="08:00:00.123456",
    )
    orders = [
        dict(order, OrderCode="BUY001"),
        dict(order, OrderCode="SELL001", BuySellInd="S", Price="100"),
        dict(order, OrderCode="MARKET001", Price="0", MarketMechanismType="MO"),
        dict(
            order, OrderCode="CARRY001", BroadcastUpdateAction="F", OrderDate="28022007"
        ),
    ]
    history = dict(
        common,
        OrderCode="BUY001",
        OrderActionType="P",
        MatchingOrderCode="SELL001",
        TradeSize="10",
        TradeCode="TRADE001",
        AggregateSize="30",
        BuySellInd="B",
        MarketMechanismType="LO",
        EventDate="01032007",
        EventTime="09:00:00.123456",
    )
    histories = [
        history,
        dict(
            history,
            OrderActionType="M",
            TradeCode="TRADE002",
            TradeSize="30",
            AggregateSize="0",
        ),
        dict(
            history,
            OrderCode="SELL001",
            BuySellInd="S",
            OrderActionType="M",
            TradeCode="TRADE002",
            TradeSize="30",
            AggregateSize="0",
            MatchingOrderCode="BUY001",
        ),
        dict(
            history,
            OrderCode="MARKET001",
            OrderActionType="M",
            TradeCode="TRADE003",
            TradeSize="5",
            AggregateSize="0",
            MarketMechanismType="MO",
        ),
        dict(
            history,
            OrderCode="CARRY001",
            OrderActionType="T",
            TradeCode="NULL",
            TradeSize="0",
            MatchingOrderCode="NULL",
        ),
    ]
    trade = dict(
        common,
        TradeCode="TRADE001",
        TradePrice="100",
        TradeSize="10",
        TradeDate="01032007",
        TradeTime="09:00:00.123456",
        BroadcastUpdateAction="E",
        TradeTypeInd="AT",
        TradeTimeInd="N",
        BargainConditions="NULL",
        ConvertedPriceInd="N",
        PublicationDate="01032007",
        PublicationTime="09:00:00.123456",
    )
    trades = [
        trade,
        dict(trade, TradeCode="TRADE002", TradePrice="102", TradeSize="30"),
        dict(
            trade,
            TradeCode="TRADE003",
            BroadcastUpdateAction="D",
            PublicationTime="10:00:00",
        ),
        dict(trade, TradeCode="TRADE003", TradePrice="101", TradeSize="5"),
        dict(trade, TradeCode="MANUAL001", TradeTypeInd="O", TradePrice="200"),
        dict(
            trade,
            TradeCode="AUCTION001",
            TradeTypeInd="UT",
            TradePrice="103",
            TradeSize="5",
        ),
        dict(trade, TradeCode="OUTSIDE001", BroadcastUpdateAction="D"),
    ]
    return {"order_detail": orders, "order_history": histories, "trade_report": trades}


def write_demo(directory, rows=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for table, records in (rows or sample_rows()).items():
        path = directory / FILES[table]
        with path.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerows(
                [[row.get(name, "NULL") for name in COLUMNS[table]] for row in records]
            )
