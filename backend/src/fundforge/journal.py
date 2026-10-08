"""Immutable, balanced, per-entity double-entry journal.

Amounts are signed: debit > 0, credit < 0. Every entry balances within its own
entity (fund or firm); a cross-entity fee payment is two entries posted
atomically via ``post_many``. Entry IDs are economic identities: re-posting the
same content is a no-op, re-using an ID with different content is an error.
"""

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from .money import CENT

ENTITIES = frozenset({"fund", "firm"})


class JournalError(ValueError):
    pass


@dataclass(frozen=True)
class Posting:
    account: str
    amount: Decimal


@dataclass(frozen=True)
class Entry:
    entry_id: str
    entity: str
    date: str  # ISO calendar date the economics belong to
    memo: str
    postings: tuple[Posting, ...]

    def __post_init__(self):
        if self.entity not in ENTITIES:
            raise JournalError(f"unknown entity {self.entity!r}")
        if len(self.postings) < 2:
            raise JournalError(f"{self.entry_id}: needs at least two postings")
        for p in self.postings:
            if not isinstance(p.amount, Decimal) or not p.amount.is_finite():
                raise JournalError(f"{self.entry_id}: non-decimal amount {p.amount!r}")
            if p.amount == 0 or p.amount != p.amount.quantize(CENT):
                raise JournalError(f"{self.entry_id}: amount must be non-zero whole cents: {p.amount}")
        if sum(p.amount for p in self.postings) != 0:
            raise JournalError(f"{self.entry_id}: unbalanced entry")

    def canonical(self) -> dict:
        return {
            "id": self.entry_id,
            "entity": self.entity,
            "date": self.date,
            "memo": self.memo,
            "postings": [[p.account, str(p.amount)] for p in self.postings],
        }


def entry(entry_id: str, entity: str, date: str, memo: str, *legs: tuple[str, Decimal]) -> Entry:
    return Entry(entry_id, entity, date, memo, tuple(Posting(a, x) for a, x in legs if x != 0))


class Journal:
    def __init__(self):
        self._entries: list[Entry] = []
        self._by_id: dict[str, Entry] = {}
        self._balances: dict[tuple[str, str], Decimal] = defaultdict(Decimal)

    def post_many(self, entries: list[Entry]) -> bool:
        """Atomically post entries; returns False if all were already posted."""
        fresh = []
        for e in entries:
            prior = self._by_id.get(e.entry_id) or next((f for f in fresh if f.entry_id == e.entry_id), None)
            if prior is None:
                fresh.append(e)
            elif prior != e:
                raise JournalError(f"{e.entry_id}: identity reused with different content")
        for e in fresh:
            self._entries.append(e)
            self._by_id[e.entry_id] = e
            for p in e.postings:
                self._balances[(e.entity, p.account)] += p.amount
        return bool(fresh)

    def post(self, e: Entry) -> bool:
        return self.post_many([e])

    def balance(self, entity: str, account: str) -> Decimal:
        return self._balances.get((entity, account), Decimal(0))

    def balances(self, entity: str) -> dict[str, Decimal]:
        return {a: v for (ent, a), v in sorted(self._balances.items()) if ent == entity and v != 0}

    @property
    def entries(self) -> tuple[Entry, ...]:
        return tuple(self._entries)

    def digest(self) -> str:
        blob = json.dumps([e.canonical() for e in self._entries], separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()
