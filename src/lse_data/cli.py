"""Load a local MIDAS bundle and export its analytical reports."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .analysis import export_reports, serial
from .database import connect
from .demo import write_demo
from .ingest import ingest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "load", "report"):
        command = sub.add_parser(name)
        command.add_argument("--db", type=Path, default=Path("output/market.sqlite"))
        command.add_argument(
            "--mysql", action="store_true", help="Use LSE_DB_* environment settings"
        )
        command.add_argument("--output", type=Path, default=Path("output/reports"))
        command.add_argument(
            "--include-lifecycle",
            action="store_true",
            help="Also export individual order execution rows",
        )
        if name == "load":
            command.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.mysql:
        if args.command == "report" and not args.db.is_file():
            parser.error("Database does not exist; run load or demo first")
        args.db.parent.mkdir(parents=True, exist_ok=True)
    with connect(args.db, mysql=args.mysql) as db:
        if args.command != "report":
            db.initialize()
            if args.command == "demo":
                with TemporaryDirectory() as directory:
                    write_demo(directory)
                    ingest(db, directory)
            else:
                ingest(db, args.data_dir)
        summary = export_reports(db, args.output, args.include_lifecycle)
        print(json.dumps(summary, indent=2, default=serial))


if __name__ == "__main__":
    main()
