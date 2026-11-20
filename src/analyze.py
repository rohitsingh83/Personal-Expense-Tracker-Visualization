"""Spending KPIs, monthly trends, and payment method analytics."""

import sqlite3
import pandas as pd


def load_transactions_df(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
    SELECT t.id, t.tx_date, t.description, t.amount, t.payment_method, t.account, c.name AS category
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    ORDER BY t.tx_date
    """
    df = pd.read_sql_query(query, conn)
    df["tx_date"] = pd.to_datetime(df["tx_date"])
    df["month"] = df["tx_date"].dt.to_period("M").astype(str)
    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    income = float(df[df["amount"] > 0]["amount"].sum())
    expenses = float(df[df["amount"] < 0]["amount"].abs().sum())
    savings = income - expenses
    expense_rows = df[df["amount"] < 0].copy()
    expense_rows["spend"] = expense_rows["amount"].abs()
    top_cat = expense_rows.groupby("category")["spend"].sum().idxmax() if not expense_rows.empty else "N/A"
    n_days = max(1, df["tx_date"].nunique())
    return {
        "total_income": round(income, 2),
        "total_spend": round(expenses, 2),
        "net_savings": round(savings, 2),
        "top_category": top_cat,
        "avg_daily_spend": round(expenses / n_days, 2),
    }
