"""Compare SQL metrics with an independent Decimal calculation on local raw data."""

import argparse
import csv
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

from lse_data.analysis import audit, report
from lse_data.database import connect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with (args.data_dir / "allGlaxoTradeReport.CSV").open(newline="") as stream:
        rows = [[x.strip() for x in r] for r in csv.reader(stream)]

    def identity(r):
        return r[5], r[1], r[3], r[4]

    cancelled = {identity(r) for r in rows if r[10] == "D"}
    originals = {identity(r) for r in rows if r[10] != "D"}
    groups = defaultdict(lambda: [0, Decimal(0), Decimal(0)])
    active = 0
    for row in rows:
        if row[10] == "D" or identity(row) in cancelled:
            continue
        active += 1
        if row[11] != "AT":
            continue
        price, size = Decimal(row[6]), Decimal(row[7])
        if price <= 0 or size <= 0:
            continue
        date = f"{row[8][4:8]}-{row[8][2:4]}-{row[8][0:2]}"
        key = row[1], row[3], row[4], date
        groups[key][0] += 1
        groups[key][1] += size
        groups[key][2] += price * size
    with connect(args.db) as db:
        summary = audit(db)
        actual = report(db, "daily_vwap")
        assert summary["active_trades"] == active
        assert summary["cancelled_originals"] == sum(
            r[10] != "D" and identity(r) in cancelled for r in rows
        )
        assert summary["unmatched_cancellations"] == sum(
            r[10] == "D" and identity(r) not in originals for r in rows
        )
        assert len(actual) == len(groups)
        errors = []
        for row in actual:
            key = tuple(
                str(row[x])
                for x in ("TICode", "CountryOfRegister", "CurrencyCode", "TradeDate")
            )
            count, volume, value = groups[key]
            assert row["NumTrades"] == count
            assert Decimal(str(row["TotalVolume"])) == volume
            errors.append(abs(Decimal(str(row["VWAP"])) - value / volume))
        maximum = max(errors, default=Decimal(0))
        assert maximum < Decimal("0.000001")
    result = {
        "engine": "SQLite " + sqlite3.sqlite_version,
        "reference": "Python Decimal from raw CSV",
        "daily_vwap_groups_checked": len(groups),
        "max_vwap_absolute_error": str(maximum),
        "cancellation_counts_match": True,
        "active_trades": active,
        "accepted_rows": sum(summary["rows"].values()),
        "rejected_rows": sum(r["rejected_rows"] for r in summary["imports"]),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
