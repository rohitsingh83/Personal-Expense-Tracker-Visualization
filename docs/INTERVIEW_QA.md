# Interview Preparation: Personal Expense Tracker (10 Q&As)

1. **Explain your project (Non-Technical):** It's a personal finance assistant that reads bank and UPI statements, automatically groups spending into categories like Groceries and Dining, warns when a monthly budget is exceeded, and generates visual charts and Excel reports.
2. **Explain your project (Technical):** It ingests CSV transactions into a normalized SQLite database with composite-key deduplication, applies regex-based categorization, computes spending KPIs and budget variances, exports a 3-sheet Excel workbook via `xlsxwriter`, and renders 4 Matplotlib charts.
3. **How do you prevent duplicate transactions on re-import?** A `UNIQUE(tx_date, description, amount, account)` constraint paired with `INSERT OR IGNORE` makes CSV ingestion idempotent.
4. **Why store transactions in SQLite instead of only CSVs?** SQLite enforces schema constraints, supports fast SQL aggregations, and avoids overwriting historical records.
5. **How does auto-categorization work?** `src/categorize.py` checks positive amounts as Income and matches negative descriptions against ordered regex rules.
6. **How would you upgrade categorization with ML?** Train a TF-IDF + `MultinomialNB` classifier on user-labeled descriptions once enough history accumulates.
7. **What KPIs does the tracker compute?** Total income, total spend, net savings, top spending category, and average daily spend.
8. **How are budget alerts calculated?** `src/budget.py` joins monthly category spend against `budgets.limit_amount` and flags `over_by > 0`.
9. **Why export to multi-sheet Excel?** Stakeholders and non-technical users can inspect raw transactions, category summaries, and budget alerts in one workbook.
10. **What future features would you add?** OCR receipt scanning with Tesseract, automated email/Telegram budget alerts, and multi-currency FX conversion.
