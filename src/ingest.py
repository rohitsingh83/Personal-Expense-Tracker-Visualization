"""CSV ingestion, cleaning, and SQLite upsert."""

import sqlite3
from pathlib import Path
import pandas as pd
from src.categorize import categorize_transaction


def ingest_csv(csv_path: Path, conn: sqlite3.Connection) -> int:
    df = pd.read_csv(csv_path)
    df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["tx_date", "description", "amount"])

    cur = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        cat = categorize_transaction(str(row["description"]), float(row["amount"]))
        cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
        cur.execute("SELECT id FROM categories WHERE name = ?", (cat,))
        cat_id = cur.fetchone()[0]

        cur.execute(
            """INSERT OR IGNORE INTO transactions
               (tx_date, description, amount, payment_method, account, category_id, raw_source)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                row["tx_date"],
                str(row["description"]).strip(),
                float(row["amount"]),
                str(row.get("payment_method", "UPI")),
                str(row.get("account", "Primary")),
                cat_id,
                str(row.get("raw_source", csv_path.name)),
            ),
        )
        inserted += cur.rowcount
    conn.commit()
    return inserted
