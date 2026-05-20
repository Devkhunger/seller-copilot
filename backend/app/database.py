import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv("DATABASE_URL", str(BASE_DIR / "seller_copilot.db"))


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS order_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_date TEXT,
                sku TEXT NOT NULL,
                product_name TEXT,
                customer_state TEXT,
                status TEXT,
                order_source TEXT,
                listed_price REAL DEFAULT 0,
                discounted_price REAL DEFAULT 0,
                quantity INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                category TEXT DEFAULT 'daily',
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                done_at TEXT
            );

            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                current_stock INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                detail TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def log_usage(event_type: str, detail: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usage_logs (event_type, detail) VALUES (?, ?)",
            (event_type, detail),
        )

