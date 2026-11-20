"""Interactive Streamlit dashboard for Personal Expense Tracker with Data Visualization."""

from pathlib import Path
import streamlit as st
import pandas as pd
from src.models import get_connection
from src.analyze import load_transactions_df, compute_kpis
from src.budget import check_budgets

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Personal Expense Tracker", layout="wide", page_icon="💰")
st.title("💰 Personal Expense Tracker & Financial Visualizer")

db_path = ROOT / "db" / "expenses.db"
images_dir = ROOT / "images"

if db_path.exists():
    conn = get_connection(db_path)
    df = load_transactions_df(conn)
    kpis = compute_kpis(df)

    # Top KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", f"₹{kpis['total_income']:,.2f}")
    col2.metric("Total Spend", f"₹{kpis['total_spend']:,.2f}")
    col3.metric("Net Savings", f"₹{kpis['net_savings']:,.2f}")
    col4.metric("Avg Daily Spend", f"₹{kpis['avg_daily_spend']:,.2f}")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Visualizations", "🎯 Monthly Budget Health", "📋 Transactions List"])

    with tab1:
        st.subheader("Financial Analytics & Spending Trends")
        c1, c2 = st.columns(2)
        with c1:
            bar_chart = images_dir / "category_spending_bar.png"
            if bar_chart.exists():
                st.image(str(bar_chart), caption="Category Spending Breakdown", use_container_width=True)
            trend_chart = images_dir / "monthly_trend_line.png"
            if trend_chart.exists():
                st.image(str(trend_chart), caption="Monthly Spending Trend", use_container_width=True)
        with c2:
            donut_chart = images_dir / "category_donut.png"
            if donut_chart.exists():
                st.image(str(donut_chart), caption="Expense Distribution Donut", use_container_width=True)
            pie_chart = images_dir / "payment_method_pie.png"
            if pie_chart.exists():
                st.image(str(pie_chart), caption="Payment Method Share", use_container_width=True)

    with tab2:
        month = st.selectbox("Select Month for Budget Analysis", sorted(df["month"].unique(), reverse=True))
        st.subheader(f"Budget Status for {month}")
        budget_df = check_budgets(df, conn, month)
        st.dataframe(budget_df, use_container_width=True)

    with tab3:
        st.subheader("All Ingested Transactions")
        cat_filter = st.selectbox("Filter by Category", ["All"] + sorted(df["category"].unique().tolist()))
        display_df = df if cat_filter == "All" else df[df["category"] == cat_filter]
        st.dataframe(display_df, use_container_width=True)

    conn.close()
else:
    st.info("Database not found. Please run `python main.py` first to ingest sample transactions.")

