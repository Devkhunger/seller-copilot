
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv("DATABASE_URL", str(BASE_DIR / "seller_copilot.db"))
DEFAULT_SELLER_EMAIL = "demo@seller-copilot.local"


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
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                full_name TEXT DEFAULT '',
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                auth_provider TEXT NOT NULL DEFAULT 'password',
                google_sub TEXT,
                google_sheet_url TEXT DEFAULT '',
                google_sheet_tab TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked_at TEXT
            );
            """
        )
        _ensure_user_schema(conn)
        _ensure_order_rows_schema(conn)
        _ensure_actions_schema(conn)
        _ensure_usage_logs_schema(conn)
        _ensure_inventory_schema(conn)
        _ensure_profit_settings_schema(conn)


def log_usage(event_type: str, detail: str = "", seller_email: str | None = None):
    seller_email = seller_email or DEFAULT_SELLER_EMAIL
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usage_logs (seller_email, event_type, detail) VALUES (?, ?, ?)",
            (seller_email, event_type, detail),
        )


def _ensure_user_schema(conn: sqlite3.Connection):
    if not _table_exists(conn, "users"):
        conn.execute(
            f"""
            CREATE TABLE users (
                email TEXT PRIMARY KEY,
                full_name TEXT DEFAULT '',
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                auth_provider TEXT NOT NULL DEFAULT 'password',
                google_sub TEXT,
                google_sheet_url TEXT DEFAULT '',
                google_sheet_tab TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    else:
        columns = _table_columns(conn, "users")
        if "auth_provider" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT NOT NULL DEFAULT 'password'")
        if "google_sub" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
        if "google_sheet_url" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN google_sheet_url TEXT DEFAULT ''")
        if "google_sheet_tab" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN google_sheet_tab TEXT DEFAULT ''")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL AND google_sub != ''")


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _ensure_order_rows_schema(conn: sqlite3.Connection):
    if not _table_exists(conn, "order_rows"):
        conn.execute(
            f"""
            CREATE TABLE order_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}',
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
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_order_rows_seller_email ON order_rows(seller_email)")
        return

    columns = _table_columns(conn, "order_rows")
    if "seller_email" not in columns:
        conn.execute(
            f"ALTER TABLE order_rows ADD COLUMN seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}'"
        )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_order_rows_seller_email ON order_rows(seller_email)")


def _ensure_actions_schema(conn: sqlite3.Connection):
    if not _table_exists(conn, "actions"):
        conn.execute(
            f"""
            CREATE TABLE actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}',
                text TEXT NOT NULL,
                category TEXT DEFAULT 'daily',
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                done_at TEXT
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_seller_email ON actions(seller_email)")
        return

    columns = _table_columns(conn, "actions")
    if "seller_email" not in columns:
        conn.execute(
            f"ALTER TABLE actions ADD COLUMN seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}'"
        )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_seller_email ON actions(seller_email)")


def _ensure_usage_logs_schema(conn: sqlite3.Connection):
    if not _table_exists(conn, "usage_logs"):
        conn.execute(
            f"""
            CREATE TABLE usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}',
                event_type TEXT NOT NULL,
                detail TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_seller_email ON usage_logs(seller_email)")
        return

    columns = _table_columns(conn, "usage_logs")
    if "seller_email" not in columns:
        conn.execute(
            f"ALTER TABLE usage_logs ADD COLUMN seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}'"
        )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_seller_email ON usage_logs(seller_email)")


def _ensure_inventory_schema(conn: sqlite3.Connection):
    if _table_exists(conn, "inventory") and "seller_email" not in _table_columns(conn, "inventory"):
        conn.execute("ALTER TABLE inventory RENAME TO inventory_legacy")

    if not _table_exists(conn, "inventory"):
        conn.execute(
            f"""
            CREATE TABLE inventory (
                seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}',
                sku TEXT NOT NULL,
                current_stock INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (seller_email, sku)
            );
            """
        )
        if _table_exists(conn, "inventory_legacy"):
            conn.execute(
                f"""
                INSERT INTO inventory (seller_email, sku, current_stock, updated_at)
                SELECT '{DEFAULT_SELLER_EMAIL}', sku, current_stock, updated_at
                FROM inventory_legacy
                """
            )
            conn.execute("DROP TABLE inventory_legacy")
        return

    conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_seller_email ON inventory(seller_email)")


def _ensure_profit_settings_schema(conn: sqlite3.Connection):
    if _table_exists(conn, "profit_settings") and "seller_email" not in _table_columns(conn, "profit_settings"):
        conn.execute("ALTER TABLE profit_settings RENAME TO profit_settings_legacy")

    if not _table_exists(conn, "profit_settings"):
        conn.execute(
            f"""
            CREATE TABLE profit_settings (
                seller_email TEXT NOT NULL DEFAULT '{DEFAULT_SELLER_EMAIL}',
                key TEXT NOT NULL,
                value REAL NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (seller_email, key)
            );
            """
        )
        rows = [
            (DEFAULT_SELLER_EMAIL, "product_cost_percent", 55),
            (DEFAULT_SELLER_EMAIL, "marketplace_fee_percent", 15),
            (DEFAULT_SELLER_EMAIL, "forward_shipping_per_order", 40),
            (DEFAULT_SELLER_EMAIL, "return_shipping_per_order", 200),
            (DEFAULT_SELLER_EMAIL, "ad_cost_percent", 8),
        ]
        conn.executemany(
            "INSERT INTO profit_settings (seller_email, key, value) VALUES (?, ?, ?)",
            rows,
        )
        if _table_exists(conn, "profit_settings_legacy"):
            old_rows = conn.execute("SELECT key, value, updated_at FROM profit_settings_legacy").fetchall()
            for row in old_rows:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO profit_settings (seller_email, key, value, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (DEFAULT_SELLER_EMAIL, row["key"], row["value"], row["updated_at"]),
                )
            conn.execute("DROP TABLE profit_settings_legacy")
        return

    conn.execute("CREATE INDEX IF NOT EXISTS idx_profit_settings_seller_email ON profit_settings(seller_email)")
