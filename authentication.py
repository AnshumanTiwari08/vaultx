import hmac
from database import Database, hash_secret
from validators import validate_account_number, validate_pin, required


class AuthenticationService:
    def __init__(self, database: Database):
        self.database = database

    def authenticate_customer(self, account_number: str, pin: str) -> dict:
        account_number = validate_account_number(account_number)
        pin = validate_pin(pin)
        with self.database.transaction() as conn:
            row = conn.execute(
                """
                SELECT a.id, a.account_number, a.account_type, a.pin_salt, a.pin_hash,
                       a.status, c.id AS customer_id, c.name
                FROM accounts a JOIN customers c ON c.id = a.customer_id
                WHERE a.account_number = ?
                """,
                (account_number,),
            ).fetchone()
        if row is None or row["status"] != "Open":
            raise ValueError("Account number or PIN is incorrect, or the account is closed.")
        _, candidate = hash_secret(pin, row["pin_salt"])
        if not hmac.compare_digest(candidate, row["pin_hash"]):
            raise ValueError("Account number or PIN is incorrect, or the account is closed.")
        return dict(row)

    def authenticate_admin(self, username: str, password: str) -> dict:
        username = required(username, "Username")
        if not password:
            raise ValueError("Password is required.")
        with self.database.transaction() as conn:
            row = conn.execute(
                "SELECT id, username, password_salt, password_hash FROM admin WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            raise ValueError("Invalid admin username or password.")
        _, candidate = hash_secret(password, row["password_salt"])
        if not hmac.compare_digest(candidate, row["password_hash"]):
            raise ValueError("Invalid admin username or password.")
        return {"id": row["id"], "username": row["username"]}

    def change_pin(self, account_id: int, old_pin: str, new_pin: str) -> None:
        old_pin = validate_pin(old_pin)
        new_pin = validate_pin(new_pin)
        with self.database.transaction() as conn:
            row = conn.execute(
                "SELECT pin_salt, pin_hash, status FROM accounts WHERE id = ?",
                (account_id,),
            ).fetchone()
            if row is None or row["status"] != "Open":
                raise ValueError("Open account not found.")
            _, candidate = hash_secret(old_pin, row["pin_salt"])
            if not hmac.compare_digest(candidate, row["pin_hash"]):
                raise ValueError("Current PIN is incorrect.")
            salt, digest = hash_secret(new_pin)
            conn.execute(
                "UPDATE accounts SET pin_salt = ?, pin_hash = ? WHERE id = ?",
                (salt, digest, account_id),
            )

    def reset_pin(self, account_number: str, new_pin: str) -> None:
        account_number = validate_account_number(account_number)
        new_pin = validate_pin(new_pin)
        salt, digest = hash_secret(new_pin)
        with self.database.transaction() as conn:
            cursor = conn.execute(
                "UPDATE accounts SET pin_salt = ?, pin_hash = ? WHERE account_number = ? AND status = 'Open'",
                (salt, digest, account_number),
            )
            if cursor.rowcount != 1:
                raise ValueError("Open account not found.")
