"""Atomic, chunked imports with raw staging and explicit rejection counts."""

import csv
import hashlib
import json
from pathlib import Path

from .cleaning import normalize
from .schema import COLUMNS, FILES


def ingest(db, directory, batch_size=1000):
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    for table in (*COLUMNS, "imports", "staging_rows", "rejected_rows"):
        if db.execute(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]:
            raise ValueError(
                "Import requires an empty project database; use a new database for another bundle"
            )
    paths = {table: Path(directory) / filename for table, filename in FILES.items()}
    if not all(path.is_file() for path in paths.values()):
        raise ValueError("All three MIDAS CSV files are required")
    parents = {}
    seen_trades = set()
    counts = []
    with db.transaction():
        for table, path in paths.items():
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            accepted, rejected, total = 0, 0, 0
            raw_batch, good_batch, bad_batch = [], [], []
            columns = COLUMNS[table]
            final_columns = columns if table == "order_detail" else ["id", *columns]
            insert = f"INSERT INTO {table} ({','.join(final_columns)}) VALUES ({','.join('?' for _ in final_columns)})"

            def flush():
                db.many("INSERT INTO staging_rows VALUES (?, ?, ?)", raw_batch)
                db.many(insert, good_batch)
                db.many("INSERT INTO rejected_rows VALUES (?, ?, ?)", bad_batch)
                raw_batch.clear()
                good_batch.clear()
                bad_batch.clear()

            with path.open(newline="", encoding="utf-8-sig") as stream:
                for number, fields in enumerate(csv.reader(stream, strict=True), 1):
                    total += 1
                    raw_batch.append((table, number, json.dumps(fields)))
                    try:
                        values = normalize(table, fields)
                        row = dict(zip(columns, values))
                        identity = tuple(
                            row[k]
                            for k in ("TICode", "CountryOfRegister", "CurrencyCode")
                        )
                        if table == "order_detail":
                            if row["OrderCode"] in parents:
                                raise RuntimeError(
                                    "Duplicate OrderCode: overlapping bundles are not supported"
                                )
                            parents[row["OrderCode"]] = (identity, row["BuySellInd"])
                        elif table == "order_history":
                            if parents.get(row["OrderCode"]) != (
                                identity,
                                row["BuySellInd"],
                            ):
                                raise ValueError(
                                    "Missing order detail or mismatched instrument/side"
                                )
                        elif row["BroadcastUpdateAction"] != "D":
                            key = (row["TradeCode"], *identity)
                            if key in seen_trades:
                                raise RuntimeError(
                                    "Ambiguous duplicate non-cancellation TradeCode"
                                )
                            seen_trades.add(key)
                        good_batch.append(
                            values if table == "order_detail" else [number, *values]
                        )
                        accepted += 1
                    except ValueError as exc:
                        rejected += 1
                        bad_batch.append((table, number, str(exc)))
                    if len(raw_batch) >= batch_size:
                        flush()
            flush()
            row = {
                "dataset": table,
                "sha256": digest.hexdigest(),
                "input_rows": total,
                "accepted_rows": accepted,
                "rejected_rows": rejected,
            }
            db.execute(
                "INSERT INTO imports VALUES (?, ?, ?, ?, ?)", tuple(row.values())
            )
            counts.append(row)
    return counts
