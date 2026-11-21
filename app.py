"""
Personal Expense Tracker dashboard.

Run:  streamlit run app.py
"""

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import analysis as an
from src.categorizer import CATEGORIES, INCOME_CATEGORIES, categorize
from src.report import excel_report, pdf_report
from src.storage import ExpenseStore

st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
COLOURS = dict(zip(CATEGORIES, ["#EF4444", "#84CC16", "#F59E0B", "#EC4899", "#0F766E", "#6366F1", "#A855F7",
                                "#06B6D4", "#F97316", "#14B8A6", "#64748B"]))
METHODS = ["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking"]

st.markdown("""
<style>
.block-container {padding-top: 1.6rem;}
.hero {background: linear-gradient(120deg, #134E4A 0%, #0F766E 50%, #2DD4BF 100%); color: white;
       padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;}
.hero h1 {margin: 0; font-size: 2rem; color: white;}
.hero p {margin: .3rem 0 0 0; opacity: .92;}
.kpi {background: white; border: 1px solid #D1FAE5; border-radius: 14px; padding: 1rem 1.2rem;
      box-shadow: 0 1px 3px rgba(15,118,110,.08);}
.kpi .label {color: #64748B; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em;}
.kpi .value {font-size: 1.85rem; font-weight: 700; color: #0F172A;}
.kpi .delta-up {color: #DC2626; font-size: .85rem;}
.kpi .delta-down {color: #16A34A; font-size: .85rem;}
.kpi .sub {color: #64748B; font-size: .85rem;}
.insight {background: white; border-radius: 12px; padding: .75rem 1rem; margin-bottom: .55rem;
          border-left: 5px solid #0F766E; box-shadow: 0 1px 2px rgba(0,0,0,.05);}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_store() -> ExpenseStore:
    return ExpenseStore()


store = get_store()


def kpi(col, label, value, delta=None, good_when_down=True, sub=""):
    delta_html = ""
    if delta is not None:
        up = delta > 0
        cls = ("delta-up" if up else "delta-down") if good_when_down else ("delta-down" if up else "delta-up")
        delta_html = f'<div class="{cls}">{"▲" if up else "▼"} {abs(delta):.0f}% vs last month</div>'
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>'
                 f'{delta_html}<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def pct_change(new, old):
    return (new - old) / old * 100 if old else None


# ------------------------------------------------------------------ sidebar: add transaction
with st.sidebar:
    st.header("➕ Add transaction")
    with st.form("add", clear_on_submit=True):
        kind = st.radio("Type", ["Expense", "Income"], horizontal=True)
        amount = st.number_input("Amount (₹)", min_value=0.0, step=50.0)
        desc = st.text_input("Description", placeholder="e.g. Swiggy dinner, Uber to office")
        cat_options = ["Auto-detect"] + (CATEGORIES if kind == "Expense" else INCOME_CATEGORIES)
        cat = st.selectbox("Category", cat_options)
        method = st.selectbox("Payment method", METHODS)
        when = st.date_input("Date", date.today())
        if st.form_submit_button("Save", type="primary", width="stretch"):
            try:
                t = kind.lower()
                store.add(when, desc, amount, None if cat == "Auto-detect" else cat, method, t)
                st.success(f"Saved: {desc} → {categorize(desc, t) if cat == 'Auto-detect' else cat}")
            except ValueError as e:
                st.error(str(e))

df = store.to_dataframe()
months = an.months_available(df)
with st.sidebar:
    st.header("📅 Period")
    month = st.selectbox("Month", months[::-1], format_func=an.month_label)
    st.caption(f"{len(df)} transactions stored in data/expenses.db")

budgets = an.load_budgets()
m = an.month_slice(df, month)
s = an.summary(m)
prev = months[months.index(month) - 1] if months.index(month) > 0 else None
ps = an.summary(an.month_slice(df, prev)) if prev else None

st.markdown(f'<div class="hero"><h1>💰 Personal Expense Tracker</h1>'
            f'<p>{an.month_label(month)} · {s["transactions"]} expenses · top category: {s["top_category"]}</p></div>',
            unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Income", f"₹{s['income']:,.0f}", pct_change(s["income"], ps["income"]) if ps else None, good_when_down=False)
kpi(c2, "Spent", f"₹{s['expense']:,.0f}", pct_change(s["expense"], ps["expense"]) if ps else None)
kpi(c3, "Saved", f"₹{s['savings']:,.0f}", sub=f"savings rate {s['savings_rate']:.0f}%")
kpi(c4, "Average per day", f"₹{s['avg_daily_spend']:,.0f}", sub=f"biggest expense ₹{s['biggest_expense']:,.0f}")
st.write("")

tab_dash, tab_budget, tab_insight, tab_txn, tab_import, tab_report = st.tabs(
    ["📊 Dashboard", "🎯 Budgets", "💡 Insights", "🧾 Transactions", "📥 Import", "📄 Reports"])

# ------------------------------------------------------------------ dashboard
with tab_dash:
    left, right = st.columns([1, 1])
    cats = an.category_breakdown(m)
    donut = px.pie(cats, names="category", values="total", hole=.55, color="category", color_discrete_map=COLOURS,
                   title=f"Where the money went in {an.month_label(month)}")
    donut.update_traces(textinfo="percent", hovertemplate="%{label}: ₹%{value:,.0f}<extra></extra>")
    donut.add_annotation(text=f"<b>₹{s['expense']:,.0f}</b><br>spent", showarrow=False, font_size=16)
    donut.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
    left.plotly_chart(donut, width="stretch")

    mt = an.monthly_totals(df)
    fig = go.Figure()
    fig.add_bar(x=[an.month_label(x) for x in mt["month"]], y=mt["income"], name="Income", marker_color="#14B8A6")
    fig.add_bar(x=[an.month_label(x) for x in mt["month"]], y=mt["expense"], name="Expenses", marker_color="#EF4444")
    fig.add_scatter(x=[an.month_label(x) for x in mt["month"]], y=mt["savings_rate"], name="Savings rate %",
                    yaxis="y2", mode="lines+markers", line=dict(color="#0F172A"))
    fig.update_layout(title="Income vs expenses", barmode="group", height=420, margin=dict(l=10, r=10, t=50, b=10),
                      yaxis=dict(title="₹"), yaxis2=dict(title="Savings %", overlaying="y", side="right",
                                                         showgrid=False), legend=dict(orientation="h", y=-0.15))
    right.plotly_chart(fig, width="stretch")

    exp = an.expenses(m)
    daily = exp.groupby(exp["date"].dt.date)["amount"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["week"] = daily["date"].dt.isocalendar().week.astype(int)
    daily["weekday"] = daily["date"].dt.day_name().str[:3]
    heat = px.density_heatmap(daily, x="week", y="weekday", z="amount", histfunc="sum", nbinsx=6,
                              category_orders={"weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                              color_continuous_scale="Teal", title="Daily spending calendar (darker = more spent)")
    heat.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Week of year",
                       yaxis_title=None, coloraxis_colorbar_title="₹")
    st.plotly_chart(heat, width="stretch")

    trend = an.category_by_month(df).reset_index().melt(id_vars="month", var_name="category", value_name="amount")
    area = px.area(trend, x="month", y="amount", color="category", color_discrete_map=COLOURS,
                   title="Spending by category over time")
    area.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10), legend_title=None)
    st.plotly_chart(area, width="stretch")

# ------------------------------------------------------------------ budgets
with tab_budget:
    bs = an.budget_status(df, month, budgets)
    total_budget, total_spent = bs["budget"].sum(), bs["spent"].sum()
    g1, g2 = st.columns([1, 2])
    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=total_spent, delta={"reference": total_budget, "increasing": {"color": "#DC2626"},
                                                              "decreasing": {"color": "#16A34A"}},
        number={"prefix": "₹", "valueformat": ",.0f"}, title={"text": "Total spent vs total budget"},
        gauge={"axis": {"range": [0, max(total_budget, total_spent) * 1.2]}, "bar": {"color": "#0F766E"},
               "threshold": {"line": {"color": "#DC2626", "width": 4}, "value": total_budget}}))
    gauge.update_layout(height=320, margin=dict(l=20, r=20, t=60, b=10))
    g1.plotly_chart(gauge, width="stretch")
    with g2:
        st.markdown(f"#### Category budgets: {an.month_label(month)}")
        icons = {"Over budget": "🔴", "Will overspend": "🟠", "Warning": "🟡", "On track": "🟢"}
        for r in bs.itertuples():
            a, b = st.columns([3, 2])
            a.progress(min(r.used_pct / 100, 1.0), text=f"{icons[r.status]} **{r.category}**: "
                                                         f"₹{r.spent:,.0f} of ₹{r.budget:,.0f} ({r.used_pct:.0f}%)")
            b.caption(f"{r.status} · projected ₹{r.projected:,.0f}" if r.status != "On track"
                      else f"₹{max(r.remaining, 0):,.0f} left")
    with st.expander("✏️ Edit monthly budgets"):
        cols = st.columns(5)
        new = {c: cols[i % 5].number_input(c, 0, 100000, int(budgets.get(c, 0)), 500, key=f"b_{c}")
               for i, c in enumerate([c for c in CATEGORIES if c != "Others"])}
        if st.button("Save budgets", type="primary"):
            an.save_budgets({k: v for k, v in new.items() if v > 0})
            st.success("Budgets saved to data/budgets.json")
            st.rerun()

# ------------------------------------------------------------------ insights
with tab_insight:
    i1, i2 = st.columns([3, 2])
    with i1:
        st.markdown("#### What your data says")
        for line in an.insights(df, month, budgets):
            st.markdown(f'<div class="insight">{line}</div>', unsafe_allow_html=True)
        st.markdown("#### 🔍 Unusual expenses (all months)")
        anomalies = an.detect_anomalies(df)
        if anomalies.empty:
            st.success("No unusual spending detected.")
        else:
            st.dataframe(anomalies.assign(date=anomalies["date"].dt.strftime("%d %b %Y")), hide_index=True,
                         width="stretch", column_config={
                             "amount": st.column_config.NumberColumn("Amount", format="₹%d"),
                             "typical": st.column_config.NumberColumn("Typical", format="₹%d"),
                             "times_typical": st.column_config.NumberColumn("× typical", format="%.1f×")})
            st.caption("Detected with a robust z-score (median and MAD) per category, so one big purchase "
                       "doesn't hide another.")
    with i2:
        f = an.forecast_next_month(df)
        if f["forecast"]:
            st.metric("🔮 Forecast for next month", f"₹{f['forecast']:,.0f}",
                      f"{f['trend_per_month']:+,.0f} ₹/month trend", delta_color="inverse")
            st.caption(f"Linear trend over {f['based_on']} complete months, blended with the 3-month average; "
                       f"{f['excluded']} one-off expenses excluded.")
        tm = an.top_merchants(m, 6)
        tm["label"] = tm["visits"].map(lambda v: f"{v} visit" + ("s" if v != 1 else ""))
        bar = px.bar(tm.sort_values("total"), x="total", y="description", orientation="h", text="label",
                     title="Top places you spend at", color_discrete_sequence=["#0F766E"])
        bar.update_traces(textposition="outside")
        bar.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="₹", yaxis_title=None)
        st.plotly_chart(bar, width="stretch")
        wk = an.weekday_pattern(df)
        wbar = px.bar(wk, x="weekday", y="avg_per_week", title="Average spend by weekday (all months)",
                      color=wk["weekday"].isin(["Saturday", "Sunday"]).map({True: "Weekend", False: "Weekday"}),
                      color_discrete_map={"Weekend": "#F59E0B", "Weekday": "#0F766E"})
        wbar.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10), legend_title=None, xaxis_title=None)
        st.plotly_chart(wbar, width="stretch")
        pay = an.payment_split(m)
        ppie = px.pie(pay, names="payment_method", values="amount", hole=.5, title="How you pay",
                      color_discrete_sequence=px.colors.sequential.Teal_r)
        ppie.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(ppie, width="stretch")

# ------------------------------------------------------------------ transactions
with tab_txn:
    f1, f2, f3 = st.columns([2, 2, 1])
    query = f1.text_input("🔎 Search description")
    cat_filter = f2.multiselect("Category", sorted(df["category"].unique()))
    scope = f3.radio("Show", ["This month", "All"], horizontal=True)
    view = m if scope == "This month" else df
    if query:
        view = view[view["description"].str.contains(query, case=False)]
    if cat_filter:
        view = view[view["category"].isin(cat_filter)]
    st.caption(f"{len(view)} transactions · total ₹{an.expenses(view)['amount'].sum():,.0f} spent. "
               "Edit cells and press Save; tick rows in 'delete' to remove them.")
    editable = view[["id", "date", "description", "category", "amount", "payment_method", "type"]].copy()
    editable["delete"] = False
    edited = st.data_editor(editable, hide_index=True, width="stretch", disabled=["id"], height=420,
                            column_config={
                                "date": st.column_config.DateColumn(format="DD MMM YYYY"),
                                "category": st.column_config.SelectboxColumn(options=CATEGORIES + INCOME_CATEGORIES),
                                "payment_method": st.column_config.SelectboxColumn(options=METHODS),
                                "type": st.column_config.SelectboxColumn(options=["expense", "income"]),
                                "amount": st.column_config.NumberColumn(format="₹%.0f", min_value=1)})
    if st.button("💾 Save changes", type="primary"):
        changed = deleted = 0
        original = editable.set_index("id")
        for row in edited.itertuples(index=False):
            if row.delete:
                store.delete(row.id)
                deleted += 1
                continue
            o = original.loc[row.id]
            fields = {k: getattr(row, k) for k in ["date", "description", "category", "amount", "payment_method", "type"]
                      if getattr(row, k) != o[k]}
            if fields:
                if "date" in fields:
                    fields["date"] = pd.Timestamp(fields["date"]).date()
                store.update(row.id, **fields)
                changed += 1
        st.success(f"Updated {changed}, deleted {deleted}.")
        st.rerun()

# ------------------------------------------------------------------ import
with tab_import:
    st.markdown("Upload a CSV bank statement with at least **date, description, amount** columns. Missing categories "
                "are filled in automatically, and rows that already exist are skipped.")
    up = st.file_uploader("CSV file", type="csv")
    if up:
        raw = pd.read_csv(up)
        preview = raw.rename(columns=str.lower).copy()
        if {"description", "amount"} <= set(preview.columns):
            if "category" not in preview.columns:
                preview["category"] = preview["description"].map(categorize)
            st.dataframe(preview.head(20), hide_index=True, width="stretch")
            if st.button("Import these transactions", type="primary"):
                added, skipped = store.import_dataframe(raw)
                st.success(f"Imported {added} transactions, skipped {skipped} duplicates.")
        else:
            st.error("The CSV needs 'date', 'description' and 'amount' columns.")
    st.download_button("⬇️ Download a template CSV",
                       "date,description,amount,payment_method,type\n2026-11-20,Swiggy order,420,UPI,expense\n"
                       "2026-11-20,Uber ride,260,UPI,expense\n", "statement_template.csv")

# ------------------------------------------------------------------ reports
with tab_report:
    st.markdown(f"#### Reports for {an.month_label(month)}")
    r1, r2, r3 = st.columns(3)
    r1.download_button("📊 Excel workbook (with charts)", excel_report(df, budgets, month),
                       f"expense_report_{month}.xlsx", width="stretch")
    r2.download_button("📄 PDF monthly statement", pdf_report(df, budgets, month),
                       f"monthly_statement_{month}.pdf", "application/pdf", width="stretch")
    r3.download_button("🧾 All transactions (CSV)",
                       df.assign(date=df["date"].dt.strftime("%Y-%m-%d")).drop(columns=["id"]).to_csv(index=False),
                       "all_transactions.csv", "text/csv", width="stretch")
    st.dataframe(an.monthly_totals(df).assign(month=lambda d: d["month"].map(an.month_label)), hide_index=True,
                 width="stretch", column_config={c: st.column_config.NumberColumn(format="₹%.0f")
                                                 for c in ["income", "expense", "savings"]})
