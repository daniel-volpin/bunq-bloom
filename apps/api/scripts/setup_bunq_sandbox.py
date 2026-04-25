#!/usr/bin/env python3
"""
Prepare bunq sandbox accounts for bunq Bloom.

This script intentionally does not create or print API keys. Set BUNQ_API_KEY in
your local .env first, then use this helper to list/create sandbox accounts,
request test funds, and produce non-secret account-id env lines.

Usage:
  cd apps/api
  python scripts/setup_bunq_sandbox.py
  python scripts/setup_bunq_sandbox.py --create-missing-accounts --fund-parent 500.00
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from requests import RequestException


DEFAULT_TOOLKIT_PATH = Path("../../hackathon_toolkit-main")
SUGAR_DADDY_EMAIL = "sugardaddy@bunq.com"


@dataclass(frozen=True)
class AccountSummary:
    id: str
    description: str
    status: str
    balance_amount: str
    balance_currency: str
    iban: str | None

    @property
    def is_active_eur(self) -> bool:
        return self.status == "ACTIVE" and self.balance_currency == "EUR"


def resolve_toolkit_path(raw_path: str | Path, *, cwd: Path | None = None) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()

    cwd = cwd or Path.cwd()
    cwd_candidate = (cwd / path).resolve()
    if (cwd_candidate / "bunq_client.py").exists():
        return cwd_candidate

    api_root_candidate = (Path(__file__).resolve().parents[1] / path).resolve()
    return api_root_candidate


def load_bunq_client(toolkit_path: Path):
    if not (toolkit_path / "bunq_client.py").exists():
        raise RuntimeError(f"Toolkit path does not contain bunq_client.py: {toolkit_path}")
    if str(toolkit_path) not in sys.path:
        sys.path.insert(0, str(toolkit_path))
    from bunq_client import BunqClient

    return BunqClient


def summarize_account(item: dict[str, Any]) -> AccountSummary:
    account = item.get("MonetaryAccountBank", {})
    balance = account.get("balance", {})
    aliases = account.get("alias", [])
    iban = next((alias.get("value") for alias in aliases if alias.get("type") == "IBAN" and alias.get("value")), None)
    return AccountSummary(
        id=str(account.get("id", "")),
        description=str(account.get("description") or ""),
        status=str(account.get("status") or ""),
        balance_amount=str(balance.get("value", "0.00")),
        balance_currency=str(balance.get("currency", "EUR")),
        iban=iban,
    )


def choose_accounts(
    accounts: list[AccountSummary],
    *,
    parent_account_id: str | None = None,
    kid_account_id: str | None = None,
) -> tuple[AccountSummary, AccountSummary]:
    active_accounts = [account for account in accounts if account.is_active_eur]
    if parent_account_id or kid_account_id:
        parent = _find_account(active_accounts, parent_account_id, "parent") if parent_account_id else None
        kid = _find_account(active_accounts, kid_account_id, "kid") if kid_account_id else None
        if parent and kid:
            if parent.id == kid.id:
                raise RuntimeError("Parent and kid account IDs must be different.")
            return parent, kid

    parent = _find_by_description(active_accounts, "parent") or (active_accounts[0] if active_accounts else None)
    kid = _find_by_description(active_accounts, "kid")
    if kid is None:
        kid = next((account for account in active_accounts if parent and account.id != parent.id), None)

    if not parent or not kid:
        raise RuntimeError("Need at least two active EUR monetary accounts. Re-run with --create-missing-accounts.")
    if parent.id == kid.id:
        raise RuntimeError("Parent and kid account selection resolved to the same account.")
    return parent, kid


def create_account(client: Any, description: str) -> str:
    response = client.post(
        f"user/{client.user_id}/monetary-account-bank",
        {
            "currency": "EUR",
            "description": description,
        },
    )
    return str(response[0]["Id"]["id"])


def request_test_funds(client: Any, *, account_id: str, amount: str) -> None:
    client.post(
        f"user/{client.user_id}/monetary-account/{account_id}/request-inquiry",
        {
            "amount_inquired": {"value": amount, "currency": "EUR"},
            "counterparty_alias": {
                "type": "EMAIL",
                "value": SUGAR_DADDY_EMAIL,
                "name": "Sugar Daddy",
            },
            "description": "bunq Bloom sandbox funds",
            "allow_bunqme": False,
        },
    )


def print_accounts(accounts: list[AccountSummary]) -> None:
    print("\nMonetary accounts")
    print("-" * 80)
    for account in accounts:
        iban_status = "yes" if account.iban else "no"
        print(
            f"id={account.id} status={account.status} "
            f"balance={account.balance_amount} {account.balance_currency} "
            f"iban={iban_status} description={account.description!r}"
        )


def print_env_lines(parent: AccountSummary, kid: AccountSummary) -> None:
    print("\nAdd/update these non-secret values in apps/api/.env:")
    print("BLOOM_USE_FAKE_BUNQ=false")
    print(f"BUNQ_PARENT_ACCOUNT_ID={parent.id}")
    print(f"BUNQ_KID_ACCOUNT_ID={kid.id}")
    print(f"BUNQ_KID_ACCOUNT_IBAN={kid.iban}")


def print_bunq_error(exc: Exception) -> None:
    print("\nbunq sandbox request failed.", file=sys.stderr)
    if isinstance(exc, RequestException):
        print("Reason: network/API request error while contacting public-api.sandbox.bunq.com.", file=sys.stderr)
    else:
        print(f"Reason: {exc}", file=sys.stderr)
    print("Check network/DNS, wait a few seconds for bunq rate limits, then rerun the command.", file=sys.stderr)


def _find_account(accounts: list[AccountSummary], account_id: str | None, label: str) -> AccountSummary:
    for account in accounts:
        if account.id == str(account_id):
            return account
    raise RuntimeError(f"Configured {label} account id was not found or is not an active EUR account: {account_id}")


def _find_by_description(accounts: list[AccountSummary], needle: str) -> AccountSummary | None:
    return next((account for account in accounts if needle in account.description.lower()), None)


def _amount(value: str) -> str:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("Amount must be a decimal string, e.g. 500.00") from exc
    if amount <= Decimal("0") or amount > Decimal("500.00"):
        raise argparse.ArgumentTypeError("Amount must be greater than 0 and no more than 500.00")
    return f"{amount:.2f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare bunq sandbox accounts for bunq Bloom.")
    parser.add_argument(
        "--toolkit-path",
        default=os.getenv("BLOOM_BUNQ_TOOLKIT_PATH", str(DEFAULT_TOOLKIT_PATH)),
        help="Path to hackathon_toolkit-main. Defaults to BLOOM_BUNQ_TOOLKIT_PATH or ../../hackathon_toolkit-main.",
    )
    parser.add_argument("--parent-account-id", default=os.getenv("BUNQ_PARENT_ACCOUNT_ID"))
    parser.add_argument("--kid-account-id", default=os.getenv("BUNQ_KID_ACCOUNT_ID"))
    parser.add_argument(
        "--create-missing-accounts",
        action="store_true",
        help="Create Bloom Parent and Bloom Kid EUR accounts if fewer than two active EUR accounts exist.",
    )
    parser.add_argument(
        "--fund-parent",
        type=_amount,
        default=None,
        metavar="AMOUNT",
        help="Request sandbox funds from sugardaddy@bunq.com for the selected parent account.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = parse_args()
    api_key = os.getenv("BUNQ_API_KEY", "").strip()
    if not api_key:
        print("BUNQ_API_KEY is required in local env. This script will not create or print API keys.", file=sys.stderr)
        return 2

    toolkit_path = resolve_toolkit_path(args.toolkit_path)
    BunqClient = load_bunq_client(toolkit_path)
    client = BunqClient(api_key=api_key, sandbox=True)

    try:
        print("Authenticating with bunq sandbox...", flush=True)
        client.authenticate()
        print(f"Authenticated sandbox user id: {client.user_id}")

        accounts = [summarize_account(item) for item in client.get(f"user/{client.user_id}/monetary-account-bank")]
        if args.create_missing_accounts and len([account for account in accounts if account.is_active_eur]) < 2:
            print("\nCreating missing Bloom sandbox accounts...")
            descriptions = {account.description for account in accounts}
            if "Bloom Parent Account" not in descriptions:
                print(f"created parent account id={create_account(client, 'Bloom Parent Account')}")
            if "Bloom Kid Account" not in descriptions:
                print(f"created kid account id={create_account(client, 'Bloom Kid Account')}")
            accounts = [summarize_account(item) for item in client.get(f"user/{client.user_id}/monetary-account-bank")]

        print_accounts(accounts)
        parent, kid = choose_accounts(
            accounts,
            parent_account_id=args.parent_account_id,
            kid_account_id=args.kid_account_id,
        )

        if not kid.iban:
            raise RuntimeError("Selected kid account has no IBAN alias; payment adapter cannot target it yet.")

        print("\nSelected Bloom accounts")
        print("-" * 80)
        print(f"parent id={parent.id} balance={parent.balance_amount} {parent.balance_currency} description={parent.description!r}")
        print(f"kid id={kid.id} balance={kid.balance_amount} {kid.balance_currency} description={kid.description!r}")

        if args.fund_parent:
            print(f"\nRequesting EUR {args.fund_parent} sandbox funds for parent account...")
            request_test_funds(client, account_id=parent.id, amount=args.fund_parent)
            print("Funding request sent. Waiting briefly before refreshing account balances...")
            time.sleep(2)
            accounts = [summarize_account(item) for item in client.get(f"user/{client.user_id}/monetary-account-bank")]
            parent, kid = choose_accounts(accounts, parent_account_id=parent.id, kid_account_id=kid.id)
            print(f"parent refreshed balance={parent.balance_amount} {parent.balance_currency}")
    except (RequestException, RuntimeError) as exc:
        print_bunq_error(exc)
        return 1

    print_env_lines(parent, kid)
    print("\nNext smoke test:")
    print("BLOOM_RUN_SMOKE_TESTS=true pytest tests/test_integration_smoke.py::test_bunq_balance_smoke -q")
    print("BLOOM_RUN_SMOKE_TESTS=true BLOOM_RUN_BUNQ_PAYMENT_SMOKE=true pytest tests/test_integration_smoke.py::test_bunq_tiny_payment_smoke -q")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
