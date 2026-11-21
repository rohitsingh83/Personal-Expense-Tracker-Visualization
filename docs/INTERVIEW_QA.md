# Interview Preparation: Personal Expense Tracker with Data Visualization

### 1. Explain your project.

**HR version:** I built a personal finance app that tracks income and expenses, sorts them into categories
automatically, compares spending with budgets, and shows everything in an interactive dashboard. It doesn't
just draw charts: it explains the data, warns when you're about to overspend, spots unusual expenses, and
predicts next month's spending. You can download a PDF statement or an Excel report.

**Technical version:** It's a Python data-analysis app. Transactions are stored in SQLite with a UNIQUE
constraint so imports are idempotent, and loaded into Pandas. A regex keyword categoriser labels them. The
analysis module uses groupby and pivot tables for monthly and category views, projects month-end budget usage,
detects anomalies with a robust z-score based on the median and MAD, and forecasts spending with a NumPy linear
fit blended with a 3-month average after removing outliers. The front end is Streamlit with Plotly. Reports use
XlsxWriter (native Excel charts) and fpdf2. There's also a Rich CLI and 18 pytest tests.

### 2. Why SQLite instead of just a CSV file?

SQLite gives safe inserts, updates and deletes, a schema with CHECK constraints (amount > 0), and a UNIQUE
constraint on date, description, amount and type. Importing the same bank statement twice adds nothing. It's
built into Python and needs no server, and the CSV is still used for sample data and exports.

### 3. How does automatic categorisation work?

A dictionary maps each category to keywords ("swiggy", "zomato" → Food & Dining; "uber", "metro" → Transport).
I match with regex word boundaries, so "auto" doesn't match "autograph". A category the user chooses always
overrides the guess. The next step would be a scikit-learn text classifier trained on the user's corrections.

### 4. Which Pandas operations did you use most?

`groupby` + `agg` for category totals, counts and averages; `pivot_table` for month × category and month ×
type; `dt` accessors for month, weekday and week; boolean masks for filtering; `merge` to remove anomalies
before forecasting; and `melt` to reshape data for stacked area charts.

### 5. How do you detect unusual expenses?

With a robust z-score per category: `0.6745 × (amount − median) ÷ MAD`. Mean and standard deviation are
distorted by the outlier itself (a ₹28k phone inflates the standard deviation so much it can hide), but the
median and MAD aren't. I also require at least 3× the typical amount and over ₹2,500 to avoid noise, and handle
MAD = 0 when most amounts are identical. On the sample data it finds exactly the two planted outliers.

### 6. How does the forecast work, and what are its limits?

I remove anomalies, take monthly totals for complete months, fit a straight line with `numpy.polyfit`, and
average that prediction with the last 3 months' mean to reduce overreaction. Limits: only six months of data,
no seasonality (festivals, travel), and it assumes past behaviour continues. With more data I'd try seasonal
decomposition or Prophet.

### 7. How is the budget status decided?

Over budget if spent > limit. "Will overspend" if the projected month-end spend (spent ÷ fraction of the month
passed) exceeds the limit. Warning at 80%+. Fixed costs like rent aren't projected, otherwise paying rent on
the 5th would look like a huge overspend.

### 8. Which charts did you choose and why?

Donut for category share (with few categories), grouped bars for income vs expenses, a line for savings rate
over time, horizontal bars for budget usage (easy to read labels), a calendar heatmap for daily spending
patterns, stacked area for category trends, and a gauge for total budget. Each chart answers one specific
question.

### 9. What insights did you find in the data?

September had a −34% savings rate because of a one-off phone purchase. Food delivery is a big repeat cost,
with 12 orders in October. Spending is highest at weekends. August spiked because of a Goa trip. The app
generates these insights as text automatically.

### 10. What challenges did you face?

Making the sample data realistic (weekend bias, fixed vs variable costs), stopping fixed costs from triggering
false overspend warnings, outliers distorting statistics, the Indian Rupee symbol and emoji in the PDF (I
embedded a Unicode font and filtered out emoji), and keeping the dashboard in sync when rows are edited.

### 11. How did you test it?

Pytest with a temporary database per test: duplicate-safe import, categorisation edge cases, CRUD and
validation, totals matching between functions, shares summing to 100%, anomalies finding exactly the planted
outliers, budget projection rules, forecast bounds, and that the Excel and PDF bytes are valid files.

### 12. How would you improve it?

Bank sync through India's Account Aggregator framework, ML categorisation that learns from corrections,
recurring-payment detection, savings goals, multi-user login, a mobile-friendly UI, and cloud deployment.
