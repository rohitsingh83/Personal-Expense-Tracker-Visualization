"""Flagship Personal Expense Tracker & Wealth Intelligence Dashboard.
Features:
- Drag-and-drop bank and UPI CSV statement uploader with automatic cleaning
- Manual transaction logger (instant ledger updates)
- Interactive Plotly visualizations (Category Donut, Spending Bar, Monthly Trend, Payment Share)
- Dynamic Category Budget Editor with real-time overspend alerts
- Formatted Excel workbook & CSV export
"""

import io
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import settings
from src.models import get_connection
from src.categorize import categorize_transaction
from src.ingest import ingest_csv
from src.analyze import load_transactions_df, compute_kpis
from src.budget import seed_budgets, check_budgets

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="FinTrack AI — Personal Wealth & Budget Intelligence",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .fintrack-title { font-size: 2.2rem; font-weight: 800; color: #047857; margin-bottom: 0.2rem; }
    .fintrack-sub { font-size: 1.05rem; color: #64748B; margin-bottom: 1.3rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="fintrack-title">💳 FinTrack AI — Personal Expense & Budget Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="fintrack-sub">Automated Statement Ingestion • Regex Auto-Categorization • Budget Variance & Cashflow Analytics</div>', unsafe_allow_html=True)

conn = get_connection(settings.db_path)
df = load_transactions_df(conn)

# Sidebar: Statement Upload & Manual Entry
with st.sidebar:
    st.header("📥 Ingest Bank Statement")
    uploaded_file = st.file_uploader("Upload Bank / UPI Statement (.csv)", type=["csv"])
    if uploaded_file:
        temp_csv = settings.data_dir / f"uploaded_{uploaded_file.name}"
        temp_csv.write_bytes(uploaded_file.getvalue())
        inserted = ingest_csv(temp_csv, conn)
        st.success(f"Successfully processed statement! Added {inserted} new transactions.")
        df = load_transactions_df(conn)

    st.markdown("---")
    st.header("➕ Add Single Transaction")
    with st.form("manual_tx_form", clear_on_submit=True):
        t_date = st.date_input("Date")
        t_desc = st.text_input("Merchant / Description", "Grocery shopping")
        t_amt = st.number_input("Amount (Negative for Expense, Positive for Income)", value=-450.0, step=50.0)
        t_method = st.selectbox("Payment Method", ["UPI", "Debit Card", "Credit Card", "Net Banking", "Cash"])
        t_acc = st.text_input("Account", "Primary Bank")
        
        submitted = st.form_submit_button("Record Transaction")
        if submitted:
            cat = categorize_transaction(t_desc, t_amt)
            cur = conn.cursor()
            cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
            cur.execute("SELECT id FROM categories WHERE name = ?", (cat,))
            cat_id = cur.fetchone()[0]
            cur.execute(
                """INSERT OR IGNORE INTO transactions
                   (tx_date, description, amount, payment_method, account, category_id, raw_source)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(t_date), t_desc, float(t_amt), t_method, t_acc, cat_id, "manual_entry"),
            )
            conn.commit()
            st.success(f"Logged transaction in category: {cat}")
            df = load_transactions_df(conn)

kpis = compute_kpis(df)

# Top KPI Metric Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Income", f"₹{kpis['total_income']:,.2f}")
k2.metric("Total Expenses", f"₹{kpis['total_spend']:,.2f}")
savings_rate = (kpis['net_savings'] / max(1, kpis['total_income'])) * 100
k3.metric("Net Savings", f"₹{kpis['net_savings']:,.2f}", delta=f"{savings_rate:.1f}% Savings Rate")
k4.metric("Average Daily Spend", f"₹{kpis['avg_daily_spend']:,.2f}")

st.markdown("---")

tab_visuals, tab_budgets, tab_ledger = st.tabs([
    "📊 Financial Visualizations & Cashflow",
    "🎯 Monthly Budget Variance & Alerts",
    "📋 Interactive Transaction Ledger"
])

with tab_visuals:
    st.subheader("Expense Distribution & Spending Trends")
    
    exp_df = df[df["amount"] < 0].copy()
    exp_df["spend"] = exp_df["amount"].abs()

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        # Category Donut Chart
        cat_agg = exp_df.groupby("category")["spend"].sum().reset_index()
        fig_donut = px.pie(
            cat_agg, values="spend", names="category", hole=0.45,
            title="Spending Share by Category",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_v2:
        # Payment Method Breakdown
        pm_agg = exp_df.groupby("payment_method")["spend"].sum().reset_index()
        fig_bar = px.bar(
            pm_agg, x="spend", y="payment_method", orientation="h",
            title="Expenditure by Payment Channel (INR)",
            color="spend", color_continuous_scale="Teal"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Monthly Trend Line
    monthly_trend = exp_df.groupby("month")["spend"].sum().reset_index()
    fig_trend = px.line(
        monthly_trend, x="month", y="spend", markers=True,
        title="Monthly Expense Burn Rate (INR)",
        labels={"month": "Billing Period", "spend": "Total Spend (₹)"}
    )
    fig_trend.update_traces(line_color="#047857", line_width=3)
    st.plotly_chart(fig_trend, use_container_width=True)

with tab_budgets:
    st.subheader("Monthly Category Budget Tracker")
    available_months = sorted(df["month"].unique())
    selected_month = st.selectbox("Select Target Month", available_months, index=len(available_months)-1)
    
    seed_budgets(conn, selected_month)
    budget_df = check_budgets(df, conn, selected_month)
    
    # Overspend Warnings
    breaches = budget_df[budget_df["status"] == "OVER BUDGET"]
    if not breaches.empty:
        for _, b in breaches.iterrows():
            st.error(f"🚨 **Budget Breach in {b['category_name']}!** Spent: ₹{b['spend']:,.2f} / Limit: ₹{b['limit_amount']:,.2f} (Over by ₹{b['over_by']:,.2f})")
    else:
        st.success("🎉 Excellent financial discipline! All categories are strictly within configured budget caps.")

    # Budget vs Actual Plotly Comparison
    fig_b = px.bar(
        budget_df, x="category_name", y=["limit_amount", "spend"],
        barmode="group",
        title=f"Budget Cap vs Actual Spending ({selected_month})",
        labels={"value": "Amount (₹)", "category_name": "Category", "variable": "Metric"},
        color_discrete_map={"limit_amount": "#3B82F6", "spend": "#EF4444"}
    )
    st.plotly_chart(fig_b, use_container_width=True)
    st.dataframe(budget_df, use_container_width=True)

with tab_ledger:
    st.subheader("Searchable Transaction Ledger")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_cat = st.selectbox("Filter Category", ["All"] + sorted(df["category"].dropna().unique().tolist()))
    with col_f2:
        search_query = st.text_input("Search Description / Merchant", "")
    
    filtered_df = df.copy()
    if f_cat != "All":
        filtered_df = filtered_df[filtered_df["category"] == f_cat]
    if search_query:
        filtered_df = filtered_df[filtered_df["description"].str.contains(search_query, case=False, na=False)]

    st.dataframe(
        filtered_df[["tx_date", "description", "category", "amount", "payment_method", "account"]].sort_values("tx_date", ascending=False),
        use_container_width=True
    )
    
    # Download
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Filtered Ledger (CSV)", data=csv_bytes, file_name="transaction_ledger.csv", mime="text/csv")

conn.close()
