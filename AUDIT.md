# Engineering Audit: Personal Expense Tracker with Data Visualization

**Project Context:**
- **What it does / who it's for:** A personal finance analytics engine that ingests bank and UPI CSV statements, normalizes and deduplicates transactions in SQLite, auto-categorizes spending via regex rules, detects monthly budget breaches, and exports formatted Excel workbooks and Matplotlib charts.
- **Stack & entry points:** Python 3.14 / 3.11, `pandas`, `sqlite3`, `matplotlib`, `xlsxwriter`, `fastapi`, `streamlit`. Entry points: `python main.py`, `python notebooks/eda_analysis.py`, `python -m uvicorn api.app:app`, `python -m streamlit run app_streamlit.py`.
- **Real usage:** Batch statement processor (`main.py`) + REST API (`api/app.py`) + financial analysis UI (`app_streamlit.py`).
- **Constraint:** Preserve `data/sample_expenses.csv` format, SQLite table structure, `reports/budget_alerts.csv` output, and generated chart filenames.

---

## Findings & Technical Debt

### 🔴 Critical Findings
1. **Flawed Deduplication Key Leading to Silent Dropped Legitimate Transactions (`src/models.py`):**
   - The unique constraint `UNIQUE(tx_date, description, amount, account)` silently discards genuine duplicate transactions. For instance, two separate ₹50 Metro recharges, two distinct ₹20 tea purchases, or split grocery payments at the same vendor on the same day are dropped on re-ingestion, causing ledger under-counting.
2. **Slow Row-by-Row Iteration During Ingestion (`src/ingest.py`):**
   - Ingestion uses `for _, row in df.iterrows():` with individual `INSERT OR IGNORE INTO categories` and `INSERT OR IGNORE INTO transactions`. `iterrows()` is known to be the slowest iterator in Pandas (~100x slower than vectorized or bulk tuple inserts).
3. **Hardcoded Financial Rules & Budget Caps in Python Source (`src/categorize.py` & `src/budget.py`):**
   - `CATEGORY_RULES` and `DEFAULT_BUDGETS` are hardcoded lists and dictionaries directly inside Python source files. Users cannot modify categorization patterns, add new budget lines, or adjust monthly thresholds without modifying Python code.

### 🟡 High Priority Findings
4. **Lack of Ingestion Schema Validation:**
   - Bank CSVs with variations in date formatting (e.g. `DD/MM/YYYY` vs `YYYY-MM-DD` vs `MM-DD-YYYY`) or varying column headers (`Txn Date`, `Value Date`, `Posting Date`) will silently fail or produce NaT dates.
5. **No Currency or Decimal Precision Safeguards:**
   - Financial amounts are stored as SQLite `REAL` and Python `float`, susceptible to floating-point representation drift (e.g. `0.1 + 0.2 = 0.30000000000000004`). In production FinTech systems, monetary amounts require integer cents/paise or `decimal.Decimal`.
6. **Excel Export Lacks Professional Styling & Formatting (`src/report.py`):**
   - `export_excel_report()` outputs raw unstyled tabular sheets without currency formatting, auto-adjusted column widths, header freeze panes, or summary row formulas.

### 🟢 Nice-to-Have / Polish
7. **No Config Object / pyproject.toml:**
   - Needs standard PEP 621 metadata, pinned dependencies, and centralized settings.
8. **Stateless Chart Generation:**
   - Plots save directly to `images/` overwriting previous versions without run timestamps or metric snapshots.

---

## What "Elite" Looks Like for This Exact Project

An elite personal finance data platform:
- Uses a unique ingestion key based on transaction references / bank IDs or deterministic multi-field hash including source line numbers.
- Handles bulk ingestion using `executemany` with sub-millisecond execution for thousands of rows.
- Externalizes categorization rules and budget ceilings into a validated YAML/JSON configuration.
- Enforces decimal precision or strict rounding on all monetary aggregations.
- Generates polished, corporate-grade Excel reports with automated column autosizing, number formatting (`₹#,##0.00`), and summary formulas.
