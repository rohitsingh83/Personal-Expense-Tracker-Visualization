"""Monthly category budget limits and overspend alerts."""

import sqlite3
import pandas as pd


DEFAULT_BUDGETS = {
    "Groceries": 3500.0,
    "Food & Dining": 1000.0,
    "Transport": 1200.0,
    "Bills & Utilities": 2500.0,
    "Shopping": 1500.0,
    "Entertainment": 700.0,
}


def seed_budgets(conn: sqlite3.Connection, month: str) -> None:
    cur = conn.cursor()
    for cat, limit_amt in DEFAULT_BUDGETS.items():
        cur.execute(
            "INSERT OR IGNORE INTO budgets (month, category_name, limit_amount) VALUES (?, ?, ?)",
            (month, cat, limit_amt),
        )
    conn.commit()


def check_budgets(df: pd.DataFrame, conn: sqlite3.Connection, month: str) -> pd.DataFrame:
    budgets = pd.read_sql_query("SELECT category_name, limit_amount FROM budgets WHERE month = ?", conn, params=(month,))
    exp = df[(df["month"] == month) & (df["amount"] < 0)].copy()
    exp["spend"] = exp["amount"].abs()
    cat_spend = exp.groupby("category")["spend"].sum().reset_index().rename(columns={"category": "category_name"})

    merged = budgets.merge(cat_spend, on="category_name", how="left").fillna({"spend": 0.0})
    merged["over_by"] = (merged["spend"] - merged["limit_amount"]).round(2)
    merged["status"] = merged["over_by"].apply(lambda x: "OVER BUDGET" if x > 0 else "Within Budget")
    return merged.sort_values("over_by", ascending=False)
