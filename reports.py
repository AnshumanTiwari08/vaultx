import csv
import io

from banking import BankingService


def account_statement(service: BankingService, account_id: int) -> list[dict]:
    return service.get_transactions(account_id)


def statement_csv(service: BankingService, account_id: int) -> str:
    output = io.StringIO()
    fields = [
        "created_at", "transaction_type", "amount_cents", "balance_after_cents",
        "related_account", "description",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(account_statement(service, account_id))
    return output.getvalue()
