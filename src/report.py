"""
Reports you can share or keep:

- Excel workbook: transactions, monthly summary, categories, budget, anomalies,
  with native Excel charts (they stay interactive in Excel)
- PDF monthly statement: KPIs, insights, charts and the biggest expenses
"""

import re
from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from fpdf import FPDF

from . import analysis as an
from .charts import all_charts


def excel_report(df: pd.DataFrame, budgets: dict, month: str, today: date | None = None) -> bytes:
    buf = BytesIO()
    monthly = an.monthly_totals(df)
    cats = an.category_breakdown(df)
    budget = an.budget_status(df, month, budgets, today)
    anomalies = an.detect_anomalies(df)
    txns = df.sort_values("date").assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d")).drop(columns=["id"])
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        book = xw.book
        money = book.add_format({"num_format": "₹#,##0"})
        header = book.add_format({"bold": True, "bg_color": "#0F766E", "font_color": "white"})
        for name, frame in [("Monthly summary", monthly), ("Categories", cats), (f"Budget {month}", budget),
                            ("Unusual spending", anomalies.assign(date=anomalies["date"].astype(str))
                             if not anomalies.empty else anomalies), ("Transactions", txns)]:
            frame.to_excel(xw, sheet_name=name, index=False)
            sheet = xw.sheets[name]
            for i, col in enumerate(frame.columns):
                sheet.write(0, i, col, header)
                sheet.set_column(i, i, max(12, min(40, len(str(col)) + 4)),
                                 money if col in {"income", "expense", "savings", "total", "average", "amount",
                                                  "budget", "spent", "remaining", "projected", "typical"} else None)
        n = len(monthly)
        chart = book.add_chart({"type": "column"})
        for col, colour in [(1, "#14B8A6"), (2, "#EF4444")]:
            chart.add_series({"name": ["Monthly summary", 0, col], "categories": ["Monthly summary", 1, 0, n, 0],
                              "values": ["Monthly summary", 1, col, n, col], "fill": {"color": colour}})
        chart.set_title({"name": "Income vs expenses"})
        xw.sheets["Monthly summary"].insert_chart("H2", chart, {"x_scale": 1.4, "y_scale": 1.3})
        pie = book.add_chart({"type": "doughnut"})
        pie.add_series({"name": "Spending by category", "categories": ["Categories", 1, 0, len(cats), 0],
                        "values": ["Categories", 1, 1, len(cats), 1]})
        pie.set_title({"name": "Spending by category"})
        xw.sheets["Categories"].insert_chart("H2", pie, {"x_scale": 1.3, "y_scale": 1.3})
    return buf.getvalue()


class _PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", size=8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 8, f"Personal Expense Tracker · page {self.page_no()}", align="C")


def _font_path() -> str:
    import matplotlib
    return str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf")


def pdf_report(df: pd.DataFrame, budgets: dict, month: str, today: date | None = None) -> bytes:
    m = an.month_slice(df, month)
    s = an.summary(m)
    pdf = _PDF()
    pdf.add_font("DejaVu", "", _font_path())
    pdf.add_font("DejaVu", "B", _font_path().replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"))
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(15, 118, 110)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_xy(12, 8)
    pdf.cell(0, 10, f"Monthly statement: {an.month_label(month)}")
    pdf.set_font("DejaVu", size=10)
    pdf.set_xy(12, 19)
    pdf.cell(0, 6, f"{s['transactions']} expenses · generated {date.today():%d %b %Y}")

    pdf.set_text_color(15, 23, 42)
    pdf.set_y(40)
    boxes = [("Income", f"₹{s['income']:,.0f}"), ("Spent", f"₹{s['expense']:,.0f}"),
             ("Saved", f"₹{s['savings']:,.0f}"), ("Savings rate", f"{s['savings_rate']:.0f}%")]
    for i, (label, value) in enumerate(boxes):
        x = 12 + i * 47
        pdf.set_fill_color(240, 253, 250)
        pdf.rect(x, 40, 44, 22, "F")
        pdf.set_xy(x + 3, 42)
        pdf.set_font("DejaVu", size=8)
        pdf.cell(38, 5, label.upper())
        pdf.set_xy(x + 3, 49)
        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(38, 8, value)

    pdf.set_y(70)
    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 8, "Insights", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", size=10)
    for line in an.insights(df, month, budgets, today):
        clean = re.sub(r"[\U00010000-\U0010FFFF\u2600-\u27BF\uFE0F]", "", line).strip()  # emoji the font lacks
        pdf.multi_cell(0, 6, f"•  {clean}", new_x="LMARGIN", new_y="NEXT")

    with TemporaryDirectory() as tmp:
        charts = all_charts(df, month, budgets, Path(tmp))
        pdf.ln(3)
        y = pdf.get_y()
        pdf.image(str(charts["donut"]), x=10, y=y, w=95)
        pdf.image(str(charts["budget"]), x=105, y=y + 2, w=95)
        pdf.add_page()
        pdf.image(str(charts["monthly"]), x=15, y=15, w=180)
        pdf.image(str(charts["trend"]), x=15, y=110, w=180)
        pdf.set_y(205)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 8, "Biggest expenses this month", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", size=9)
    top = an.expenses(m).nlargest(8, "amount")
    for r in top.itertuples():
        pdf.cell(28, 6, f"{r.date:%d %b}")
        pdf.cell(85, 6, r.description[:45])
        pdf.cell(45, 6, r.category)
        pdf.cell(25, 6, f"₹{r.amount:,.0f}", align="R", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def save_reports(df: pd.DataFrame, budgets: dict, month: str, folder: Path, today: date | None = None) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = {"excel": folder / f"expense_report_{month}.xlsx", "pdf": folder / f"monthly_statement_{month}.pdf",
             "csv": folder / "all_transactions.csv"}
    paths["excel"].write_bytes(excel_report(df, budgets, month, today))
    paths["pdf"].write_bytes(pdf_report(df, budgets, month, today))
    df.sort_values("date").assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d")).drop(columns=["id"]).to_csv(
        paths["csv"], index=False)
    return paths
