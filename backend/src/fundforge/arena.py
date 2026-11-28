"""Arena: accounts (email magic links), verified results, the leaderboard and the weekly digest.

Nothing here is game state and the engine never imports it. A result is written only after ``Store.verified``
replays the room from its tape and hash-chained command log and the room has finished: clients never send a
score, so a tampered or unfinished room cannot reach the leaderboard. Tokens (magic links, sessions) are stored
as SHA-256 hashes, like seat tokens.

Run the weekly digest with ``python -m fundforge.arena digest``; it sends at most once per ISO week.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
import secrets
import smtplib
import sys
from decimal import Decimal
from email.message import EmailMessage
from typing import Any
from urllib.parse import unquote, urlsplit

from .governance import CLOCK
from .store import Store, _h

log = logging.getLogger("fundforge.arena")

LOGIN_TTL_MINUTES = 15
SESSION_DAYS = 30
PUBLIC_URL = os.environ.get("FUNDFORGE_PUBLIC_URL", "http://localhost:3000").rstrip("/")
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
DISPLAY_NAME = re.compile(r"^[A-Za-z0-9 _-]{2,24}$")
HIDDEN_TYPES = frozenset({"say"})  # private between partners: never in a public replay


class AuthError(PermissionError):
    pass


# ---------- mail ----------
def send_mail(to: str, subject: str, body: str) -> None:
    """Console in development; SMTP when FUNDFORGE_SMTP_URL=smtp://user:pass@host:587 (STARTTLS) is set."""
    url = os.environ.get("FUNDFORGE_SMTP_URL")
    if not url:
        log.info("console mail to=%s subject=%s\n%s", to, subject, body)
        print(f"--- mail to {to}: {subject}\n{body}\n---", file=sys.stderr, flush=True)
        return
    u = urlsplit(url)
    msg = EmailMessage()
    msg["From"] = os.environ.get("FUNDFORGE_MAIL_FROM", "FundForge <noreply@localhost>")
    msg["To"], msg["Subject"] = to, subject
    msg.set_content(body)
    with smtplib.SMTP(u.hostname or "localhost", u.port or 587, timeout=15) as smtp:
        smtp.starttls()
        if u.username:
            smtp.login(unquote(u.username), unquote(u.password or ""))
        smtp.send_message(msg)


# ---------- accounts ----------
def request_login(store: Store, email: str) -> None:
    """Mail a single-use sign-in link. The caller answers the same way whether or not the address has an account."""
    email = email.strip().lower()
    if len(email) > 254 or not EMAIL.fullmatch(email):
        raise ValueError("enter a valid email address")
    token = secrets.token_urlsafe(32)
    with store.pool.connection() as c:
        c.execute("insert into login_tokens (token_hash, email) values (%s,%s)", (_h(token), email))
    send_mail(email, "Your FundForge sign-in link",
              f"Sign in to FundForge Arena:\n\n{PUBLIC_URL}/login#token={token}\n\n"
              f"The link works once, for {LOGIN_TTL_MINUTES} minutes. If you did not ask for it, ignore this email.")


def verify_login(store: Store, token: str) -> dict[str, str]:
    """Spend a magic link: create the account on first sign-in and return a session token."""
    session = secrets.token_urlsafe(32)
    with store.pool.connection() as c, c.transaction():
        row = c.execute("update login_tokens set used_at=now() where token_hash=%s and used_at is null"
                        " and created_at > now() - make_interval(mins => %s) returning email",
                        (_h(token), LOGIN_TTL_MINUTES)).fetchone()
        if not row:
            raise AuthError("this sign-in link is invalid, used or expired")
        email = row[0]
        c.execute("insert into users (id, email, display_name) values (%s,%s,%s) on conflict (email) do nothing",
                  (secrets.token_hex(8), email, f"Player-{secrets.token_hex(2).upper()}"))
        uid = c.execute("select id from users where email=%s", (email,)).fetchone()[0]  # type: ignore[index]
        c.execute("insert into account_sessions values (%s,%s, now() + make_interval(days => %s))",
                  (_h(session), uid, SESSION_DAYS))
    return {"session": session, "user_id": uid}


