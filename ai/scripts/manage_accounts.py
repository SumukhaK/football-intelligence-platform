"""CLI: invite people, and ban or unban accounts (ADR 022).

Usage:
    uv run python -m scripts.manage_accounts invite --email sam@example.com
    uv run python -m scripts.manage_accounts ban --email sam@example.com
    uv run python -m scripts.manage_accounts unban --email sam@example.com

``invite`` prints a one-time code valid for 7 days; send it to the person
privately. They redeem it in the app with a password of their choosing.
Inviting an existing account again lets them reset their password. The
accounts file is ``ACCOUNTS_PATH`` (default ``accounts/accounts.json``).
"""

from __future__ import annotations

import argparse
import sys

from backend.app.config import get_settings
from backend.app.services.account_service import AccountService
from backend.app.services.account_store import JsonAccountStore


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manage_accounts")
    parser.add_argument("action", choices=["invite", "ban", "unban"])
    parser.add_argument("--email", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one account action; 1 if the account does not exist."""
    args = _build_arg_parser().parse_args(argv)
    accounts = AccountService(JsonAccountStore(get_settings().accounts_path))
    if args.action == "invite":
        code = accounts.create_invite(args.email)
        print(f"Invite code for {args.email} (valid 7 days): {code}")
        return 0
    try:
        user = accounts.set_banned(args.email, banned=args.action == "ban")
    except KeyError:
        print(f"No account for {args.email}.", file=sys.stderr)
        return 1
    print(f"{user.email} is now {user.status}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
