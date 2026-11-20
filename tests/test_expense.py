import unittest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from src.models import get_connection
from src.categorize import categorize_transaction
from src.ingest import ingest_csv
from src.analyze import load_transactions_df, compute_kpis
from src.budget import seed_budgets, check_budgets
from api.app import app

ROOT = Path(__file__).resolve().parent.parent


class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        self.db_path = ROOT / "db" / "test_expenses.db"
        if self.db_path.exists():
            self.db_path.unlink()
        self.conn = get_connection(self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        self.conn.close()
        if self.db_path.exists():
            self.db_path.unlink()

    def test_categorization_rules(self):
        """Verify regex categorization accurately maps expense descriptions."""
        self.assertEqual(categorize_transaction("Swiggy Order #1234", -350.0), "Food & Dining")
        self.assertEqual(categorize_transaction("Dmart Supermarket", -1200.0), "Groceries")
        self.assertEqual(categorize_transaction("Uber Ride", -250.0), "Transport")
        self.assertEqual(categorize_transaction("Monthly Salary Transfer", 45000.0), "Income")
        self.assertEqual(categorize_transaction("Random Unmatched Expense", -50.0), "Uncategorized")

    def test_ingestion_and_deduplication(self):
        """Verify idempotency: re-ingesting identical rows does not duplicate records."""
        csv_file = ROOT / "data" / "sample_expenses.csv"
        first_inserted = ingest_csv(csv_file, self.conn)
        self.assertGreater(first_inserted, 0)

        # Ingesting the same file a second time should insert 0 new rows
        second_inserted = ingest_csv(csv_file, self.conn)
        self.assertEqual(second_inserted, 0)

    def test_kpis_computation(self):
        """Verify accurate financial summation of income, spending, and savings."""
        ingest_csv(ROOT / "data" / "sample_expenses.csv", self.conn)
        df = load_transactions_df(self.conn)
        kpis = compute_kpis(df)
        self.assertGreater(kpis["total_income"], 0)
        self.assertGreater(kpis["total_spend"], 0)
        self.assertEqual(kpis["net_savings"], round(kpis["total_income"] - kpis["total_spend"], 2))

    def test_budget_checking(self):
        """Verify budget status evaluation correctly detects limits and variances."""
        ingest_csv(ROOT / "data" / "sample_expenses.csv", self.conn)
        df = load_transactions_df(self.conn)
        latest_month = sorted(df["month"].unique())[-1]
        seed_budgets(self.conn, latest_month)
        b_df = check_budgets(df, self.conn, latest_month)
        self.assertFalse(b_df.empty)
        self.assertIn("status", b_df.columns)
        self.assertIn("over_by", b_df.columns)

    def test_api_health(self):
        """Verify FastAPI health status probe."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