def account(store: Store, session: str) -> str | None:
    """The user id for a live session token, else None."""
    if not session:
        return None
    with store.pool.connection() as c:
        row = c.execute("select user_id from account_sessions where token_hash=%s and expires_at > now()",
                        (_h(session),)).fetchone()
    return str(row[0]) if row else None


def sign_out(store: Store, session: str) -> None:
    with store.pool.connection() as c:
        c.execute("delete from account_sessions where token_hash=%s", (_h(session),))


def link_seat(store: Store, room: str, role: str, user_id: str | None) -> None:
    """Record that an account sat in a room's seat (the first account to claim a seat keeps it)."""
    if user_id:
        with store.pool.connection() as c:
            c.execute("insert into room_players values (%s,%s,%s) on conflict do nothing", (room, role, user_id))


def rename(store: Store, user_id: str, name: str) -> None:
    name = name.strip()
    if not DISPLAY_NAME.fullmatch(name):
        raise ValueError("display names are 2-24 letters, digits, spaces, _ or -")
    with store.pool.connection() as c:
        c.execute("update users set display_name=%s where id=%s", (name, user_id))


def profile(store: Store, user_id: str) -> dict[str, Any]:
    with store.pool.connection() as c:
        name, email = c.execute("select display_name, email from users where id=%s", (user_id,)).fetchone()  # type: ignore[misc]
        games = c.execute(
            "select p.room_id, r.scenario, p.role, r.created_at, x.label, x.score from room_players p"
            " join rooms r on r.id=p.room_id left join results x on x.room_id=p.room_id"
            " where p.user_id=%s order by r.created_at desc limit 50", (user_id,)).fetchall()
    return {"user_id": user_id, "display_name": name, "email": email, "games": [
        {"room_id": g[0], "scenario": g[1], "role": g[2], "created_at": g[3].isoformat(), "label": g[4],
         "score": None if g[5] is None else str(g[5])} for g in games]}


# ---------- results and leaderboard ----------
def record_result(store: Store, room: str) -> dict[str, Any]:
    """Replay and verify a finished room, then store its outcome once. Raises ReplayDivergence on tampering."""
    with store.pool.connection() as c:
        row = c.execute("select 1 from results where room_id=%s", (room,)).fetchone()
    if row:
        return result(store, room)
    report, s = store.verified(room)
    if not s.e.finished():
        raise ValueError("the run has not finished; results are recorded at the end")
    o = s.e.outcome()
    with store.pool.connection() as c:
        # the room's own scenario key: overlays such as case1-controls share Case1's tape id but rank separately
        scenario, solo = c.execute("select scenario, bot_role is not null from rooms where id=%s",
                                   (room,)).fetchone()  # type: ignore[misc]
        c.execute("insert into results (room_id, scenario, label, score, excess_bps, nav, solo, journal_digest,"
                  " chain_head, rules_version) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict do nothing",
                  (room, scenario, o["label"], o["score"], o["excess_bps"], o["nav"], solo,
                   report["journal_digest"], report["chain_head"], report["rules_version"]))
    return result(store, room)


def _players(c: Any, rooms: list[str]) -> dict[str, dict[str, str]]:
    """Public names per room and seat: an account's display name, 'Guest', or the bot."""
    out: dict[str, dict[str, str]] = {r: {} for r in rooms}
    for rid, bot_role in c.execute("select id, bot_role from rooms where id = any(%s)", (rooms,)):
        out[rid] = {"pm": "Guest", "mp": "Guest", **({bot_role: "Bot"} if bot_role else {})}
    for rid, role, name in c.execute("select p.room_id, p.role, u.display_name from room_players p"
                                     " join users u on u.id=p.user_id where p.room_id = any(%s)", (rooms,)):
        out[rid][role] = name
    return out


def _row(r: tuple[Any, ...]) -> dict[str, Any]:
    keys = ("room_id", "scenario", "label", "score", "excess_bps", "nav", "solo", "journal_digest", "chain_head",
            "rules_version", "verified_at")
    d: dict[str, Any] = dict(zip(keys, r, strict=True))
    for k in ("score", "excess_bps", "nav"):
        d[k] = str(d[k])
    d["verified_at"] = d["verified_at"].isoformat()
    return d


