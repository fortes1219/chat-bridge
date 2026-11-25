"""The strategy tests answer questions through the chat service, so they start no program and read
no database for the split, the date the data reaches or the market sections, as the chat tests do.
"""

from tests.chat.conftest import codex_not_installed, no_split_and_a_fixed_date

__all__ = ["codex_not_installed", "no_split_and_a_fixed_date"]
