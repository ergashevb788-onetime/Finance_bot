"""Parser utility for amount strings and money lent entries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedAmount:
    """Result of parsing an amount string."""

    amount: float
    currency: str
    note: Optional[str] = None


@dataclass
class ParsedLentEntry:
    """Result of parsing a money lent entry."""

    person_name: str
    amount: float
    currency: str
    note: Optional[str] = None


# Currency symbol/code mapping
_CURRENCY_MAP: dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "₽": "RUB",
    "¥": "JPY",
    "usd": "USD",
    "eur": "EUR",
    "gbp": "GBP",
    "rub": "RUB",
    "uzs": "UZS",
    "sum": "UZS",
    "so'm": "UZS",
}

# Regex: optional currency prefix, number (with k/m suffix), optional currency suffix
_AMOUNT_RE = re.compile(
    r"^"
    r"(?P<pre_curr>[$€£₽¥])?"          # optional leading currency symbol
    r"\s*"
    r"(?P<num>[\d][0-9\s,\.]*)"         # number, may contain spaces/commas/dots
    r"(?P<suffix>[km])?"                # optional k/m suffix
    r"\s*"
    r"(?P<post_curr>[$€£₽¥]|USD|EUR|GBP|RUB|UZS|sum|so'm)?"  # optional trailing currency
    r"\s*"
    r"(?P<note>.+)?$",                  # optional note
    re.IGNORECASE,
)


def _parse_number(num_str: str, suffix: str) -> float:
    """Normalize a raw number string and apply k/m multiplier."""
    # Remove spaces and commas used as thousands separators
    cleaned = re.sub(r"[\s,]", "", num_str)
    value = float(cleaned)
    if suffix:
        s = suffix.lower()
        if s == "k":
            value *= 1_000
        elif s == "m":
            value *= 1_000_000
    return value


def _resolve_currency(pre: Optional[str], post: Optional[str], default: str = "UZS") -> str:
    token = (pre or post or "").strip().lower()
    return _CURRENCY_MAP.get(token, default)


def parse_amount(text: str, default_currency: str = "UZS") -> Optional[ParsedAmount]:
    """
    Parse an amount string like:
        29000
        29 000
        29,000
        29k
        1.5m
        100$
        100 USD
        29000 Osh

    Returns ParsedAmount or None if parsing fails.
    """
    text = text.strip()
    m = _AMOUNT_RE.match(text)
    if not m:
        return None

    num_str = m.group("num")
    suffix = m.group("suffix") or ""
    pre_curr = m.group("pre_curr")
    post_curr = m.group("post_curr")
    note_part = (m.group("note") or "").strip() or None

    try:
        amount = _parse_number(num_str, suffix)
    except (ValueError, AttributeError):
        return None

    if amount <= 0:
        return None

    currency = _resolve_currency(pre_curr, post_curr, default_currency)

    return ParsedAmount(amount=amount, currency=currency, note=note_part)


def parse_lent_entry(text: str, default_currency: str = "UZS") -> Optional[ParsedLentEntry]:
    """
    Parse a money lent entry like:
        Tohirmalik 29k Osh
        Aziz 100$ House
        Sardor 250000

    Format: <Name> <amount>[currency] [note]
    """
    text = text.strip()
    parts = text.split(None, 1)  # split on first whitespace only
    if len(parts) < 2:
        return None

    person_name = parts[0].strip()
    rest = parts[1].strip()

    parsed = parse_amount(rest, default_currency)
    if parsed is None:
        return None

    return ParsedLentEntry(
        person_name=person_name,
        amount=parsed.amount,
        currency=parsed.currency,
        note=parsed.note,
    )


def format_amount(amount: float, currency: str) -> str:
    """Format amount for display: 1500000 UZS → 1.5m, 29000 UZS → 29k."""
    if currency == "UZS":
        if amount >= 1_000_000:
            val = amount / 1_000_000
            formatted = f"{val:g}m"
        elif amount >= 1_000:
            val = amount / 1_000
            formatted = f"{val:g}k"
        else:
            formatted = f"{amount:g}"
        return formatted
    # Foreign currency: keep as is
    if amount == int(amount):
        return f"{int(amount)} {currency}"
    return f"{amount:.2f} {currency}"
