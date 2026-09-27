import tkinter as tk

from authentication import AuthenticationService
from banking import BankingService
from database import Database
from gui.app import VaultXApp


def main():
    database = Database()
    root = tk.Tk()
    root.report_callback_exception = _report_callback_exception
    VaultXApp(root, BankingService(database), AuthenticationService(database))
    root.mainloop()
    database.close()


def _report_callback_exception(exception, value, traceback):
    import traceback as traceback_module
    from tkinter import messagebox

    traceback_module.print_exception(exception, value, traceback)
    messagebox.showerror("Unexpected error", str(value))


if __name__ == "__main__":
    main()