COLUMNS = ("room_id, scenario, label, score, excess_bps, nav, solo, journal_digest, chain_head, rules_version,"
           " verified_at")


def leaderboard(store: Store, scenario: str, limit: int = 20) -> list[dict[str, Any]]:
    with store.pool.connection() as c:
        rows = [_row(r) for r in c.execute(f"select {COLUMNS} from results where scenario=%s"
                                           " order by score desc, verified_at limit %s", (scenario, limit))]
        names = _players(c, [r["room_id"] for r in rows])
    return [{**r, "rank": i + 1, "players": names[r["room_id"]]} for i, r in enumerate(rows)]


def result(store: Store, room: str) -> dict[str, Any]:
    """A recorded result with its public command timeline (chat excluded). KeyError if none is recorded."""
    with store.pool.connection() as c:
        row = c.execute(f"select {COLUMNS} from results where room_id=%s", (room,)).fetchone()
        if not row:
            raise KeyError(room)
        roles: dict[str, str] = dict(c.execute("select user_id, role from seats where room_id=%s", (room,)).fetchall())
        bot_role = c.execute("select bot_role from rooms where id=%s", (room,)).fetchone()[0]  # type: ignore[index]
        timeline = [{"seq": seq, "actor": "clock" if uid == CLOCK else roles.get(uid, bot_role or "?"),
                     "type": cmd.get("type"), "at": at.isoformat()}
                    for seq, uid, cmd, at in c.execute(
                        "select seq, user_id, command, created_at from commands where room_id=%s order by seq",
                        (room,)) if cmd.get("type") not in HIDDEN_TYPES]
        names = _players(c, [room])[room]
    return {**_row(row), "players": names, "timeline": timeline}


# ---------- weekly digest ----------
def iso_week(day: dt.date) -> str:
    y, w, _ = day.isocalendar()
    return f"{y}-W{w:02d}"


def digest(store: Store, today: dt.date | None = None) -> dict[str, Any]:
    """Email each account that played in the last 7 days its games, best score and the week's top scores.

    Idempotent per ISO week: a second run in the same week sends nothing.
    """
    today = today or dt.datetime.now(dt.UTC).date()
    week = iso_week(today)
    with store.pool.connection() as c, c.transaction():
        if not c.execute("insert into digest_runs (week, sent) values (%s, 0) on conflict do nothing",
                         (week,)).rowcount:
            return {"week": week, "sent": 0, "skipped": "already sent this week"}
        top = c.execute("select scenario, label, score from results where verified_at > now() - interval '7 days'"
                        " order by score desc limit 3").fetchall()
        players = c.execute(
            "select u.email, u.display_name, count(*), max(x.score) from room_players p join users u on u.id=p.user_id"
            " join rooms r on r.id=p.room_id left join results x on x.room_id=p.room_id"
            " where r.created_at > now() - interval '7 days' group by u.email, u.display_name").fetchall()
        lines = [f"  {i + 1}. {s} {label} score {Decimal(sc):.2f}" for i, (s, label, sc) in enumerate(top)]
        board = "\n".join(lines) or "  No verified results this week."
        for email, name, games, best in players:
            best_line = f"Your best verified score: {Decimal(best):.2f}." if best is not None else (
                "None of your runs finished this week.")
            send_mail(email, f"FundForge league digest {week}",
                      f"Hi {name},\n\nYou played {games} game(s) this week. {best_line}\n\n"
                      f"This week's top verified scores:\n{board}\n\nLeaderboard: {PUBLIC_URL}/leaderboard\n")
        c.execute("update digest_runs set sent=%s where week=%s", (len(players), week))
    return {"week": week, "sent": len(players)}


if __name__ == "__main__":  # python -m fundforge.arena digest
    if sys.argv[1:] != ["digest"]:
        sys.exit("usage: python -m fundforge.arena digest")
    logging.basicConfig(level=logging.INFO)
    st = Store(os.environ.get("DATABASE_URL", "postgresql://fundforge:fundforge@localhost:5432/fundforge"))
    try:
        st.init()
        print(digest(st))
    finally:
        st.close()
