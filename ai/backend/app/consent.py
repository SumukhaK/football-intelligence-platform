"""The notice users accept before using the app (ADR 022).

Changing the text means raising ``CONSENT_VERSION``: everyone is asked again.
"""

from __future__ import annotations

CONSENT_VERSION = 1
CONSENT_TEXT = """\
Football Intelligence is a private project shared with family and friends.

While you use it, the server records your email, when you sign in, how many \
questions you ask the assistant, how long answers take, how many tokens they \
use, and whether a question was refused. This is used to set fair usage \
limits and to improve the app. It is not shared with anyone.

The text of your questions is stored only if you allow it below.

Questions that are abusive or harmful count as strikes. After three strikes \
the account is blocked.

You can ask the owner to delete your account and its data at any time.\
"""
