"""Main execution pipeline for Personal Expense Tracker with Data Visualization."""

from pathlib import Path
from src.models import get_connection
from src.ingest import ingest_csv
from src.analyze import load_transactions_df, compute_kpis
from src.budget import seed_budgets, check_budgets
from src.plots import generate_all_charts
from src.report import export_excel_report

ROOT = Path(__file__).resolve().parent


def main() -> None:
    conn = get_connection(ROOT / "db" / "expenses.db")
    inserted = ingest_csv(ROOT / "data" / "sample_expenses.csv", conn)
    df = load_transactions_df(conn)
    kpis = compute_kpis(df)

    latest_month = sorted(df["month"].unique())[-1]
    seed_budgets(conn, latest_month)
    budget_df = check_budgets(df, conn, latest_month)

    generate_all_charts(df, ROOT / "images")
    export_excel_report(df, budget_df, ROOT / "outputs" / "expense_report.xlsx")
    budget_df.to_csv(ROOT / "reports" / "budget_alerts.csv", index=False)

    print("=== Personal Expense Tracker Summary ===")
    print(f"Newly ingested rows: {inserted} | Total rows in DB: {len(df)}")
    print(f"Income: INR {kpis['total_income']:,.2f} | Spend: INR {kpis['total_spend']:,.2f} | Savings: INR {kpis['net_savings']:,.2f}")
    print(f"Top Category: {kpis['top_category']} | Avg Daily Spend: INR {kpis['avg_daily_spend']:,.2f}")
    print(f"\n--- Budget Status ({latest_month}) ---")
    print(budget_df.to_string(index=False))
    conn.close()


if __name__ == "__main__":
    main()
