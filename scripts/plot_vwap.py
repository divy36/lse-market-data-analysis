"""Plot saved aggregate VWAP and daily execution-price range."""

import argparse
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/daily_vwap.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/vwap.png"))
    args = parser.parse_args()
    with args.input.open() as stream:
        rows = list(csv.DictReader(stream))
    identities = {
        (r["TICode"], r["CountryOfRegister"], r["CurrencyCode"]) for r in rows
    }
    if len(identities) != 1:
        raise ValueError("Plot requires one nonempty instrument/currency series")
    rows.sort(key=lambda r: r["TradeDate"])
    dates = [datetime.fromisoformat(r["TradeDate"]) for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    ax.fill_between(
        dates,
        [float(r["DayLow"]) for r in rows],
        [float(r["DayHigh"]) for r in rows],
        alpha=0.18,
        color="#2563eb",
        label="Execution-price range",
    )
    ax.plot(
        dates,
        [float(r["VWAP"]) for r in rows],
        color="#2563eb",
        linewidth=2,
        marker=".",
        label="Daily VWAP",
    )
    ax.set_title("LSE automatic trades · daily VWAP")
    ax.set_ylabel("Price (" + rows[0]["CurrencyCode"] + ")")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    ax.tick_params(axis="x", labelrotation=25)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
