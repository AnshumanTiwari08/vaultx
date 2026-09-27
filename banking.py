import secrets
import sqlite3
import hmac
from decimal import Decimal, InvalidOperation

from database import Database, hash_secret
from validators import (
    required,
    validate_account_number,
    validate_account_type,
    validate_dob,
    validate_email,
    validate_phone,
    validate_pin,
)

MAX_CENTS = 9_223_372_036_854_775_807


def to_cents(amount: str | int | float | Decimal) -> int:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Enter a valid amount.") from error
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    if value.as_tuple().exponent < -2:
        raise ValueError("Amount may have no more than two decimal places.")
    cents = int(value * 100)
    if cents > MAX_CENTS:
        raise ValueError("Amount exceeds the supported transaction limit.")
    return cents


def money(cents: int) -> str:
    return format_rupees(Decimal(cents) / 100)


def format_rupees(amount: str | int | float | Decimal) -> str:
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    sign = "-" if value < 0 else ""
    whole, fraction = f"{abs(value):.2f}".split(".")
    if len(whole) > 3:
        prefix = whole[:-3]
        groups = []
        while prefix:
            groups.insert(0, prefix[-2:])
            prefix = prefix[:-2]
        whole = f"{','.join(groups)},{whole[-3:]}"
    return f"{sign}₹{whole}.{fraction}"


