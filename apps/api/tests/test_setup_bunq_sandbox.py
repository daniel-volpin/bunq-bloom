import argparse
from pathlib import Path

import pytest

from scripts.setup_bunq_sandbox import AccountSummary, _amount, choose_accounts, resolve_toolkit_path, summarize_account


def account(account_id: str, description: str, *, status: str = "ACTIVE", currency: str = "EUR") -> AccountSummary:
    return AccountSummary(
        id=account_id,
        description=description,
        status=status,
        balance_amount="10.00",
        balance_currency=currency,
        iban=f"NL00BUNQ{account_id:0>10}",
    )


def test_resolve_toolkit_path_prefers_current_working_directory(tmp_path):
    toolkit = tmp_path / "hackathon_toolkit-main"
    toolkit.mkdir()
    (toolkit / "bunq_client.py").write_text("# fake toolkit\n", encoding="utf-8")

    assert resolve_toolkit_path("hackathon_toolkit-main", cwd=tmp_path) == toolkit.resolve()


def test_summarize_account_extracts_iban_and_balance():
    summary = summarize_account(
        {
            "MonetaryAccountBank": {
                "id": 123,
                "description": "Bloom Kid Account",
                "status": "ACTIVE",
                "balance": {"value": "27.50", "currency": "EUR"},
                "alias": [
                    {"type": "EMAIL", "value": "kid@example.test"},
                    {"type": "IBAN", "value": "NL00BUNQ0123456789"},
                ],
            }
        }
    )

    assert summary.id == "123"
    assert summary.description == "Bloom Kid Account"
    assert summary.balance_amount == "27.50"
    assert summary.iban == "NL00BUNQ0123456789"


def test_choose_accounts_uses_parent_and_kid_descriptions():
    parent, kid = choose_accounts(
        [
            account("1", "Bloom Kid Account"),
            account("2", "Bloom Parent Account"),
        ]
    )

    assert parent.id == "2"
    assert kid.id == "1"


def test_choose_accounts_validates_explicit_ids():
    parent, kid = choose_accounts(
        [
            account("100", "Main Account"),
            account("200", "Second Account"),
        ],
        parent_account_id="100",
        kid_account_id="200",
    )

    assert parent.id == "100"
    assert kid.id == "200"


def test_choose_accounts_requires_two_active_eur_accounts():
    with pytest.raises(RuntimeError, match="Need at least two active EUR"):
        choose_accounts(
            [
                account("100", "Only Account"),
                account("200", "Inactive Account", status="CANCELLED"),
                account("300", "USD Account", currency="USD"),
            ]
        )


def test_amount_accepts_sandbox_limit():
    assert _amount("500") == "500.00"
    assert _amount("0.01") == "0.01"


def test_amount_rejects_invalid_values():
    with pytest.raises(argparse.ArgumentTypeError):
        _amount("500.01")
    with pytest.raises(argparse.ArgumentTypeError):
        _amount("0")
    with pytest.raises(argparse.ArgumentTypeError):
        _amount("not-money")
