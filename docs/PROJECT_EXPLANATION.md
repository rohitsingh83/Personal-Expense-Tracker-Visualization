# Project Explanation: Personal Expense Tracker with Data Visualization

## 1. What is it?

**Simple explanation.** Most people don't know where their salary goes each month. This app records every
expense and income, sorts them into categories automatically, compares spending with monthly budgets, and turns
everything into clear charts. It also tells you things in plain English, like "Shopping spending rose 1098%
this month" or "this ₹9,800 hospital bill is 19× your usual health spend", and predicts next month's spending.

**Technical explanation.** It's a data-analysis application in Python. Transactions are stored in SQLite (with a
uniqueness rule so bank statements can't be imported twice) and loaded into Pandas. Keyword rules with regex
assign categories. The analysis layer computes KPIs, monthly pivots, month-over-month changes, budget usage
with month-end projection, anomalies via a robust z-score (median and MAD), and a forecast that blends a NumPy
linear trend with a 3-month average after removing one-off outliers. Results appear in a Streamlit + Plotly
dashboard, a Rich CLI, an Excel workbook with native charts, and a PDF monthly statement.

### Why it matters

Personal-finance apps (Walnut, Money View, YNAB, INDmoney) and bank dashboards do exactly this. It's also the
same workflow a data analyst follows at work: **collect → clean → categorise → aggregate → visualise → explain
→ report**.

### Workflow

```
add / import transactions → validate & auto-categorise → store in SQLite → load into Pandas
   → summaries, trends, budgets, anomalies, forecast → insights → charts, dashboard, Excel and PDF reports
```

## 2. Tech stack options

| Option | Tools | Difficulty | Output |
|---|---|---|---|
| A. Easy | Python lists/dicts, CSV module, Matplotlib | Beginner | Totals per category + a pie chart |
| **B. Intermediate** ✅ | Pandas, NumPy, SQLite, Matplotlib, Plotly, Streamlit, XlsxWriter, fpdf2 | Intermediate | Full dashboard, budgets, anomaly detection, forecast, reports |
| C. Advanced | B + bank APIs (Account Aggregator), ML categorisation (scikit-learn), user accounts, cloud DB | Advanced | Multi-user fintech product |

**Chosen: B.** These are exactly the libraries data-analyst job descriptions ask for, and every result can be
explained.

## 3. Architecture

```
  INPUT        sidebar form / CLI "add"     CSV bank statement      data/budgets.json
                         │                         │                       │
  PROCESSING   ┌─────────▼─────────────────────────▼──┐                    │
               │ categorizer.py  keyword rules → cat  │                    │
               │ storage.py      SQLite CRUD, import, │                    │
               │                 duplicate protection │                    │
               └─────────────────┬────────────────────┘                    │
                                 │ Pandas DataFrame                        │
               ┌─────────────────▼────────────────────────────────────────▼┐
               │ analysis.py  summary · monthly totals · category pivots  │
               │              month-over-month · budget status/projection │
               │              anomalies (robust z) · forecast · insights  │
               └───────┬──────────────────┬───────────────────┬───────────┘
  OUTPUT               ▼                  ▼                   ▼
               app.py (Streamlit)    charts.py (PNG)     report.py (Excel + PDF)
               main.py (CLI)
```

### Key algorithms

**Budget projection.** For the current month, `projected = spent ÷ fraction of month passed`. Fixed monthly
costs (rent, bills) are not extrapolated, because rent paid on the 5th doesn't grow by the 30th.

**Anomaly detection.** For each category, `z = 0.6745 × (amount − median) ÷ MAD`. Median and MAD resist
outliers, unlike mean and standard deviation (one ₹28k phone would inflate the standard deviation and hide
itself). A transaction is flagged when z > 3.5, it is at least 3× the typical amount, and it is over ₹2,500.
When most amounts are identical (MAD = 0), 10% of the median is used instead.

**Forecast.** Remove anomalies → monthly totals of complete months → fit `y = a·x + b` with `numpy.polyfit`
→ forecast = ½ × trend prediction + ½ × average of the last 3 months.

## 4. Implementation plan

| Phase | What | Why | Output | Common mistakes |
|---|---|---|---|---|
| 1. Setup | venv + requirements | Reproducible | Libraries ready | Global installs |
| 2. Folders | data, src, outputs, images, docs, tests | Organisation | Clean tree | Everything in one file |
| 3. Data | `scripts/generate_sample_data.py` | Bank data is private | 6 months, 244 rows | Perfectly uniform fake data |
| 4. Storage | SQLite schema + CRUD | Safe edits, no duplicates | expenses.db | Re-importing creates duplicates |
| 5. Categorise | keyword rules | Manual labelling is slow | Category per row | "auto" matching "autograph" |
| 6. Analysis | Pandas groupby/pivot | Answer questions with numbers | KPIs, trends | Mixing income with expenses |
| 7. Budgets | status + projection | Act before overspending | On track / Warning / Over | Projecting rent linearly |
| 8. Insights | anomalies, forecast, text | Explain, don't just show | Plain-English tips | Mean/std hiding outliers |
| 9. Visualise | Matplotlib + Plotly | Patterns are obvious in charts | 5 static + 10 interactive charts | Pie charts with 15 slices |
| 10. Reports | Excel + PDF | Shareable results | .xlsx and .pdf | Emoji breaking PDF fonts |
| 11. GitHub | commit + screenshots | Proof of work | Public repo | Committing a personal DB |

## 8. Virtual simulation

1. `scripts/generate_sample_data.py` simulates a young professional in Bengaluru from June to November 2026:
   salary on the 1st, rent on the 5th, monthly bills, frequent food orders and cabs (more at weekends), a Goa
   trip in August, Diwali shopping, two freelance payments, and two unusual expenses (a ₹27,999 phone and a
   ₹9,800 hospital bill).
2. On first run the app creates `data/expenses.db` and imports the CSV.
3. Add expenses from the sidebar or with `python main.py add 450 "Swiggy dinner"` and watch the category get
   detected.
4. Import a statement CSV; importing it twice adds nothing.
5. Change budgets and see statuses update; change the month to compare periods.

**Results from the simulation:** savings ranged from +50% (July, with freelance income) to −34% (September,
when the phone was bought). The anomaly detector found exactly the two planted outliers, and the forecast for
December is about ₹54k after excluding them.

## 12. Proof-building plan

| Day | Work | Commit message | Screenshot |
|---|---|---|---|
| 1 | Setup, sample data, budgets | `chore: project setup with six months of sample data` | Folder + CSV |
| 2 | SQLite storage + categoriser | `feat: SQLite storage with auto-categorisation and safe imports` | `python main.py list` |
| 3 | Analysis | `feat: summaries, budgets, anomaly detection, forecast and insights` | `python main.py summary` |
| 4 | Charts + reports | `feat: charts, Excel workbook and PDF monthly statement` | PDF, Excel |
| 5 | Dashboard | `feat: Streamlit dashboard` | Each tab |
| 6 | Tests + docs | `docs: README, explanation, interview Q&A` | pytest, GitHub page |

## 13. Screenshot checklist

- [ ] Folder structure
- [ ] `python main.py summary` output
- [ ] Dashboard, Budgets and Insights tabs
- [ ] PDF statement and Excel workbook opened
- [ ] Charts in `images/`
- [ ] pytest passing
- [ ] GitHub repository page
