import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = os.environ.get("VAULTX_ADMIN_PASSWORD", "Admin@12345")


def hash_secret(secret: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, 310_000)
    return salt, digest


class Database:
    def __init__(self, path: str | Path = "data/vaultx.db"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    @contextmanager
    def transaction(self):
        with self._lock:
            try:
                self._connection.execute("BEGIN")
                yield self._connection
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def initialize(self) -> None:
        with self.transaction() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    address TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL UNIQUE REFERENCES customers(id),
                    account_number TEXT NOT NULL UNIQUE,
                    account_type TEXT NOT NULL CHECK(account_type IN ('Savings', 'Current')),
                    pin_salt BLOB NOT NULL,
                    pin_hash BLOB NOT NULL,
                    balance_cents INTEGER NOT NULL DEFAULT 0 CHECK(balance_cents >= 0),
                    status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open', 'Closed')),
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL REFERENCES accounts(id),
                    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Deposit', 'Withdrawal', 'Transfer In', 'Transfer Out')),
                    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                    balance_after_cents INTEGER NOT NULL CHECK(balance_after_cents >= 0),
                    related_account TEXT,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );
                CREATE INDEX IF NOT EXISTS idx_transactions_account_date
                    ON transactions(account_id, created_at DESC, id DESC);
                CREATE INDEX IF NOT EXISTS idx_accounts_number ON accounts(account_number);
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL
                );
                """
            )
            row = conn.execute(
                "SELECT id FROM admin WHERE username = ?", (DEFAULT_ADMIN_USERNAME,)
            ).fetchone()
            if row is None:
                salt, digest = hash_secret(DEFAULT_ADMIN_PASSWORD)
                conn.execute(
                    "INSERT INTO admin (username, password_salt, password_hash) VALUES (?, ?, ?)",
                    (DEFAULT_ADMIN_USERNAME, salt, digest),
                )

    def close(self) -> None:
        with self._lock:
            self._connection.close()
