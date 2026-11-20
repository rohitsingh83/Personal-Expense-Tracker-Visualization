"""High-performance batch CSV ingestion and SQLite persistence."""

import sqlite3
from pathlib import Path
import pandas as pd
from src.categorize import categorize_transaction


def ingest_csv(csv_path: Path, conn: sqlite3.Connection) -> int:
    """Ingest, clean, and bulk-insert transactions into SQLite using executemany.
    
    Args:
        csv_path: Path to the transactions CSV statement.
        conn: Open SQLite database connection.
        
    Returns:
        Count of newly inserted transaction records.
    """
    df = pd.read_csv(csv_path)
    df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["tx_date", "description", "amount"]).copy()

    cur = conn.cursor()
    
    # 1. Pre-categorize in memory
    df["category"] = [categorize_transaction(str(d), float(a)) for d, a in zip(df["description"], df["amount"])]
    
    # 2. Bulk register categories
    unique_cats = df["category"].unique().tolist()
    cur.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(c,) for c in unique_cats])
    
    # 3. Cache category mappings
    cur.execute("SELECT id, name FROM categories")
    cat_map = {name: cid for cid, name in cur.fetchall()}
    df["category_id"] = df["category"].map(cat_map)
    
    # 4. Bulk insert transactions
    tx_tuples = [
        (
            row["tx_date"],
            str(row["description"]).strip(),
            float(row["amount"]),
            str(row.get("payment_method", "UPI")),
            str(row.get("account", "Primary")),
            int(row["category_id"]),
            str(row.get("raw_source", csv_path.name)),
        )
        for _, row in df.iterrows()
    ]
    
    initial_count = cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    cur.executemany(
        """INSERT OR IGNORE INTO transactions
           (tx_date, description, amount, payment_method, account, category_id, raw_source)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        tx_tuples,
    )
    final_count = cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.commit()
    
    return final_count - initial_count
