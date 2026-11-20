"""SQLite schema initialization for Personal Expense Tracker."""

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    payment_method TEXT NOT NULL,
    account TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    raw_source TEXT,
    UNIQUE(tx_date, description, amount, account),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    category_name TEXT NOT NULL,
    limit_amount REAL NOT NULL,
    UNIQUE(month, category_name)
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    return conn


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with required tables and return connection."""
    return get_connection(db_path)
