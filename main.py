"""
Personal Expense Tracker: command-line tool.

    python main.py summary                       overview of the latest month
    python main.py summary --month 2026-09       a specific month
    python main.py add 450 "Swiggy dinner"       add an expense (category is guessed)
    python main.py add 1200 "Petrol" --category Transport --method "Credit Card" --date 2026-11-20
    python main.py add 5000 "Freelance logo" --income
    python main.py list --last 15                recent transactions
    python main.py import my_statement.csv       import a bank statement (duplicates skipped)
    python main.py report --month 2026-10        Excel + PDF report + charts
    python main.py budget "Food & Dining" 8000   change a monthly budget
"""

import argparse
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import analysis as an
from src.categorizer import CATEGORIES
from src.charts import all_charts
from src.report import save_reports
from src.storage import ExpenseStore

ROOT = Path(__file__).resolve().parent
console = Console()
STATUS = {"Over budget": "red", "Will overspend": "yellow", "Warning": "yellow", "On track": "green"}


def latest_month(df) -> str:
    return an.months_available(df)[-1]


def cmd_summary(args, store):
    df = store.to_dataframe()
    month = args.month or latest_month(df)
    m = an.month_slice(df, month)
    s = an.summary(m)
    console.print(Panel.fit(
        f"Income  [green]₹{s['income']:,.0f}[/]    Spent  [red]₹{s['expense']:,.0f}[/]    "
        f"Saved  [bold]₹{s['savings']:,.0f}[/] ({s['savings_rate']:.0f}%)\n"
        f"{s['transactions']} expenses · average ₹{s['avg_daily_spend']:,.0f}/day · top category: {s['top_category']}",
        title=f"💰 {an.month_label(month)}", border_style="cyan"))

    t = Table(title="Spending by category", header_style="bold white on dark_cyan")
    for col in ["Category", "Spent", "Share", "Budget", "Used", "Status"]:
        t.add_column(col, justify="right" if col not in {"Category", "Status"} else "left")
    cats = an.category_breakdown(m).set_index("category")
    for r in an.budget_status(df, month, an.load_budgets()).itertuples():
        share = cats["share"].get(r.category, 0)
        t.add_row(r.category, f"₹{r.spent:,.0f}", f"{share:.0f}%", f"₹{r.budget:,.0f}", f"{r.used_pct:.0f}%",
                  f"[{STATUS[r.status]}]{r.status}[/]")
    console.print(t)

    console.print("\n[bold]Insights[/]")
    for line in an.insights(df, month, an.load_budgets()):
        console.print(f"  {line}")
    f = an.forecast_next_month(df)
    if f["forecast"]:
        console.print(f"\n🔮 Forecast for next month: [bold]₹{f['forecast']:,.0f}[/] "
                      f"(trend {f['trend_per_month']:+,.0f} ₹/month over {f['based_on']} months, "
                      f"{f['excluded']} one-off expenses excluded)")


def cmd_add(args, store):
    txn_type = "income" if args.income else "expense"
    txn_id = store.add(args.date, args.description, args.amount, args.category, args.method, txn_type)
    row = store.to_dataframe().set_index("id").loc[txn_id]
    console.print(f"[green]✔ Added #{txn_id}[/]: {row.description} ₹{row.amount:,.0f} → [bold]{row.category}[/] "
                  f"({row.payment_method}, {row.date:%d %b %Y})")


def cmd_list(args, store):
    df = store.to_dataframe().head(args.last)
    t = Table(header_style="bold white on dark_cyan")
    for col in ["#", "Date", "Description", "Category", "Method", "Amount"]:
        t.add_column(col, justify="right" if col in {"#", "Amount"} else "left")
    for r in df.itertuples():
        colour = "green" if r.type == "income" else "white"
        t.add_row(str(r.id), f"{r.date:%d %b}", r.description, r.category, r.payment_method,
                  f"[{colour}]{'+' if r.type == 'income' else ''}₹{r.amount:,.0f}[/]")
    console.print(t)


def cmd_import(args, store):
    added, skipped = store.import_csv(Path(args.file))
    console.print(f"[green]Imported {added} new transactions[/], skipped {skipped} duplicates.")


def cmd_report(args, store):
    df = store.to_dataframe()
    month = args.month or latest_month(df)
    budgets = an.load_budgets()
    paths = save_reports(df, budgets, month, ROOT / "outputs")
    charts = all_charts(df, month, budgets, ROOT / "images")
    console.print(f"[bold]Reports for {an.month_label(month)}[/]")
    for p in list(paths.values()) + list(charts.values()):
        console.print(f"  - {p.relative_to(ROOT)}")


def cmd_budget(args, store):
    budgets = an.load_budgets()
    budgets[args.category] = args.amount
    an.save_budgets(budgets)
    console.print(f"Budget for {args.category} set to ₹{args.amount:,.0f}/month")


def main():
    p = argparse.ArgumentParser(description="Personal Expense Tracker")
    sub = p.add_subparsers(dest="command")
    s = sub.add_parser("summary")
    s.add_argument("--month", help="YYYY-MM")
    s = sub.add_parser("add")
    s.add_argument("amount", type=float)
    s.add_argument("description")
    s.add_argument("--category", choices=CATEGORIES)
    s.add_argument("--method", default="UPI")
    s.add_argument("--date", default=date.today().isoformat())
    s.add_argument("--income", action="store_true")
    s = sub.add_parser("list")
    s.add_argument("--last", type=int, default=15)
    s = sub.add_parser("import")
    s.add_argument("file")
    s = sub.add_parser("report")
    s.add_argument("--month", help="YYYY-MM")
    s = sub.add_parser("budget")
    s.add_argument("category")
    s.add_argument("amount", type=float)
    args = p.parse_args()
    if args.command is None:
        args = p.parse_args(["summary"])

    store = ExpenseStore()
    {"summary": cmd_summary, "add": cmd_add, "list": cmd_list, "import": cmd_import,
     "report": cmd_report, "budget": cmd_budget}[args.command](args, store)
    store.close()


if __name__ == "__main__":
    main()
