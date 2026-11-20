"""Optional interactive Streamlit dashboard for Personal Expense Tracker."""

from pathlib import Path
import streamlit as st
from src.models import get_connection
from src.analyze import load_transactions_df, compute_kpis
from src.budget import check_budgets

ROOT = Path(__file__).resolve().parent.parent
st.set_page_config(page_title="Personal Expense Tracker", layout="wide")
st.title("Personal Expense Tracker & Budget Dashboard")

conn = get_connection(ROOT / "db" / "expenses.db")
df = load_transactions_df(conn)
kpis = compute_kpis(df)

c1, c2, c3 = st.columns(3)
c1.metric("Total Income", f"INR {kpis['total_income']:,.0f}")
c2.metric("Total Spend", f"INR {kpis['total_spend']:,.0f}")
c3.metric("Net Savings", f"INR {kpis['net_savings']:,.0f}")

month = st.selectbox("Select Month", sorted(df["month"].unique(), reverse=True))
st.subheader(f"Budget Check ({month})")
st.dataframe(check_budgets(df, conn, month), use_container_width=True)
