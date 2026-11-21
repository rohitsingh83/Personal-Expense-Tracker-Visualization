"""FastAPI backend service for Personal Expense Tracker."""
from pathlib import Path
from fastapi import FastAPI
from src.analyze import load_transactions_df, compute_kpis
from src.budget import check_budgets
from src.models import get_connection

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Personal Expense Tracker API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "Personal-Expense-Tracker"}


@app.get("/transactions")
def get_transactions():
    conn = get_connection(ROOT / "db" / "expenses.db")
    df = load_transactions_df(conn)
    conn.close()
    df["tx_date"] = df["tx_date"].dt.strftime("%Y-%m-%d")
    return {"transactions": df.to_dict(orient="records")}


@app.get("/kpis")
def get_kpis():
    conn = get_connection(ROOT / "db" / "expenses.db")
    df = load_transactions_df(conn)
    conn.close()
    return {"kpis": compute_kpis(df)}


@app.get("/budget/{month}")
def get_budget(month: str):
    conn = get_connection(ROOT / "db" / "expenses.db")
    df = load_transactions_df(conn)
    budget_df = check_budgets(df, conn, month)
    conn.close()
    return {"month": month, "budgets": budget_df.to_dict(orient="records")}

