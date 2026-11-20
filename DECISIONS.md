# Architecture & Engineering Decisions (ADR)

## ADR 001: Deduplication Key Integrity & Preserving Legitimate Duplicates
- **Status:** Accepted
- **Context:** `UNIQUE(tx_date, description, amount, account)` silently drops distinct transactions that share identical metadata on the same day.
- **Decision:** Introduce a deterministic line-item composite hash / row sequence index while maintaining backward-compatible upsert queries.
- **Consequences:** Prevents ledger under-counting while preserving idempotency.

## ADR 002: Batch Ingestion via executemany
- **Status:** Accepted
- **Context:** `iterrows()` row-by-row insertion in Pandas is an anti-pattern that slows ingestion significantly on large CSVs.
- **Decision:** Convert cleaned DataFrames into lists of tuples and execute bulk `executemany` statements inside a transaction.
- **Consequences:** Orders of magnitude faster statement loading.

## ADR 003: Externalized Categorization & Budget Limits
- **Status:** Accepted
- **Context:** Hardcoded lists in `src/categorize.py` and `src/budget.py` prevent customization without code modifications.
- **Decision:** Load rules from structured settings with built-in fallbacks.
- **Consequences:** Enables customizable budget and categorization rules per deployment.
