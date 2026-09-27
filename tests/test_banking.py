import unittest

from authentication import AuthenticationService
from banking import BankingService, format_rupees, money
from database import Database


class BankingServiceTests(unittest.TestCase):
    def setUp(self):
        self.database = Database(":memory:")
        self.banking = BankingService(self.database)
        self.auth = AuthenticationService(self.database)
        self.first = self.register("alice@example.com")
        self.second = self.register("bob@example.com")

    def tearDown(self):
        self.database.close()

    def register(self, email):
        return self.banking.register_customer(
            "Test Customer", "1995-06-15", "+1 202 555 0100", email,
            "1 Test Street", "Savings", "1234",
        )

    def test_registration_hashes_pin_and_login_succeeds(self):
        account = self.auth.authenticate_customer(self.first["account_number"], "1234")
        self.assertEqual(account["id"], self.first["account_id"])
        with self.database.transaction() as conn:
            stored = conn.execute(
                "SELECT pin_hash FROM accounts WHERE id = ?", (self.first["account_id"],)
            ).fetchone()["pin_hash"]
        self.assertNotEqual(stored, b"1234")

    def test_deposit_withdraw_and_insufficient_funds(self):
        self.assertEqual(self.banking.deposit(self.first["account_id"], "100.25"), 10025)
        self.assertEqual(self.banking.withdraw(self.first["account_id"], "40"), 6025)
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            self.banking.withdraw(self.first["account_id"], 70)
        self.assertEqual(self.banking.get_account(self.first["account_id"])["balance_cents"], 6025)

    def test_transfer_updates_both_accounts_and_records_entries(self):
        self.banking.deposit(self.first["account_id"], 250)
        balances = self.banking.transfer(
            self.first["account_id"], self.second["account_number"], "75.50"
        )
        self.assertEqual(balances, (17450, 7550))
        self.assertEqual(len(self.banking.get_transactions(self.first["account_id"])), 2)
        self.assertEqual(self.banking.get_account(self.second["account_id"])["balance_cents"], 7550)
        self.assertEqual(
            self.banking.get_summary(self.first["account_id"])["total_withdrawals_cents"],
            0,
        )

    def test_failed_transfer_leaves_both_accounts_unchanged(self):
        self.banking.deposit(self.first["account_id"], 30)
        before_source = self.banking.get_account(self.first["account_id"])["balance_cents"]
        before_dest = self.banking.get_account(self.second["account_id"])["balance_cents"]
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            self.banking.transfer(
                self.first["account_id"], self.second["account_number"], 50
            )
        self.assertEqual(self.banking.get_account(self.first["account_id"])["balance_cents"], before_source)
        self.assertEqual(self.banking.get_account(self.second["account_id"])["balance_cents"], before_dest)

    def test_invalid_login_and_closed_account(self):
        with self.assertRaisesRegex(ValueError, "incorrect"):
            self.auth.authenticate_customer(self.first["account_number"], "9999")
        self.banking.close_account(self.first["account_id"], "1234")
        with self.assertRaisesRegex(ValueError, "closed"):
            self.auth.authenticate_customer(self.first["account_number"], "1234")

    def test_duplicate_email_and_invalid_amount(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.register("alice@example.com")
        for amount in (0, -1, "not money", "1.001"):
            with self.assertRaises(ValueError):
                self.banking.deposit(self.first["account_id"], amount)

    def test_pin_change_and_account_close_require_valid_state(self):
        self.auth.change_pin(self.first["account_id"], "1234", "5678")
        self.auth.authenticate_customer(self.first["account_number"], "5678")
        self.banking.deposit(self.first["account_id"], 15)
        with self.assertRaisesRegex(ValueError, "remaining balance"):
            self.banking.close_account(self.first["account_id"], "5678")
        self.banking.withdraw(self.first["account_id"], 15)
        self.banking.close_account(self.first["account_id"], "5678")
        with self.assertRaisesRegex(ValueError, "closed"):
            self.banking.deposit(self.first["account_id"], 1)

    def test_admin_login_and_search(self):
        self.assertEqual(self.auth.authenticate_admin("admin", "Admin@12345")["username"], "admin")
        self.assertEqual(len(self.banking.search_customers("alice@example.com")), 1)
        self.assertEqual(self.banking.admin_statistics()["total_customers"], 2)

    def test_amounts_format_as_indian_rupees(self):
        self.assertEqual(money(123456789), "₹12,34,567.89")
        self.assertEqual(format_rupees(12500), "₹12,500.00")


if __name__ == "__main__":
    unittest.main()
