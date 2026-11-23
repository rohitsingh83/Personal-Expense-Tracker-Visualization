"""Build the GitHub Pages report: python scripts/build_site.py  -> docs/index.html"""

import sys
import tempfile
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import plotly.express as px
import plotly.graph_objects as go

from site_template import fig_html, page, table_html
from src import analysis as an
from src.storage import ExpenseStore

TODAY = date(2026, 11, 21)
MONTH = "2026-10"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ExpenseStore(Path(tmp) / "site.db")      # fresh copy of the sample data
        df = store.to_dataframe()
        store.close()
    budgets = an.load_budgets()
    s_all, m = an.summary(df), an.month_slice(df, MONTH)
    s = an.summary(m)

    mt = an.monthly_totals(df)
    labels = [an.month_label(x) for x in mt["month"]]
    inc = go.Figure()
    inc.add_bar(x=labels, y=mt["income"], name="Income", marker_color="#14B8A6")
    inc.add_bar(x=labels, y=mt["expense"], name="Expenses", marker_color="#EF4444")
    inc.add_scatter(x=labels, y=mt["savings_rate"], name="Savings rate %", yaxis="y2", line=dict(color="#e2e8f0"))
    inc.update_layout(title="Income vs expenses", barmode="group",
                      yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Savings %"))

    cats = an.category_breakdown(m)
    donut = px.pie(cats, names="category", values="total", hole=.55, title=f"Where the money went: {an.month_label(MONTH)}")
    bs = an.budget_status(df, MONTH, budgets, TODAY)
    colours = {"Over budget": "#EF4444", "Will overspend": "#F59E0B", "Warning": "#F59E0B", "On track": "#14B8A6"}
    bud = px.bar(bs.sort_values("used_pct"), x="used_pct", y="category", color="status", orientation="h",
                 color_discrete_map=colours, title="Budget used (%)", text="used_pct")
    bud.add_vline(100, line_dash="dash")
    trend = an.category_by_month(df).reset_index().melt(id_vars="month", var_name="category", value_name="amount")
    area = px.area(trend, x="month", y="amount", color="category", title="Spending by category over time")

    anomalies = an.detect_anomalies(df).assign(date=lambda d: d["date"].dt.strftime("%d %b %Y"))
    f = an.forecast_next_month(df, TODAY)
    insights = "".join(f"<li>{escape(x)}</li>" for x in an.insights(df, MONTH, budgets, TODAY))
    html = page(
        title="Personal Expense Tracker",
        tagline="Six months of transactions turned into budgets, plain-English insights, anomaly detection and a "
                "next-month forecast.",
        accent="#2DD4BF", repo="Personal-Expense-Tracker-Visualization",
        kpis=[("Transactions", str(len(df))), ("Total spent (6 mo)", f"₹{s_all['expense']:,.0f}"),
              ("Overall savings rate", f"{s_all['savings_rate']:.0f}%"), ("Unusual expenses found", str(len(anomalies))),
              ("Forecast next month", f"₹{f['forecast']:,.0f}")],
        sections=[
            ("Monthly overview", "Income, expenses and savings rate per month.", fig_html(inc, 420)),
            (f"{an.month_label(MONTH)} in detail", f"Spent ₹{s['expense']:,.0f} of ₹{s['income']:,.0f} income "
             f"({s['savings_rate']:.0f}% saved).", f'<div class="grid2">{fig_html(donut, 420)}{fig_html(bud, 420)}</div>'),
            ("Auto-generated insights", f"What the analysis says about {an.month_label(MONTH)}.",
             f'<ul class="list">{insights}</ul>'),
            ("Unusual expenses", "Robust z-score (median + MAD) per category: both planted outliers found, no false alarms.",
             table_html(anomalies)),
            ("Category trends", "Stacked spending by category.", fig_html(area, 420)),
        ],
        note="Transactions are simulated by scripts/generate_sample_data.py (a fictional Bengaluru professional).",
        run_cmds=["pip install -r requirements.txt", "python main.py summary --month 2026-10",
                  "python main.py report --month 2026-10", "streamlit run app.py"])
    out = ROOT / "docs" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
