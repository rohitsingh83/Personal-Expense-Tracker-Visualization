"""
SQLite storage for transactions: add, edit, delete, import and query.

Why a database instead of only CSV?
  - safe concurrent edits from the CLI and the dashboard
  - a UNIQUE rule stops the same bank statement being imported twice
  - fast filtering with SQL
"""

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from .categorizer import categorize

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "expenses.db"
SAMPLE_CSV = ROOT / "data" / "expenses.csv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL,
    description    TEXT NOT NULL,
    category       TEXT NOT NULL,
    amount         REAL NOT NULL CHECK (amount > 0),
    payment_method TEXT NOT NULL DEFAULT 'UPI',
    type           TEXT NOT NULL DEFAULT 'expense' CHECK (type IN ('expense', 'income')),
    UNIQUE (date, description, amount, type)
);
"""

REQUIRED = ["date", "description", "amount"]


class ExpenseStore:
    def __init__(self, path: Path = DB_PATH, seed_sample: bool = True):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        if seed_sample and self.count() == 0 and SAMPLE_CSV.exists():
            self.import_csv(SAMPLE_CSV)

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]

    def add(self, txn_date: date | str, description: str, amount: float, category: str | None = None,
            payment_method: str = "UPI", txn_type: str = "expense") -> int:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        if not description.strip():
            raise ValueError("Description is required")
        category = category or categorize(description, txn_type)
        cur = self.conn.execute(
            "INSERT INTO transactions (date, description, category, amount, payment_method, type) VALUES (?,?,?,?,?,?)",
            (str(txn_date), description.strip(), category, float(amount), payment_method, txn_type))
        self.conn.commit()
        return cur.lastrowid

    def update(self, txn_id: int, **fields) -> None:
        allowed = {"date", "description", "category", "amount", "payment_method", "type"}
        sets = {k: v for k, v in fields.items() if k in allowed}
        if not sets:
            return
        self.conn.execute(f"UPDATE transactions SET {', '.join(f'{k}=?' for k in sets)} WHERE id=?",
                          (*[str(v) if k == "date" else v for k, v in sets.items()], txn_id))
        self.conn.commit()

    def delete(self, txn_id: int) -> None:
        self.conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
        self.conn.commit()

    def import_dataframe(self, df: pd.DataFrame) -> tuple[int, int]:
        """Import rows; missing categories are auto-filled. Returns (added, duplicates skipped)."""
        df = df.rename(columns=str.lower)
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(missing)}")
        df = df.copy()
        df["type"] = df.get("type", "expense")
        df["type"] = df["type"].fillna("expense").str.lower()
        df["payment_method"] = df.get("payment_method", "UPI")
        df["payment_method"] = df["payment_method"].fillna("UPI")
        df["date"] = pd.to_datetime(df["date"], dayfirst=False).dt.strftime("%Y-%m-%d")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").abs()
        df = df.dropna(subset=["amount"])
        if "category" not in df.columns:
            df["category"] = None
        df["category"] = [c if isinstance(c, str) and c.strip() else categorize(d, t)
                          for c, d, t in zip(df["category"], df["description"], df["type"])]
        before = self.count()
        self.conn.executemany(
            "INSERT OR IGNORE INTO transactions (date, description, category, amount, payment_method, type)"
            " VALUES (?,?,?,?,?,?)",
            df[["date", "description", "category", "amount", "payment_method", "type"]].itertuples(index=False))
        self.conn.commit()
        added = self.count() - before
        return added, len(df) - added

    def import_csv(self, path: Path) -> tuple[int, int]:
        return self.import_dataframe(pd.read_csv(path))

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC, id DESC", self.conn)
        df["date"] = pd.to_datetime(df["date"])
        return df

    def close(self) -> None:
        self.conn.close()
