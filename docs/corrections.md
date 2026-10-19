# Corrections and changes

Compared with `coursework_final.ipynb`; original coursework files remain unchanged.

1. Apply cancellation exclusion consistently to trade counts, trade-type reports and execution joins. Previously several queries counted original trades after cancellation.
2. Separate cancellation-message counts, cancelled original trades and unmatched cancellations. Counting non-deletion messages alone does not count active trades.
3. Scope trade matching by instrument, country and currency as well as trade code.
4. Include partial matches alongside full matches in execution analysis; label these as order-side execution events.
5. Make execution-versus-limit differences side-aware and stop labeling them as market slippage.
6. Add the documented transaction-limit lifecycle action (`T`).
7. Preserve microsecond timestamps and use deterministic sequence/tie-break ordering.
8. Use BIGINT sequence and size fields, retaining DECIMAL(18,8) prices in MySQL; avoid SQLite integer division in VWAP.
9. Validate field widths, required values, dates, times, nonnegative finite decimals, integral quantities and order sides. Normalize whitespace before interpreting null markers.
10. Preserve raw staging rows and rejection reasons instead of dropping all import evidence.
11. Load the three files transactionally; roll back failed bundles and refuse accidental duplicate imports or ambiguous duplicate identities.
12. Remove hard-coded root connections and personal paths. Use environment configuration, bound SQL parameters and reliably closed connections/cursors.
13. Replace global `local_infile` changes and notebook execution order with an installable CLI and batch inserts.
14. Guard VWAP denominators and exclude nonpositive executions consistently. Group by instrument/currency rather than assuming a single security.
15. Audit missing matching-order references separately from parent-order integrity. An inner join alone does not prove referential completeness.
16. Correct the auction-code explanation: individual historic uncrossing trades have unique codes; the aggregated broadcast report has a dummy code.
17. Add SQLite portability, invented sample data, an independent Decimal reference calculation, source hashes and Python/MySQL CI.
18. Remove long coursework discussion, screenshots, student identifiers and notebook boilerplate. Publish concise documentation and aggregate outputs; no AUTHORS.md or vendor tick files.
