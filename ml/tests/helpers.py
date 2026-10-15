"""Shared test helper: outbox rows of a full solo game, built exactly as Store builds them."""

import hashlib

from fundforge import bot, outbox
from fundforge.engine import Engine
from fundforge.governance import Session

from fundforge_ml import worlds


def game_rows(variant: str, room: str = "room-1") -> list[dict]:
    e = Engine(worlds.world(None, variant).tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "bot"}, bots=frozenset({"mp"}))
    rows, before, finished_before, k = [], outbox.counts(s), False, 0
    while not s.e.finished():
        k += 1
        start = s.version
        bot.act(s, "mp", "bot", f"b{k}")
        s.handle("ana", f"r{k}", {"type": "ready", "version": s.version})
        bot.act(s, "mp", "bot", f"c{k}")
        for seq in range(start + 1, s.version + 1):
            entry = s.log[seq - 1]
            head = hashlib.sha256(f"{seq}".encode()).hexdigest()
            rows += outbox.rows_for(room, "rules-x", s, seq, entry, before, head, finished_before,
                                    last=seq == s.version)
            before = entry["after"]
        finished_before = s.e.finished()
    return rows
