# VaultX – Smart Banking Management System

VaultX is a desktop banking simulation built with Python, Tkinter/ttk and SQLite. It is intended for learning and demonstration; it is not connected to a bank and must not be used to store real financial information.

## Features

- Customer registration with a unique account number and PBKDF2-hashed PIN.
- Customer sign-in, profile updates, PIN changes and account closure.
- Persistent deposits, withdrawals and account-to-account transfers.
- Transfer records and both account balances are written in one SQLite transaction.
- Dashboard with balance, deposit/withdrawal totals and recent activity.
- Currency displayed in Indian rupees (INR) with Indian digit grouping.
- Transaction history and CSV account statement export.
- Simple-interest and loan-EMI calculators.
- Separate administrator sign-in, customer/account search, transaction search and banking statistics.
- Input validation for contact details, dates, PINs, account numbers and transaction amounts.

## Requirements

- Python 3.10 or later
- Tkinter (usually included with the standard Python distribution)

The application uses Python's standard library only; `requirements.txt` intentionally has no third-party packages.

## Setup and execution

1. Open a terminal in the project folder.
2. Run:

   ```text
   python main.py
   ```

The SQLite database is created at `data/vaultx.db` the first time the application runs. Customer accounts and transactions persist between launches.

The first run creates the administrator account `admin` with the initial password `Admin@12345`. For a fresh installation, set the `VAULTX_ADMIN_PASSWORD` environment variable before the first launch to choose a different initial password. The initial password is hashed before it is stored. Once the administrator row exists, changing the environment variable does not change that account's password.

## Tests

Run the standard-library unit tests from the project folder:

```text
python -m unittest discover -v
```

The tests use a temporary in-memory SQLite database and cover registration, PIN hashing, deposits, withdrawals, insufficient funds, transfers and transfer failure behavior.

## Disclaimer

VaultX is an educational project, not production banking software. It does not implement regulatory controls, identity verification, encryption at rest, multi-factor authentication, external payment rails or production-grade operational security. Do not use it for real money, real customer data or sensitive credentials.
