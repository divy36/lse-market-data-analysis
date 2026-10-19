# Database guide

## MySQL

Use a dedicated empty MySQL 8 database. Install the optional driver:

```bash
python -m pip install -e '.[mysql]'
```

Set `LSE_DB_HOST`, `LSE_DB_PORT` (default 3306), `LSE_DB_USER`, `LSE_DB_PASSWORD` and `LSE_DB_NAME` in your environment. The account needs access only to the project database, including table/view creation and inserts.

```bash
lse-data load --mysql --data-dir /path/to/csv-files --output output/mysql
lse-data report --mysql --output output/mysql
```

Schema DDL lives in `src/lse_data/sql/schema_mysql.sql`. MySQL stores prices as DECIMAL(18,8), times as TIME(6), and sequence/size fields as BIGINT. Data inserts use bound parameters. No server-wide settings or `LOCAL INFILE` changes are required.

## Import behavior

1. Create missing tables and views.
2. Refuse imports into a nonempty project database.
3. Hash each source file and preserve parsed raw fields in `staging_rows`.
4. Normalize dates, times, decimals, null markers and whitespace in batches.
5. Retain rejected rows in staging and record their reasons in `rejected_rows`.
6. Commit all three files and their audit counts together; database or ambiguous-key failures roll back the entire import.

Invalid individual records are quarantined and counted. Duplicate order codes or duplicate non-cancellation trade identities abort the bundle rather than guessing which record is correct. This loader supports one monthly three-file bundle per database; overlapping monthly snapshots need an explicit merge policy.

## SQL meaning

`active_trades` excludes cancellation messages and their original trades using trade code, instrument, country and currency. This is a retrospective corrected view of the whole supplied bundle, not an as-of replay. A later cancellation revises the earlier trade's inclusion. Unmatched cancellations remain in the audit.

Daily VWAP includes positive-price, positive-size `AT` trades only. Trade-type reports use the same cancellation rule. Grouping includes instrument and currency. Contra/post-contra records are not automatically linked to an original trade because the supplied feed documentation gives no definitive mapping.

Execution joins include partial and full matches, and automatic/individual auction reports (`AT`, `UT`). `ExecutionVsLimit` is execution minus limit for buys and limit minus execution for sells: positive means worse than the stated limit. It is not a measure of market slippage or implementation shortfall. One trade can relate to two order-side events; lifecycle row counts are not distinct trade counts.

Order timelines use dates, fractional times, instrument, message sequence, order code, detail-before-history priority, descending remaining size, and source row as a final tie-breaker. Carry-over `F` rows retain their original order timestamps and remaining sizes. The timeline does not reconstruct a complete limit order book.

## Data limits

The supplied 17/15/17-field exports use DDMMYYYY dates; ISO dates are also accepted. Times retain up to six fractional digits. Timestamps are left in the source clock, without an inferred timezone conversion. Zero-price market orders are retained, but excluded from limit-price summaries.

Missing matching-order details can reflect aggressive/non-persistent orders or hidden iceberg activity absent from this feed. Such references are audited, not treated as broken parent foreign keys. Individual historic auction trades have unique codes; the dummy code described by MIDAS concerns the aggregated broadcast auction report.

SQLite provides an easy local runner. Its numeric aggregates use floating-point arithmetic; MySQL uses decimal arithmetic. The supplied dataset's SQLite VWAP outputs were independently checked with Python Decimal. Large new datasets need the same validation before relying on SQLite numerical precision.
