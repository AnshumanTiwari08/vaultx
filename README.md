# VaultX – Smart Banking Management System

VaultX is a desktop banking simulation which has been developed using Python, Tkinter/ttk and SQLite; it is designed for educational and demonstrative purposes and is not linked to a bank since it should not be used for storing any real financial information.

## Features

- The customer is registered using a unique account number and a PIN that is hashed with the PBKDF2 method.
- Signing in as a customer, updating your profile, changing your PIN, and closing your account.
- Ongoing deposits, withdrawals, and transfers between accounts.
The transfer records and both account balances are all entered as part of a single SQLite transaction.
- A dashboard displaying the balance, the total amount deposited and withdrawn, and recent activity.
- The currency is shown in Indian rupees (INR) using Indian digit grouping.
- The transaction history and export of the CSV account statement.
- Simple interest and loan EMI calculators.
— Separate out the administrator's sign-in, the customer/account search, the transaction search, and the banking statistics.
- Validate the input for contact details, dates, PINs, account numbers and transaction amounts.

## Requirements

- Python 3.10 or a later version
- Tkinter (usually included with the standard Python distribution)

The application makes use of nothing but Python's standard library, and the requirements.txt file deliberately does not include any third-party packages.

## Setup and execution

1. Open the terminal in the folder that contains the project.
2. Run:

   ```text
   python main.py
   ```

When the application is first run, the SQLite database is created at `data/vaultx.db` and customer accounts together with transactions are retained between launches.

The administrator account `admin` is created on the first run using the initial password `Admin@12345`. If you are carrying out a fresh installation, you should set the `VAULTX_ADMIN_PASSWORD` environment variable before the first launch in order to specify a different initial password. The initial password is hashed before it is stored, and once the administrator record has been created, altering the environment variable will not change the password for that account.

## Tests

Run the standard-library unit tests from the project folder:

```text
python -m unittest discover -v
```

The tests involve the use of a temporary SQLite database that is stored in memory and include all the aspects of registration, PIN hashing, deposits, withdrawals, cases of insufficient funds, and the way in which transfers fail.

## Disclaimer

VaultX is an educational college project, not genuine production banking software, and it does not include regulatory controls, identity verification, encryption when data is at rest, multi-factor authentication, access to external payment systems, or production-standard operational security. It should not be used with real money, real customer data or sensitive credentials.
