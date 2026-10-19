# Validation

Full local replay on 19 October 2026, using SQLite 3.54.0:

| Table | Input / accepted rows | Rejected |
| --- | ---: | ---: |
| Order detail | 274,322 | 0 |
| Order history | 322,208 | 0 |
| Trade report | 130,136 | 0 |
| Total | 726,666 | 0 |

- 367 cancellation messages: 338 match original trades; 29 have no original in the bundle.
- 129,431 remaining trade reports after excluding cancellations and cancelled originals.
- Zero orphaned parent-order history records; zero execution events without a trade report.
- 89,542 history events reference a matching order absent from order detail. These are event counts, not distinct missing orders; they are retained and reported as a feed-coverage limitation.
- 113,784 linked limit-order execution events checked for side-aware price differences: 46,865 partial and 66,919 full matches.
- 22 daily automatic-trade VWAPs independently recomputed from raw CSV using Decimal. Maximum absolute error: 1.316e-13 GBX.

The notebook's automatic-trade VWAP already excluded cancellations. Its trade-type and active-trade summaries did not apply that rule consistently. Correcting those reports removes 338 cancelled originals; it does not change this sample's `AT` VWAP.

`results/audit.json` contains source SHA-256 hashes and reconciled row counts. `results/validation.json` records the independent checks. Detailed order-level exports and raw source files are excluded from the repository.

## Reproduce the reference check

```bash
python scripts/verify_reference.py --data-dir /path/to/csv-files \
  --db output/market.sqlite --output output/reference.json
```

Local tests cover cancellation matching and scope, partial/full execution joins, side-aware limit differences, exact sample VWAP, fractional times, data rejection, atomic rollback, repeat-import protection and bound order-code queries. GitHub CI runs Python 3.11/3.12 and a dedicated MySQL 8 integration job with invented data.

The full historical replay is SQLite-based. MySQL integration checks use the synthetic fixture; the historical files are not uploaded to CI.

To regenerate the chart, install `.[plots]` and run `python scripts/plot_vwap.py`.
