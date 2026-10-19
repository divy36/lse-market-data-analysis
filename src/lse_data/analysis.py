"""Named SQL reports and relational audits."""

import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
from importlib.resources import files
import json
from pathlib import Path

REPORTS = (
    "daily_vwap",
    "trade_types",
    "order_events",
    "order_sides",
    "carry_over",
    "lifecycle",
)


def report(db, name):
    if name not in REPORTS:
        raise ValueError("Unknown report")
    query = files("lse_data").joinpath("sql", f"{name}.sql").read_text()
    return db.execute(query)


def audit(db):
    def count(query):
        return db.execute(query)[0]["n"]

    match = "c.TradeCode=t.TradeCode AND c.TICode=t.TICode AND c.CountryOfRegister=t.CountryOfRegister AND c.CurrencyCode=t.CurrencyCode"
    return {
        "rows": {
            t: count(f"SELECT COUNT(*) AS n FROM {t}")
            for t in ("order_detail", "order_history", "trade_report")
        },
        "cancellation_messages": count(
            "SELECT COUNT(*) AS n FROM trade_report WHERE BroadcastUpdateAction='D'"
        ),
        "cancelled_originals": count(
            f"SELECT COUNT(*) AS n FROM trade_report t WHERE t.BroadcastUpdateAction<>'D' AND EXISTS (SELECT 1 FROM trade_report c WHERE c.BroadcastUpdateAction='D' AND {match})"
        ),
        "unmatched_cancellations": count(
            f"SELECT COUNT(*) AS n FROM trade_report c WHERE c.BroadcastUpdateAction='D' AND NOT EXISTS (SELECT 1 FROM trade_report t WHERE t.BroadcastUpdateAction<>'D' AND {match})"
        ),
        "active_trades": count("SELECT COUNT(*) AS n FROM active_trades"),
        "orphan_history": count(
            "SELECT COUNT(*) AS n FROM order_history h LEFT JOIN order_detail d ON h.OrderCode=d.OrderCode WHERE d.OrderCode IS NULL"
        ),
        "missing_matching_orders": count(
            "SELECT COUNT(*) AS n FROM order_history h LEFT JOIN order_detail d ON h.MatchingOrderCode=d.OrderCode WHERE h.MatchingOrderCode IS NOT NULL AND d.OrderCode IS NULL"
        ),
        "execution_events_without_trade_report": count(
            "SELECT COUNT(*) AS n FROM order_history h WHERE h.OrderActionType IN ('M','P') AND NOT EXISTS (SELECT 1 FROM trade_report t WHERE t.TradeCode=h.TradeCode AND t.TICode=h.TICode AND t.CountryOfRegister=h.CountryOfRegister AND t.CurrencyCode=h.CurrencyCode AND t.BroadcastUpdateAction<>'D')"
        ),
        "active_nonpositive_price_or_size": count(
            "SELECT COUNT(*) AS n FROM active_trades WHERE TradePrice<=0 OR TradeSize<=0"
        ),
        "imports": db.execute("SELECT * FROM imports ORDER BY dataset"),
    }


def serial(value):
    if isinstance(value, (Decimal, date, datetime, timedelta)):
        return str(value)
    raise TypeError(f"Unsupported output type: {type(value)}")


def export_reports(db, output, include_lifecycle=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary = audit(db)
    (output / "audit.json").write_text(
        json.dumps(summary, indent=2, default=serial) + "\n"
    )
    for name in REPORTS:
        if name == "lifecycle" and not include_lifecycle:
            continue
        rows = report(db, name)
        with (output / f"{name}.csv").open("w", newline="") as stream:
            if rows:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    return summary


def order_timeline(db, order_code):
    return db.execute(
        """
        SELECT OrderCode, TICode, CountryOfRegister, OrderDate AS EventDate,
               OrderTime AS EventTime, MessageSequenceNumber,
               0 AS RecordRank, BroadcastUpdateAction AS Action,
               AggregateSize, NULL AS TradeCode, 0 AS SourceRow
        FROM order_detail WHERE OrderCode = ?
        UNION ALL
        SELECT OrderCode, TICode, CountryOfRegister, EventDate,
               EventTime, MessageSequenceNumber,
               1 AS RecordRank, OrderActionType AS Action,
               AggregateSize, TradeCode, id AS SourceRow
        FROM order_history WHERE OrderCode = ?
        ORDER BY EventDate, EventTime, TICode, CountryOfRegister,
                 MessageSequenceNumber, OrderCode, RecordRank,
                 AggregateSize DESC, SourceRow
    """,
        (order_code, order_code),
    )