class BankingService:
    def __init__(self, database: Database):
        self.database = database

    def register_customer(
        self, name: str, dob: str, phone: str, email: str, address: str,
        account_type: str, pin: str,
    ) -> dict:
        name = required(name, "Name")
        dob = validate_dob(dob)
        phone = validate_phone(phone)
        email = validate_email(email)
        address = required(address, "Address")
        account_type = validate_account_type(account_type)
        pin = validate_pin(pin)
        salt, digest = hash_secret(pin)

        with self.database.transaction() as conn:
            if conn.execute(
                "SELECT 1 FROM customers WHERE email = ? COLLATE NOCASE", (email,)
            ).fetchone():
                raise ValueError("An account already exists for this email address.")
            customer = conn.execute(
                """
                INSERT INTO customers (name, dob, phone, email, address)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, dob, phone, email, address),
            )
            account_number = self._new_account_number(conn)
            account = conn.execute(
                """
                INSERT INTO accounts (customer_id, account_number, account_type, pin_salt, pin_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (customer.lastrowid, account_number, account_type, salt, digest),
            )
        return {
            "customer_id": customer.lastrowid,
            "account_id": account.lastrowid,
            "account_number": account_number,
            "account_type": account_type,
        }

    @staticmethod
    def _new_account_number(conn: sqlite3.Connection) -> str:
        for _ in range(10):
            number = f"VX{secrets.randbelow(10**10):010d}"
            if conn.execute(
                "SELECT 1 FROM accounts WHERE account_number = ?", (number,)
            ).fetchone() is None:
                return number
        raise RuntimeError("Could not generate a unique account number.")

    def get_account(self, account_id: int) -> dict:
        with self.database.transaction() as conn:
            row = conn.execute(
                """
                SELECT a.id AS account_id, a.account_number, a.account_type, a.balance_cents,
                       a.status, a.created_at AS account_created_at, c.id AS customer_id,
                       c.name, c.dob, c.phone, c.email, c.address, c.created_at AS customer_created_at
                FROM accounts a JOIN customers c ON c.id = a.customer_id
                WHERE a.id = ?
                """,
                (account_id,),
            ).fetchone()
        if row is None:
            raise ValueError("Account not found.")
        account = dict(row)
        account.update(self.get_summary(account_id))
        account["recent_transactions"] = self.get_transactions(account_id, limit=5)
        return account

    def get_account_by_number(self, account_number: str) -> dict:
        account_number = validate_account_number(account_number)
        with self.database.transaction() as conn:
            row = conn.execute(
                "SELECT id FROM accounts WHERE account_number = ?", (account_number,)
            ).fetchone()
        if row is None:
            raise ValueError("Account not found.")
        return self.get_account(row["id"])

    def get_summary(self, account_id: int) -> dict:
        with self.database.transaction() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN transaction_type = 'Deposit' THEN amount_cents END), 0)
                           AS total_deposits_cents,
                       COALESCE(SUM(CASE WHEN transaction_type = 'Withdrawal'
                                         THEN amount_cents END), 0) AS total_withdrawals_cents
                FROM transactions WHERE account_id = ?
                """,
                (account_id,),
            ).fetchone()
        return dict(row)

    def deposit(self, account_id: int, amount: str | int | float | Decimal) -> int:
        cents = to_cents(amount)
        with self.database.transaction() as conn:
            row = self._open_account(conn, account_id)
            if row["balance_cents"] > MAX_CENTS - cents:
                raise ValueError("Deposit exceeds the supported account balance limit.")
            balance = row["balance_cents"] + cents
            conn.execute("UPDATE accounts SET balance_cents = ? WHERE id = ?", (balance, account_id))
            conn.execute(
                """
                INSERT INTO transactions
                    (account_id, transaction_type, amount_cents, balance_after_cents, description)
                VALUES (?, 'Deposit', ?, ?, 'Cash deposit')
                """,
                (account_id, cents, balance),
            )
        return balance

    def withdraw(self, account_id: int, amount: str | int | float | Decimal) -> int:
        cents = to_cents(amount)
        with self.database.transaction() as conn:
            row = self._open_account(conn, account_id)
            if cents > row["balance_cents"]:
                raise ValueError("Insufficient balance.")
            balance = row["balance_cents"] - cents
            conn.execute("UPDATE accounts SET balance_cents = ? WHERE id = ?", (balance, account_id))
            conn.execute(
                """
                INSERT INTO transactions
                    (account_id, transaction_type, amount_cents, balance_after_cents, description)
                VALUES (?, 'Withdrawal', ?, ?, 'Cash withdrawal')
                """,
                (account_id, cents, balance),
            )
        return balance

    def transfer(
        self, source_account_id: int, destination_account_number: str,
        amount: str | int | float | Decimal,
    ) -> tuple[int, int]:
        cents = to_cents(amount)
        destination_account_number = validate_account_number(destination_account_number)
        with self.database.transaction() as conn:
            source = self._open_account(conn, source_account_id)
            destination = conn.execute(
                "SELECT id, account_number, balance_cents, status FROM accounts WHERE account_number = ?",
                (destination_account_number,),
            ).fetchone()
            if destination is None or destination["status"] != "Open":
                raise ValueError("Destination account was not found or is closed.")
            if destination["id"] == source_account_id:
                raise ValueError("You cannot transfer money to the same account.")
            if cents > source["balance_cents"]:
                raise ValueError("Insufficient balance.")
            if destination["balance_cents"] > MAX_CENTS - cents:
                raise ValueError("Transfer exceeds the destination account balance limit.")
            source_balance = source["balance_cents"] - cents
            destination_balance = destination["balance_cents"] + cents
            conn.execute("UPDATE accounts SET balance_cents = ? WHERE id = ?", (source_balance, source_account_id))
            conn.execute("UPDATE accounts SET balance_cents = ? WHERE id = ?", (destination_balance, destination["id"]))
            conn.execute(
                """
                INSERT INTO transactions
                    (account_id, transaction_type, amount_cents, balance_after_cents, related_account, description)
                VALUES (?, 'Transfer Out', ?, ?, ?, 'Account transfer')
                """,
                (source_account_id, cents, source_balance, destination_account_number),
            )
            conn.execute(
                """
                INSERT INTO transactions
                    (account_id, transaction_type, amount_cents, balance_after_cents, related_account, description)
                VALUES (?, 'Transfer In', ?, ?, ?, 'Account transfer')
                """,
                (destination["id"], cents, destination_balance, source["account_number"]),
            )
        return source_balance, destination_balance

    @staticmethod
    def _open_account(conn: sqlite3.Connection, account_id: int) -> sqlite3.Row:
        row = conn.execute(
            "SELECT id, account_number, balance_cents, status FROM accounts WHERE id = ?",
            (account_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Account not found.")
        if row["status"] != "Open":
            raise ValueError("This account is closed.")
        return row

    def get_transactions(self, account_id: int, limit: int | None = None) -> list[dict]:
        query = """
            SELECT transaction_type, amount_cents, balance_after_cents, related_account,
                   description, created_at
            FROM transactions WHERE account_id = ?
            ORDER BY created_at DESC, id DESC
        """
        parameters: tuple = (account_id,)
        if limit is not None:
            query += " LIMIT ?"
            parameters = (account_id, limit)
        with self.database.transaction() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def update_profile(self, customer_id: int, name: str, dob: str, phone: str, email: str, address: str) -> None:
        values = (
            required(name, "Name"), validate_dob(dob), validate_phone(phone),
            validate_email(email), required(address, "Address"),
        )
        with self.database.transaction() as conn:
            if conn.execute(
                "SELECT 1 FROM customers WHERE email = ? COLLATE NOCASE AND id != ?",
                (values[3], customer_id),
            ).fetchone():
                raise ValueError("That email address is already used by another customer.")
            cursor = conn.execute(
                "UPDATE customers SET name = ?, dob = ?, phone = ?, email = ?, address = ? WHERE id = ?",
                (*values, customer_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Customer not found.")

    def close_account(self, account_id: int, pin: str) -> None:
        pin = validate_pin(pin)
        with self.database.transaction() as conn:
            row = conn.execute(
                "SELECT pin_salt, pin_hash, balance_cents, status FROM accounts WHERE id = ?",
                (account_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Account not found.")
            if row["status"] != "Open":
                raise ValueError("This account is already closed.")
            _, candidate = hash_secret(pin, row["pin_salt"])
            if not hmac.compare_digest(candidate, row["pin_hash"]):
                raise ValueError("PIN is incorrect.")
            if row["balance_cents"] != 0:
                raise ValueError("Withdraw or transfer the remaining balance before closing your account.")
            conn.execute("UPDATE accounts SET status = 'Closed' WHERE id = ?", (account_id,))

    def search_customers(self, query: str = "") -> list[dict]:
        pattern = f"%{query.strip()}%"
        with self.database.transaction() as conn:
            rows = conn.execute(
                """
                SELECT c.id AS customer_id, c.name, c.email, c.phone, a.account_number,
                       a.account_type, a.balance_cents, a.status
                FROM customers c JOIN accounts a ON a.customer_id = c.id
                WHERE c.name LIKE ? OR c.email LIKE ? OR c.phone LIKE ? OR a.account_number LIKE ?
                ORDER BY c.name COLLATE NOCASE
                """,
                (pattern, pattern, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def admin_transactions(self, query: str = "") -> list[dict]:
        pattern = f"%{query.strip()}%"
        with self.database.transaction() as conn:
            rows = conn.execute(
                """
                SELECT t.transaction_type, t.amount_cents, t.balance_after_cents,
                       t.related_account, t.description, t.created_at,
                       a.account_number, c.name
                FROM transactions t JOIN accounts a ON a.id = t.account_id
                JOIN customers c ON c.id = a.customer_id
                WHERE a.account_number LIKE ? OR c.name LIKE ?
                ORDER BY t.created_at DESC, t.id DESC LIMIT 500
                """,
                (pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def admin_statistics(self) -> dict:
        with self.database.transaction() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total_customers,
                       SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_accounts,
                       SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) AS closed_accounts,
                       COALESCE(SUM(CASE WHEN status = 'Open' THEN balance_cents ELSE 0 END), 0)
                           AS total_balance_cents
                FROM accounts
                """
            ).fetchone()
            txn = conn.execute("SELECT COUNT(*) AS total_transactions FROM transactions").fetchone()
        result = dict(row)
        result["total_transactions"] = txn["total_transactions"]
        return result
