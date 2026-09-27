import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from authentication import AuthenticationService
from banking import BankingService, format_rupees, money
from calculators import loan_emi, simple_interest
from reports import statement_csv


NAVY = "#132238"
NAVY_LIGHT = "#1D3553"
TEAL = "#18A999"
TEAL_DARK = "#118477"
BG = "#F3F6FA"
WHITE = "#FFFFFF"
TEXT = "#1D2A3A"
MUTED = "#738197"
RED = "#B54747"


class VaultXApp:
    def __init__(self, root: tk.Tk, banking: BankingService, auth: AuthenticationService):
        self.root = root
        self.banking = banking
        self.auth = auth
        self.customer = None
        self.admin = None
        self._style()
        self.root.title("VaultX | Smart Banking Management System")
        self.root.geometry("1180x760")
        self.root.minsize(940, 640)
        self.root.configure(bg=BG)
        self.show_login()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), foreground=TEXT)
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=WHITE)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Card.TLabel", background=WHITE, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("CardMuted.TLabel", background=WHITE, foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 23), foreground=TEXT, background=BG)
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 15), foreground=TEXT, background=BG)
        style.configure("CardSection.TLabel", font=("Segoe UI Semibold", 15), foreground=TEXT, background=WHITE)
        style.configure("CardValue.TLabel", font=("Segoe UI Semibold", 22), foreground=NAVY, background=WHITE)
        style.configure("Brand.TLabel", font=("Segoe UI Semibold", 25), foreground=WHITE, background=NAVY)
        style.configure("BrandSub.TLabel", font=("Segoe UI", 11), foreground="#C1D2E5", background=NAVY)
        style.configure("TEntry", padding=9, fieldbackground=WHITE)
        style.configure("TCombobox", padding=8)
        style.configure("TButton", padding=(12, 9), font=("Segoe UI Semibold", 10))
        style.configure("Primary.TButton", background=TEAL, foreground=WHITE, borderwidth=0)
        style.map("Primary.TButton", background=[("active", TEAL_DARK), ("disabled", "#A8C8C2")])
        style.configure("Nav.TButton", background=NAVY, foreground="#D4DFEA", anchor="w", padding=(18, 12), borderwidth=0)
        style.map("Nav.TButton", background=[("active", NAVY_LIGHT)], foreground=[("active", WHITE)])
        style.configure("Treeview", rowheight=31, background=WHITE, fieldbackground=WHITE, borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#EAF0F6", foreground=NAVY, padding=8)

    def _clear(self):
        for child in self.root.winfo_children():
            child.destroy()

    def _entry(self, parent, label, variable=None, show=None, width=36):
        ttk.Label(parent, text=label, style="Card.TLabel").pack(anchor="w", pady=(10, 4))
        entry = ttk.Entry(parent, textvariable=variable, show=show, width=width)
        entry.pack(fill="x")
        return entry

    def show_login(self):
        self.customer = None
        self.admin = None
        self._clear()
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)
        brand = tk.Frame(shell, bg=NAVY, width=410)
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)
        tk.Label(brand, text="◈  VaultX", font=("Segoe UI Semibold", 26), fg=WHITE, bg=NAVY).pack(anchor="w", padx=46, pady=(82, 18))
        tk.Label(
            brand, text="Banking that puts\nyou in control.", font=("Segoe UI Semibold", 27),
            fg=WHITE, bg=NAVY, justify="left",
        ).pack(anchor="w", padx=46, pady=(34, 16))
        tk.Label(
            brand, text="A secure, simple place to manage your money.", font=("Segoe UI", 11),
            fg="#C1D2E5", bg=NAVY, wraplength=300, justify="left",
        ).pack(anchor="w", padx=46)
        panel = ttk.Frame(shell, padding=(70, 45))
        panel.pack(side="left", fill="both", expand=True)
        ttk.Label(panel, text="Welcome back", style="Title.TLabel").pack(anchor="w", pady=(36, 6))
        ttk.Label(panel, text="Sign in to continue to your account.", style="Muted.TLabel").pack(anchor="w", pady=(0, 24))
        card = ttk.Frame(panel, style="Card.TFrame", padding=28)
        card.pack(anchor="w", fill="x", expand=True)
        self.login_account = tk.StringVar()
        self.login_pin = tk.StringVar()
        self._entry(card, "Account number", self.login_account)
        self._entry(card, "Secure PIN", self.login_pin, show="●")
        ttk.Button(card, text="Sign in", style="Primary.TButton", command=self._login_customer).pack(fill="x", pady=(22, 8))
        actions = ttk.Frame(card, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Create an account", command=self.show_registration).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(actions, text="Admin sign in", command=self.show_admin_login).pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.login_pin_entry = None

    def _login_customer(self):
        try:
            self.customer = self.auth.authenticate_customer(self.login_account.get(), self.login_pin.get())
            self.show_customer_shell()
        except ValueError as error:
            messagebox.showerror("Sign in failed", str(error), parent=self.root)

    def show_registration(self):
        self._clear()
        outer = ttk.Frame(self.root, padding=32)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 16))
        ttk.Button(header, text="←  Back to sign in", command=self.show_login).pack(side="left")
        ttk.Label(header, text="Open your VaultX account", style="Title.TLabel").pack(side="left", padx=22)
        card = ttk.Frame(outer, style="Card.TFrame", padding=26)
        card.pack(fill="both", expand=True)
        self.reg_vars = {key: tk.StringVar() for key in ("name", "dob", "phone", "email", "address", "pin", "confirm_pin")}
        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(fill="both", expand=True)
        fields = [
            ("Full name", "name", None), ("Date of birth (YYYY-MM-DD)", "dob", None),
            ("Phone number", "phone", None), ("Email address", "email", None),
            ("Street address", "address", None), ("Create PIN (4–6 digits)", "pin", "●"),
            ("Confirm PIN", "confirm_pin", "●"),
        ]
        for index, (label, key, show) in enumerate(fields):
            column = index % 2
            row = index // 2
            cell = ttk.Frame(form, style="Card.TFrame")
            cell.grid(row=row, column=column, sticky="ew", padx=(0, 14) if column == 0 else (14, 0), pady=4)
            self._entry(cell, label, self.reg_vars[key], show=show)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        self.reg_type = tk.StringVar(value="Savings")
        cell = ttk.Frame(form, style="Card.TFrame")
        cell.grid(row=3, column=1, sticky="ew", padx=(14, 0), pady=4)
        ttk.Label(cell, text="Account type", style="Card.TLabel").pack(anchor="w", pady=(10, 4))
        ttk.Combobox(cell, textvariable=self.reg_type, values=("Savings", "Current"), state="readonly").pack(fill="x")
        ttk.Button(card, text="Create account", style="Primary.TButton", command=self._register).pack(anchor="e", pady=(22, 0))

    def _register(self):
        values = {key: variable.get() for key, variable in self.reg_vars.items()}
        if values["pin"] != values["confirm_pin"]:
            messagebox.showerror("Registration failed", "PIN entries do not match.", parent=self.root)
            return
        try:
            account = self.banking.register_customer(
                values["name"], values["dob"], values["phone"], values["email"],
                values["address"], self.reg_type.get(), values["pin"],
            )
        except ValueError as error:
            messagebox.showerror("Registration failed", str(error), parent=self.root)
            return
        messagebox.showinfo(
            "Account created",
            f"Your account is ready.\n\nAccount number: {account['account_number']}\nAccount type: {account['account_type']}\n\nKeep your account number safe.",
            parent=self.root,
        )
        self.show_login()

    def show_admin_login(self):
        self._clear()
        frame = ttk.Frame(self.root, padding=60)
        frame.pack(fill="both", expand=True)
        ttk.Button(frame, text="←  Back to customer sign in", command=self.show_login).pack(anchor="w")
        ttk.Label(frame, text="Administrator sign in", style="Title.TLabel").pack(anchor="w", pady=(45, 6))
        ttk.Label(frame, text="Access customer, account and transaction records.", style="Muted.TLabel").pack(anchor="w", pady=(0, 20))
        card = ttk.Frame(frame, style="Card.TFrame", padding=28)
        card.pack(anchor="w", fill="x", padx=(0, 330))
        self.admin_username = tk.StringVar()
        self.admin_password = tk.StringVar()
        self._entry(card, "Username", self.admin_username)
        self._entry(card, "Password", self.admin_password, show="●")
        ttk.Button(card, text="Admin sign in", style="Primary.TButton", command=self._login_admin).pack(fill="x", pady=(22, 0))

    def _login_admin(self):
        try:
            self.admin = self.auth.authenticate_admin(self.admin_username.get(), self.admin_password.get())
            self.show_admin_shell()
        except ValueError as error:
            messagebox.showerror("Sign in failed", str(error), parent=self.root)

    def _base_shell(self, title, subtitle, nav_items, on_select, name):
        self._clear()
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(shell, bg=NAVY, width=224)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="◈  VaultX", font=("Segoe UI Semibold", 20), fg=WHITE, bg=NAVY).pack(anchor="w", padx=22, pady=(25, 32))
        tk.Label(sidebar, text=name, font=("Segoe UI Semibold", 11), fg=WHITE, bg=NAVY, anchor="w").pack(fill="x", padx=22)
        tk.Label(sidebar, text="SECURE BANKING", font=("Segoe UI", 8), fg="#95A9C0", bg=NAVY, anchor="w").pack(fill="x", padx=22, pady=(3, 20))
        for item in nav_items:
            ttk.Button(sidebar, text=item, style="Nav.TButton", command=lambda selected=item: on_select(selected)).pack(fill="x", padx=8, pady=2)
        self.main_area = ttk.Frame(shell, padding=(30, 24))
        self.main_area.pack(side="left", fill="both", expand=True)
        heading = ttk.Frame(self.main_area)
        heading.pack(fill="x", pady=(0, 24))
        ttk.Label(heading, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(5, 0))
        self.content = ttk.Frame(self.main_area)
        self.content.pack(fill="both", expand=True)
        return self.content

    def show_customer_shell(self):
        account = self.banking.get_account(self.customer["id"])
        content = self._base_shell(
            f"Hello, {account['name'].split()[0]}",
            "Your account overview at a glance.",
            ["Dashboard", "Deposit", "Withdraw", "Transfer", "Transactions", "Profile", "Change PIN", "Calculators", "Account statement", "Close account", "Log out"],
            self._customer_nav,
            account["name"],
        )
        self._customer_dashboard(content, account)

    def _customer_nav(self, selected):
        methods = {
            "Dashboard": self.show_customer_shell,
            "Deposit": lambda: self._operation_page("Deposit"),
            "Withdraw": lambda: self._operation_page("Withdraw"),
            "Transfer": lambda: self._operation_page("Transfer"),
            "Transactions": self._show_transactions,
            "Profile": self._show_profile,
            "Change PIN": self._show_change_pin,
            "Calculators": self._show_calculators,
            "Account statement": self._show_statement,
            "Close account": self._show_close_account,
            "Log out": self.show_login,
        }
        methods[selected]()

    def _page(self, title, subtitle):
        for child in self.main_area.winfo_children():
            child.destroy()
        heading = ttk.Frame(self.main_area)
        heading.pack(fill="x", pady=(0, 24))
        ttk.Label(heading, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(5, 0))
        self.content = ttk.Frame(self.main_area)
        self.content.pack(fill="both", expand=True)
        return self.content

    def _customer_dashboard(self, parent, account):
        cards = ttk.Frame(parent)
        cards.pack(fill="x", pady=(0, 22))
        self._stat_card(cards, "Available balance", money(account["balance_cents"]), 0)
        self._stat_card(cards, "Total deposits", money(account["total_deposits_cents"]), 1)
        self._stat_card(cards, "Total withdrawals", money(account["total_withdrawals_cents"]), 2)
        for column in range(3):
            cards.columnconfigure(column, weight=1, uniform="stat")
        info = ttk.Frame(parent, style="Card.TFrame", padding=20)
        info.pack(fill="x", pady=(0, 18))
        ttk.Label(info, text=f"{account['account_type']} account", style="Card.TLabel", font=("Segoe UI Semibold", 12)).pack(anchor="w")
        ttk.Label(info, text=f"Account  {account['account_number']}    •    Status  {account['status']}", style="CardMuted.TLabel").pack(anchor="w", pady=(5, 0))
        quick = ttk.Frame(parent)
        quick.pack(fill="x", pady=(0, 18))
        for label in ("Deposit", "Withdraw", "Transfer"):
            ttk.Button(quick, text=f"+  {label}", style="Primary.TButton", command=lambda action=label: self._operation_page(action)).pack(side="left", padx=(0, 10))
        ttk.Label(parent, text="Recent activity", style="Section.TLabel").pack(anchor="w", pady=(4, 10))
        self._transaction_table(parent, account["recent_transactions"], height=6)

    def _stat_card(self, parent, label, value, column):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 16))
        card.grid(row=0, column=column, sticky="ew", padx=(0, 10) if column < 2 else (0, 0))
        ttk.Label(card, text=label, style="CardMuted.TLabel").pack(anchor="w")
        ttk.Label(card, text=value, style="CardValue.TLabel").pack(anchor="w", pady=(10, 0))

    def _operation_page(self, operation):
        parent = self._page(operation, {
            "Deposit": "Add funds to your VaultX account.",
            "Withdraw": "Withdraw funds from your available balance.",
            "Transfer": "Send funds securely to another open VaultX account.",
        }[operation])
        card = ttk.Frame(parent, style="Card.TFrame", padding=25)
        card.pack(anchor="nw", fill="x", padx=(0, 170))
        if operation == "Transfer":
            self.transfer_destination = tk.StringVar()
            self._entry(card, "Destination account number", self.transfer_destination)
        self.operation_amount = tk.StringVar()
        self._entry(card, "Amount (₹)", self.operation_amount)
        ttk.Button(card, text=f"Confirm {operation.lower()}", style="Primary.TButton", command=lambda: self._execute_operation(operation)).pack(anchor="e", pady=(22, 0))

    def _execute_operation(self, operation):
        try:
            if operation == "Deposit":
                balance = self.banking.deposit(self.customer["id"], self.operation_amount.get())
                detail = f"New balance: {money(balance)}"
            elif operation == "Withdraw":
                balance = self.banking.withdraw(self.customer["id"], self.operation_amount.get())
                detail = f"New balance: {money(balance)}"
            else:
                balances = self.banking.transfer(
                    self.customer["id"], self.transfer_destination.get(), self.operation_amount.get()
                )
                detail = f"Transfer complete. New balance: {money(balances[0])}"
        except ValueError as error:
            messagebox.showerror(f"{operation} failed", str(error), parent=self.root)
            return
        messagebox.showinfo(f"{operation} successful", detail, parent=self.root)
        self.show_customer_shell()

    def _transaction_table(self, parent, rows, height=12):
        columns = ("created_at", "transaction_type", "amount", "balance", "related")
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        table = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        headings = (("created_at", "Date"), ("transaction_type", "Transaction"), ("amount", "Amount"), ("balance", "Balance after"), ("related", "Other account"))
        for key, label in headings:
            table.heading(key, text=label)
        table.column("created_at", width=155, anchor="w")
        table.column("transaction_type", width=135, anchor="w")
        table.column("amount", width=110, anchor="e")
        table.column("balance", width=135, anchor="e")
        table.column("related", width=150, anchor="w")
        for row in rows:
            table.insert("", "end", values=(
                row["created_at"], row["transaction_type"],
                money(row["amount_cents"]), money(row["balance_after_cents"]),
                row["related_account"] or "—",
            ))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return table

    def _show_transactions(self):
        parent = self._page("Transactions", "A complete record of activity on your account.")
        self._transaction_table(parent, self.banking.get_transactions(self.customer["id"]))

    def _show_profile(self):
        account = self.banking.get_account(self.customer["id"])
        parent = self._page("Profile", "View and update your personal details.")
        card = ttk.Frame(parent, style="Card.TFrame", padding=24)
        card.pack(anchor="nw", fill="x", padx=(0, 130))
        self.profile_vars = {key: tk.StringVar(value=account[key]) for key in ("name", "dob", "phone", "email", "address")}
        fields = [("Full name", "name"), ("Date of birth (YYYY-MM-DD)", "dob"), ("Phone", "phone"), ("Email", "email"), ("Address", "address")]
        for label, key in fields:
            self._entry(card, label, self.profile_vars[key])
        ttk.Label(card, text=f"Account number: {account['account_number']}  ·  {account['account_type']}", style="CardMuted.TLabel").pack(anchor="w", pady=(14, 0))
        ttk.Button(card, text="Save profile", style="Primary.TButton", command=self._save_profile).pack(anchor="e", pady=(20, 0))

    def _save_profile(self):
        values = {key: variable.get() for key, variable in self.profile_vars.items()}
        try:
            self.banking.update_profile(
                self.customer["customer_id"], values["name"], values["dob"],
                values["phone"], values["email"], values["address"],
            )
        except ValueError as error:
            messagebox.showerror("Profile update failed", str(error), parent=self.root)
            return
        messagebox.showinfo("Profile updated", "Your profile has been saved.", parent=self.root)
        self.show_customer_shell()

    def _show_change_pin(self):
        parent = self._page("Change PIN", "Choose a new private PIN for your account.")
        card = ttk.Frame(parent, style="Card.TFrame", padding=25)
        card.pack(anchor="nw", fill="x", padx=(0, 170))
        self.pin_vars = [tk.StringVar() for _ in range(3)]
        for label, variable in zip(("Current PIN", "New PIN", "Confirm new PIN"), self.pin_vars):
            self._entry(card, label, variable, show="●")
        ttk.Button(card, text="Update PIN", style="Primary.TButton", command=self._change_pin).pack(anchor="e", pady=(20, 0))

    def _change_pin(self):
        old_pin, new_pin, confirm = (variable.get() for variable in self.pin_vars)
        if new_pin != confirm:
            messagebox.showerror("PIN update failed", "New PIN entries do not match.", parent=self.root)
            return
        try:
            self.auth.change_pin(self.customer["id"], old_pin, new_pin)
        except ValueError as error:
            messagebox.showerror("PIN update failed", str(error), parent=self.root)
            return
        messagebox.showinfo("PIN updated", "Your PIN has been changed.", parent=self.root)
        self.show_customer_shell()

    def _show_statement(self):
        parent = self._page("Account statement", "Review your statement or save a CSV copy.")
        ttk.Button(parent, text="Export statement as CSV", style="Primary.TButton", command=self._export_statement).pack(anchor="e", pady=(0, 12))
        self._transaction_table(parent, self.banking.get_transactions(self.customer["id"]))

    def _export_statement(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Save account statement", defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"),),
        )
        if not path:
            return
        content = statement_csv(self.banking, self.customer["id"])
        with open(path, "w", newline="", encoding="utf-8") as file:
            file.write(content)
        messagebox.showinfo("Statement exported", "Your statement was saved.", parent=self.root)

    def _show_close_account(self):
        parent = self._page("Close account", "Closing an account is permanent and requires a zero balance.")
        card = ttk.Frame(parent, style="Card.TFrame", padding=25)
        card.pack(anchor="nw", fill="x", padx=(0, 170))
        ttk.Label(card, text="You must transfer or withdraw all funds before closing.", style="Card.TLabel").pack(anchor="w")
        self.close_pin = tk.StringVar()
        self._entry(card, "Confirm with your PIN", self.close_pin, show="●")
        ttk.Button(card, text="Close my account", command=self._close_account).pack(anchor="e", pady=(18, 0))

    def _close_account(self):
        if not messagebox.askyesno("Close account", "Are you sure you want to permanently close this account?", parent=self.root):
            return
        try:
            self.banking.close_account(self.customer["id"], self.close_pin.get())
        except ValueError as error:
            messagebox.showerror("Could not close account", str(error), parent=self.root)
            return
        messagebox.showinfo("Account closed", "Your account has been closed.", parent=self.root)
        self.show_login()

    def _show_calculators(self):
        parent = self._page("Calculators", "Estimate simple interest and monthly loan repayments.")
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        interest = ttk.Frame(parent, style="Card.TFrame", padding=22)
        interest.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        loan = ttk.Frame(parent, style="Card.TFrame", padding=22)
        loan.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(interest, text="Simple interest", style="CardSection.TLabel").pack(anchor="w")
        ttk.Label(interest, text="Estimate earnings on a principal amount.", style="CardMuted.TLabel").pack(anchor="w", pady=(4, 8))
        self.si_vars = [tk.StringVar() for _ in range(3)]
        for label, variable in zip(("Principal (₹)", "Annual rate (%)", "Time (years)"), self.si_vars):
            self._entry(interest, label, variable)
        ttk.Button(interest, text="Calculate interest", style="Primary.TButton", command=self._calculate_interest).pack(anchor="w", pady=(17, 0))
        self.si_result = ttk.Label(interest, text="", style="Card.TLabel")
        self.si_result.pack(anchor="w", pady=(12, 0))
        ttk.Label(loan, text="Loan EMI", style="CardSection.TLabel").pack(anchor="w")
        ttk.Label(loan, text="Estimate your fixed monthly payment.", style="CardMuted.TLabel").pack(anchor="w", pady=(4, 8))
        self.emi_vars = [tk.StringVar() for _ in range(3)]
        for label, variable in zip(("Loan amount (₹)", "Annual rate (%)", "Term (months)"), self.emi_vars):
            self._entry(loan, label, variable)
        ttk.Button(loan, text="Calculate EMI", style="Primary.TButton", command=self._calculate_emi).pack(anchor="w", pady=(17, 0))
        self.emi_result = ttk.Label(loan, text="", style="Card.TLabel")
        self.emi_result.pack(anchor="w", pady=(12, 0))

    def _calculate_interest(self):
        try:
            interest, total = simple_interest(*(variable.get() for variable in self.si_vars))
        except (ValueError, TypeError) as error:
            messagebox.showerror("Calculator", str(error), parent=self.root)
            return
        self.si_result.configure(text=f"Interest: {format_rupees(interest)}   ·   Total: {format_rupees(total)}")

    def _calculate_emi(self):
        try:
            emi = loan_emi(*(variable.get() for variable in self.emi_vars))
        except (ValueError, TypeError) as error:
            messagebox.showerror("Calculator", str(error), parent=self.root)
            return
        self.emi_result.configure(text=f"Estimated monthly payment: {format_rupees(emi)}")

    def show_admin_shell(self):
        stats = self.banking.admin_statistics()
        content = self._base_shell(
            "Admin overview", "VaultX operations and account insights.",
            ["Overview", "Customers & accounts", "Transactions", "Log out"],
            self._admin_nav, self.admin["username"],
        )
        cards = ttk.Frame(content)
        cards.pack(fill="x")
        stats_data = [
            ("Customers", str(stats["total_customers"] or 0)),
            ("Open accounts", str(stats["open_accounts"] or 0)),
            ("Closed accounts", str(stats["closed_accounts"] or 0)),
            ("Total balances", money(stats["total_balance_cents"])),
            ("Transactions", str(stats["total_transactions"])),
        ]
        for index, (label, value) in enumerate(stats_data):
            self._stat_card(cards, label, value, index)
            cards.columnconfigure(index, weight=1, uniform="admin-stat")
        ttk.Label(content, text="Use the navigation to search customer records or review transactions.", style="Muted.TLabel").pack(anchor="w", pady=(25, 0))

    def _admin_nav(self, selected):
        if selected == "Overview":
            self.show_admin_shell()
        elif selected == "Customers & accounts":
            self._admin_customers()
        elif selected == "Transactions":
            self._admin_transactions()
        else:
            self.show_login()

    def _admin_customers(self):
        parent = self._page("Customers & accounts", "Search account number, customer name, email or phone.")
        search = ttk.Frame(parent)
        search.pack(fill="x", pady=(0, 14))
        self.admin_search = tk.StringVar()
        entry = ttk.Entry(search, textvariable=self.admin_search)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry.bind("<Return>", lambda _event: self._refresh_admin_customers())
        ttk.Button(search, text="Search", style="Primary.TButton", command=self._refresh_admin_customers).pack(side="left")
        columns = ("name", "account", "type", "balance", "status", "email", "phone")
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)
        self.admin_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        for key, heading in zip(columns, ("Customer", "Account number", "Type", "Balance", "Status", "Email", "Phone")):
            self.admin_table.heading(key, text=heading)
            self.admin_table.column(key, width=115, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.admin_table.yview)
        self.admin_table.configure(yscrollcommand=scrollbar.set)
        self.admin_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._refresh_admin_customers()

    def _refresh_admin_customers(self):
        rows = self.banking.search_customers(self.admin_search.get())
        self.admin_table.delete(*self.admin_table.get_children())
        for row in rows:
            self.admin_table.insert("", "end", values=(
                row["name"], row["account_number"], row["account_type"],
                money(row["balance_cents"]), row["status"], row["email"], row["phone"],
            ))

    def _admin_transactions(self):
        parent = self._page("Transaction records", "Search by customer name or account number; up to 500 latest records.")
        search = ttk.Frame(parent)
        search.pack(fill="x", pady=(0, 14))
        self.admin_txn_search = tk.StringVar()
        entry = ttk.Entry(search, textvariable=self.admin_txn_search)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry.bind("<Return>", lambda _event: self._refresh_admin_transactions())
        ttk.Button(search, text="Search", style="Primary.TButton", command=self._refresh_admin_transactions).pack(side="left")
        columns = ("date", "customer", "account", "type", "amount", "related")
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)
        self.admin_txn_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        for key, heading in zip(columns, ("Date", "Customer", "Account", "Transaction", "Amount", "Other account")):
            self.admin_txn_table.heading(key, text=heading)
            self.admin_txn_table.column(key, width=130, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.admin_txn_table.yview)
        self.admin_txn_table.configure(yscrollcommand=scrollbar.set)
        self.admin_txn_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._refresh_admin_transactions()

    def _refresh_admin_transactions(self):
        rows = self.banking.admin_transactions(self.admin_txn_search.get())
        self.admin_txn_table.delete(*self.admin_txn_table.get_children())
        for row in rows:
            self.admin_txn_table.insert("", "end", values=(
                row["created_at"], row["name"], row["account_number"],
                row["transaction_type"], money(row["amount_cents"]),
                row["related_account"] or "—",
            ))
