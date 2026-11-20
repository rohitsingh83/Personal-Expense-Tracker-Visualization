# Personal Expense Tracker with Data Visualization

A modular FinTech personal finance analytics pipeline that ingests bank and UPI CSV statements, cleans and deduplicates transaction data into SQLite, auto-categorizes spending using flexible regex rules, tracks monthly budget deviations, generates Matplotlib charts, and exports multi-tab formatted Excel reports.

---

## 🏛 Architecture & Financial Analytics Pipeline

```
[Bank / UPI CSV Statements]
             │
             ▼
[ETL & Idempotent SQLite Ingestion] (Deduplicates via Composite Keys)
             │
             ▼
[Regex Rule-Based Categorization]   (Groceries, Food, Utilities, Transport, etc.)
             │
             ▼
[Financial KPI & Analytics Engine]  (Income, Spend, Savings, Burn-Rate)
             │
             ▼
[Budget Variance & Alert Monitor]   (Compares Spending against Monthly Caps)
             │
             ▼
[Outputs: 4 Matplotlib Charts] + [Excel Workbook] + [Streamlit & FastAPI]
```

---

## ✨ Key Capabilities

- **Idempotent Ingestion:** Employs SQLite unique constraints `(tx_date, description, amount, account)` to ensure multiple uploads never introduce duplicate records.
- **Rule-Based Regex Categorization:** Matches merchant and transaction descriptions to standardized categories (Groceries, Food & Dining, Transport, Shopping, Utilities, Entertainment, Income).
- **Budget Tracking & Overspend Warnings:** Compares actual spending per category against configured monthly budgets and flags threshold breaches.
- **Multi-Sheet Excel Automation:** Generates formatted workbooks with distinct sheets for Raw Transactions, Category Summaries, and Budget Audits via `XlsxWriter`.
- **Publication-Ready Visualizations:** Automatically renders Category Bar Charts, Donut Share charts, Monthly Trend lines, and Payment Method distribution charts.
- **Dual Interface:** Full interactive Streamlit dashboard + FastAPI REST endpoints for integration into mobile/web backends.

---

## 🚀 Quick Start Guide

### 1. Installation
```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run Main Pipeline
```bash
python main.py
```

### 3. Launch Interactive Dashboard
```bash
python -m streamlit run app_streamlit.py
```

### 4. Start FastAPI Service
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## 📊 Generated Visualizations

| Chart Type | Path | Purpose |
|---|---|---|
| **Category Bar** | `images/category_spending_bar.png` | Ranks absolute expense volume by category. |
| **Category Donut** | `images/category_donut.png` | Visualizes relative percentage share of budget. |
| **Monthly Trend** | `images/monthly_trend_line.png` | Tracks cash burn rate over consecutive months. |
| **Payment Method** | `images/payment_method_pie.png` | Compares UPI vs Debit Card vs Net Banking usage. |
