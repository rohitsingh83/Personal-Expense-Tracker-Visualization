import unittest
import sqlite3
import tempfile
from pathlib import Path
import pandas as pd

from src.categorize import categorize_transaction
from src.models import init_db, get_connection
from src.ingest import ingest_csv
from src.analyze import load_transactions_df, compute_kpis
from src.budget import seed_budgets, check_budgets
from src.plots import generate_all_charts
from src.report import export_excel_report

ROOT = Path(__file__).resolve().parent.parent


class TestExpenseTracker(unittest.TestCase):
    def test_categorization_rules(self):
        self.assertEqual(categorize_transaction("Swiggy Dinner Order", -340), "Food & Dining")
        self.assertEqual(categorize_transaction("Zomato Pizza Delivery", -550), "Food & Dining")
        self.assertEqual(categorize_transaction("Monthly Stipend", 25000), "Income")
        self.assertEqual(categorize_transaction("DMart Grocery", -1500), "Groceries")
        self.assertEqual(categorize_transaction("Uber Cab Ride", -320), "Transport")
        self.assertEqual(categorize_transaction("Electricity Bill Payment", -1200), "Bills & Utilities")
        self.assertEqual(categorize_transaction("Amazon Shopping Order", -2499), "Shopping")
        self.assertEqual(categorize_transaction("Netflix Subscription", -499), "Entertainment")
        self.assertEqual(categorize_transaction("Miscellaneous Expense", -100), "Uncategorized")

    def test_ingestion_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_expenses.db"
            conn = get_connection(db_path)
            sample_csv = ROOT / "data" / "sample_expenses.csv"

            # First ingestion should insert rows
            inserted_first = ingest_csv(sample_csv, conn)
            self.assertGreater(inserted_first, 0)

            # Re-ingesting same file should be idempotent (0 new rows)
            inserted_second = ingest_csv(sample_csv, conn)
            self.assertEqual(inserted_second, 0)

            df = load_transactions_df(conn)
            self.assertEqual(len(df), inserted_first)
            conn.close()

    def test_kpis_and_budgets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_expenses.db"
            conn = get_connection(db_path)
            ingest_csv(ROOT / "data" / "sample_expenses.csv", conn)
            df = load_transactions_df(conn)

            kpis = compute_kpis(df)
            self.assertIn("total_income", kpis)
            self.assertIn("total_spend", kpis)
            self.assertIn("net_savings", kpis)
            self.assertGreater(kpis["total_income"], 0)
            self.assertGreater(kpis["total_spend"], 0)

            month = sorted(df["month"].unique())[-1]
            seed_budgets(conn, month)
            budget_df = check_budgets(df, conn, month)
            self.assertIn("status", budget_df.columns)
            self.assertIn("over_by", budget_df.columns)
            conn.close()

    def test_charts_and_excel_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "test_expenses.db"
            conn = get_connection(db_path)
            ingest_csv(ROOT / "data" / "sample_expenses.csv", conn)
            df = load_transactions_df(conn)
            month = sorted(df["month"].unique())[-1]
            seed_budgets(conn, month)
            budget_df = check_budgets(df, conn, month)

            # Test chart generation
            images_dir = tmp_path / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            generate_all_charts(df, images_dir)
            self.assertTrue((images_dir / "category_spending_bar.png").exists())
            self.assertTrue((images_dir / "category_donut.png").exists())
            self.assertTrue((images_dir / "monthly_trend_line.png").exists())
            self.assertTrue((images_dir / "payment_method_pie.png").exists())

            # Test Excel report export
            xlsx_path = tmp_path / "test_report.xlsx"
            export_excel_report(df, budget_df, xlsx_path)
            self.assertTrue(xlsx_path.exists())
            self.assertGreater(xlsx_path.stat().st_size, 1000)
            conn.close()


if __name__ == "__main__":
    unittest.main()
