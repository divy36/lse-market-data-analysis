import csv
from decimal import Decimal
import os

import pytest

from lse_data.analysis import audit, export_reports, report
from lse_data.cleaning import normalize
from lse_data.database import connect
from lse_data.demo import sample_rows, write_demo
from lse_data.ingest import ingest
from lse_data.schema import COLUMNS, FILES


@pytest.fixture
def db():
    with connect() as database:
        database.initialize()
        yield database


def load_demo(db, tmp_path, rows=None):
    write_demo(tmp_path, rows)
    return ingest(db, tmp_path, batch_size=2)


def assert_reports(db):
    summary = audit(db)
    assert summary["rows"] == {"order_detail": 4, "order_history": 5, "trade_report": 7}
    assert summary["cancellation_messages"] == 2
    assert summary["cancelled_originals"] == 1
    assert summary["unmatched_cancellations"] == 1
    assert summary["active_trades"] == 4
    assert summary["orphan_history"] == 0
    vwap = report(db, "daily_vwap")[0]
    assert Decimal(str(vwap["VWAP"])) == Decimal("101.5")
    assert vwap["TotalVolume"] == 40
    assert vwap["NumTrades"] == 2
    types = {r["TradeTypeInd"]: r for r in report(db, "trade_types")}
    assert types["AT"]["TradeCount"] == 2
    assert "UT" in types
    lifecycle = report(db, "lifecycle")
    assert len(lifecycle) == 3
    assert sorted(float(r["ExecutionVsLimit"]) for r in lifecycle) == [-5, -3, -2]
    assert any(r["Outcome"] == "P" for r in lifecycle)
    assert str(
        db.execute("SELECT OrderTime FROM order_detail WHERE OrderCode='BUY001'")[0][
            "OrderTime"
        ]
    ).endswith("123456")
    assert any(
        r["Description"] == "Transaction Limit" for r in report(db, "order_events")
    )


def test_end_to_end(db, tmp_path):
    load_demo(db, tmp_path)
    assert_reports(db)
    export_reports(db, tmp_path / "reports", include_lifecycle=True)
    assert (tmp_path / "reports" / "audit.json").is_file()
    assert (tmp_path / "reports" / "daily_vwap.csv").is_file()
    assert db.execute("SELECT COUNT(*) AS n FROM staging_rows")[0]["n"] == 16


def test_rerun_does_not_duplicate(db, tmp_path):
    load_demo(db, tmp_path)
    with pytest.raises(ValueError, match="empty"):
        ingest(db, tmp_path)
    assert audit(db)["rows"]["trade_report"] == 7


def test_bad_rows_quarantined_and_reconciled(db, tmp_path):
    rows = sample_rows()
    rows["order_detail"].append(
        dict(rows["order_detail"][0], OrderCode="INVALID", Price="NaN")
    )
    rows["order_history"].append(dict(rows["order_history"][0], OrderCode="MISSING"))
    result = load_demo(db, tmp_path, rows)
    assert sum(r["rejected_rows"] for r in result) == 2
    assert all(
        r["input_rows"] == r["accepted_rows"] + r["rejected_rows"] for r in result
    )
    assert db.execute("SELECT COUNT(*) AS n FROM rejected_rows")[0]["n"] == 2


def test_transaction_rolls_back_all_tables(db, tmp_path):
    rows = sample_rows()
    rows["trade_report"].append(rows["trade_report"][0])
    write_demo(tmp_path, rows)
    with pytest.raises(RuntimeError, match="duplicate"):
        ingest(db, tmp_path, batch_size=1)
    for name in (
        "order_detail",
        "order_history",
        "trade_report",
        "imports",
        "staging_rows",
    ):
        assert db.execute(f"SELECT COUNT(*) AS n FROM {name}")[0]["n"] == 0


def test_cancellation_scoped_to_instrument(db, tmp_path):
    rows = sample_rows()
    rows["trade_report"].append(
        dict(rows["trade_report"][0], TICode="SYNTHETIC002", BroadcastUpdateAction="D")
    )
    load_demo(db, tmp_path, rows)
    assert report(db, "daily_vwap")[0]["NumTrades"] == 2
    assert audit(db)["unmatched_cancellations"] == 2


def test_zero_size_omitted_from_vwap(db, tmp_path):
    rows = sample_rows()
    rows["trade_report"].append(
        dict(
            rows["trade_report"][0],
            TradeCode="ZEROSIZE",
            TradeSize="0",
            TradePrice="999",
        )
    )
    load_demo(db, tmp_path, rows)
    assert report(db, "daily_vwap")[0]["DayHigh"] == 102
    assert audit(db)["active_nonpositive_price_or_size"] == 1


def test_nulls_whitespace_and_decimal():
    row = dict(
        sample_rows()["order_detail"][0], ParticipantCode=" NULL ", Price="105.12345678"
    )
    normalized = dict(
        zip(
            COLUMNS["order_detail"],
            normalize("order_detail", [row[n] for n in COLUMNS["order_detail"]]),
        )
    )
    assert normalized["ParticipantCode"] is None
    assert normalized["Price"] == "105.12345678"
    assert normalized["OrderDate"] == "2007-03-01"


@pytest.mark.parametrize(
    "field,value",
    [
        ("Price", "Infinity"),
        ("Price", "-1"),
        ("Price", "0.000000001"),
        ("OrderDate", "31022007"),
        ("OrderTime", "25:00:00"),
        ("AggregateSize", "1.5"),
        ("BuySellInd", "X"),
        ("OrderCode", "TOO_LONG_ORDER"),
        ("MessageSequenceNumber", "9223372036854775808"),
    ],
)
def test_invalid_fields(field, value):
    row = dict(sample_rows()["order_detail"][0], **{field: value})
    with pytest.raises(ValueError):
        normalize("order_detail", [row[n] for n in COLUMNS["order_detail"]])


def test_missing_file_and_unknown_report(db, tmp_path):
    with pytest.raises(ValueError):
        ingest(db, tmp_path)
    with pytest.raises(ValueError):
        report(db, "trade_report; DROP TABLE order_detail")


@pytest.mark.skipif(
    os.getenv("LSE_TEST_MYSQL") != "1",
    reason="Requires a dedicated MySQL test database",
)
def test_mysql_pipeline(tmp_path):
    with connect(mysql=True) as db:
        db.initialize()
        load_demo(db, tmp_path)
        assert_reports(db)
        with pytest.raises(ValueError, match="empty"):
            ingest(db, tmp_path)


def test_full_order_timeline_and_parameter_binding(db, tmp_path):
    from lse_data.analysis import order_timeline

    load_demo(db, tmp_path)
    timeline = order_timeline(db, "BUY001")
    assert [r["Action"] for r in timeline] == ["A", "P", "M"]
    assert [r["AggregateSize"] for r in timeline] == [40, 30, 0]
    assert order_timeline(db, "' OR 1=1 --") == []
    assert [r["Action"] for r in order_timeline(db, "CARRY001")] == ["F", "T"]


def test_missing_required_field_and_wrong_width():
    with pytest.raises(ValueError):
        normalize("order_detail", ["incomplete"])
    row = dict(sample_rows()["order_detail"][0], TICode="NULL")
    with pytest.raises(ValueError):
        normalize("order_detail", [row[n] for n in COLUMNS["order_detail"]])
