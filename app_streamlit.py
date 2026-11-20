"""Interactive Streamlit dashboard for Personal Expense Tracker."""
from pathlib import Path
import pandas as pd
import streamlit as st
from src.models import get_connection
from src.analyze import load_transactions_df, compute_kpis
from src.budget import check_budgets

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Personal Expense & Financial Health Tracker",
    layout="wide",
    page_icon="💰",
)

st.title("💰 Personal Expense & Budget Tracker")
st.caption("Automated Ingestion, Regex Categorization & Visual Financial Analytics")

db_path = ROOT / "db" / "expenses.db"

if db_path.exists():
    conn = get_connection(db_path)
    df = load_transactions_df(conn)
    kpis = compute_kpis(df)
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Filter Transactions")
        available_categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
        selected_cat = st.selectbox("Category Filter", available_categories)
        
        available_months = ["All"] + sorted(df["month"].dropna().unique().tolist(), reverse=True)
        selected_month = st.selectbox("Month Filter", available_months)

    # Top KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income", f"₹{kpis['total_income']:,.2f}")
    c2.metric("Total Expenses", f"₹{kpis['total_spend']:,.2f}")
    c3.metric("Net Savings", f"₹{kpis['net_savings']:,.2f}", delta=f"{(kpis['net_savings']/max(1, kpis['total_income'])*100):.1f}% savings rate")
    c4.metric("Avg Daily Spend", f"₹{kpis['avg_daily_spend']:,.2f}")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Financial Visualizations", "⚠️ Budget Checks", "📝 Transaction Ledger", "📈 Monthly Breakdown"])

    with tab1:
        st.subheader("Spending Analysis Charts")
        col_a, col_b = st.columns(2)
        with col_a:
            p1 = ROOT / "images" / "category_spending_bar.png"
            if p1.exists():
                st.image(str(p1), caption="Spending by Category", use_container_width=True)
            p3 = ROOT / "images" / "monthly_trend_line.png"
            if p3.exists():
                st.image(str(p3), caption="Monthly Spending Trend", use_container_width=True)
        with col_b:
            p2 = ROOT / "images" / "category_donut.png"
            if p2.exists():
                st.image(str(p2), caption="Category Distribution", use_container_width=True)
            p4 = ROOT / "images" / "payment_method_pie.png"
            if p4.exists():
                st.image(str(p4), caption="Payment Method Breakdown", use_container_width=True)

    with tab2:
        st.subheader("Category Budget Variance Monitor")
        latest_month = sorted(df["month"].unique())[-1]
        budget_df = check_budgets(df, conn, latest_month)
        
        st.write(f"Target Period: **{latest_month}**")
        st.dataframe(budget_df, use_container_width=True)
        
        over_budget = budget_df[budget_df["status"] == "OVER BUDGET"]
        if not over_budget.empty:
            for _, r in over_budget.iterrows():
                st.error(f"⚠️ **{r['category_name']}** exceeded limit by ₹{r['over_by']:,.2f} (Limit: ₹{r['limit_amount']:,.2f}, Spent: ₹{r['spend']:,.2f})")
        else:
            st.success("🎉 All categories are within budget limits!")

    with tab3:
        st.subheader("Detailed Transaction Ledger")
        filtered_df = df.copy()
        if selected_cat != "All":
            filtered_df = filtered_df[filtered_df["category"] == selected_cat]
        if selected_month != "All":
            filtered_df = filtered_df[filtered_df["month"] == selected_month]
        
        st.dataframe(filtered_df[["tx_date", "description", "category", "amount", "payment_method", "account"]], use_container_width=True)

    with tab4:
        st.subheader("Aggregated Monthly Summary")
        exp_df = df[df["amount"] < 0].copy()
        exp_df["spend"] = exp_df["amount"].abs()
        pivot = exp_df.pivot_table(index="category", columns="month", values="spend", aggfunc="sum", fill_value=0)
        st.dataframe(pivot, use_container_width=True)

    conn.close()
else:
    st.warning("Database not found. Run `python main.py` first to ingest sample transaction statements.")
