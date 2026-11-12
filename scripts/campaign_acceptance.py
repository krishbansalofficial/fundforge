"""Campaign acceptance: two real headless Godot clients admit the prospect, then declare a winddown.

Room 1 (campaign-v1, pinned base variant): the API plays only the setup to stage ``eligible`` (as
frontend/e2e/admission.spec.ts does). The managing partner's client then presses "Propose admission" in
the investor lounge and the portfolio manager's client presses "Countersign" in the committee room. The
API readies past the day 20 dealing close; the server view must show stage ``admitted`` and the new series.

Room 2: the portfolio manager's client proposes a controlled winddown in the committee room and the
managing partner's client countersigns. The API then only liquidates and readies to the WINDDOWN ending.

This script never sends propose_admission, propose_winddown or the countersigning ``sign``: those reach
the server only through the clients' own buttons (--press, a dev flag in game/scripts/main.gd). Headless
button presses are programmatic client evidence, not a graphical human playtest.

Run from backend/ against an API with FUNDFORGE_CLOCK=0 FUNDFORGE_TEST_VARIANTS=1:
    uv run python ../scripts/campaign_acceptance.py --server http://127.0.0.1:8011 --godot /path/to/godot
Writes an evidence JSON (no seat tokens) and exits non-zero on any failed assertion.
"""

import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError

from coop_acceptance import GAME, call, stop_clients  # the shared two-client harness


class Room:
    def __init__(self, args, names):
        self.args = args
        room = call(args.server, "/api/rooms", body={"scenario": "campaign-v1", "variant": "base",
                                                     "pm_name": names[0], "mp_name": names[1]})
        self.id, self.tokens, self.prefix = room["room_id"], room["tokens"], "/api/rooms/" + room["room_id"]

    def view(self, role="mp"):
        return call(self.args.server, self.prefix + "/view", self.tokens[role])

    def command(self, role, body):
        """None when the server refuses (a stale ready is simply retried by the caller's loop)."""
        try:
            return call(self.args.server, self.prefix + "/commands", self.tokens[role], body, uuid.uuid4().hex)
        except HTTPError:
            return None

    def ready_both(self):
        v = self.view("pm")
        for role in ("pm", "mp"):
            if role not in v["ready"]:
                self.command(role, {"type": "ready", "version": v["version"]})

    def until(self, done, before=None):
        for _ in range(400):
            v = self.view()
            if done(v):
                return v
            assert not v["clock"]["finished"], "the run ended during setup"
            if before:
                before(self.view("pm"))
            self.ready_both()
        raise AssertionError("the room did not reach the expected state in 400 steps")

    def clients(self, press):
        """One Godot client per seat, each told which panel to open and which button to press."""
        base = [self.args.godot, "--headless", "--max-fps", "30"] + ([] if self.args.exported else ["--path", str(GAME)])
        return [subprocess.Popen(base + ["--", f"--server={self.args.server}", f"--join={self.id}:{self.tokens[r]}",
                                         f"--press={press[r]}"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True) for r in ("pm", "mp")]

    def package(self, kind, seconds=90):
        """Wait for the clients to propose and countersign a package of this kind; the script sends neither."""
        end = time.monotonic() + seconds
        seen = []
        while time.monotonic() < end:
            seen = [p for p in self.view()["packages"] if p["kind"] == kind]
            if seen and seen[0]["status"] != "PENDING_APPROVAL":
                return seen[0]
            time.sleep(0.3)
        raise AssertionError(f"clients did not propose and countersign a {kind} package in {seconds} s: {seen}")

    def verify(self):
        verified = call(self.args.server, self.prefix + "/verify", self.tokens["pm"])
        assert verified["ok"], verified
        return {k: verified[k] for k in ("ok", "version", "journal_digest", "chain_head")}


def at_exec(v):
    return bool(v["clock"]["next"] and v["clock"]["next"]["phase"].startswith("EXEC"))


def admission(args):
    room = Room(args, ("Adm PM", "Adm MP"))
    for assignment, day in (("prospect_qualification", 2), ("prospect_diligence", 3)):
        assert room.command("mp", {"type": "visit", "location": "lp", "assignment": assignment}), assignment
        room.until(lambda v, day=day: v["clock"]["day"] >= day)
    assert room.view()["prospect"]["stage"] == "diligence"
    eligible = room.until(lambda v: v["clock"]["day"] >= 19 and at_exec(v))
    assert eligible["prospect"]["stage"] == "eligible", eligible["prospect"]
    clients = room.clients({"mp": "lp:Propose admission", "pm": "committee:Countersign"})
    try:
        package = room.package("admission")
        assert package["proposer"] == "mp" and package["status"] == "ELECTED", package
        consented = room.view()
        assert consented["prospect"]["authorized"] == package["terms"]["amount"], consented["prospect"]
        assert "Anchor" not in [s["id"] for s in consented["series"]], "consent is not cash: no series before dealing"
        after = room.until(lambda v: v["clock"]["day"] >= 21)  # both clients stay joined and render every view
        assert after["prospect"]["stage"] == "admitted", after["prospect"]
        assert "Anchor" in [s["id"] for s in after["series"]], after["series"]
        time.sleep(2)  # let both clients poll and render the admitted view before they are stopped
    finally:
        errors = stop_clients(clients)
    assert not errors, errors
    return {"room": room.id, "consent_day": consented["clock"]["day"], "package": package,
            "stage": after["prospect"]["stage"], "series": [s["id"] for s in after["series"]], "verify": room.verify()}


def winddown(args):
    room = Room(args, ("Wind PM", "Wind MP"))
    declared = room.until(at_exec)["clock"]["day"]
    clients = room.clients({"pm": "committee:Propose a controlled winddown", "mp": "committee:Countersign"})

    def liquidate(v):  # joint packages at each execution barrier, as frontend/e2e/winddown.spec.ts
        if not at_exec(v):
            return
        for p in v["positions"]:
            if p["qty"] == 0 or any(o["sym"] == p["sym"] and o["status"] in ("QUEUED", "PARTIALLY_FILLED")
                                    for o in v["orders"]):
                continue
            pid = "liq-" + uuid.uuid4().hex[:8]
            d = room.command("pm", {"type": "propose", "package_id": pid, "orders": [
                {"order_id": pid, "sym": p["sym"], "side": "SELL" if p["qty"] > 0 else "COVER", "qty": abs(p["qty"])}]})
            if d:
                room.command("mp", {"type": "sign", "package_id": pid, "digest": d["digest"]})

    try:
        package = room.package("winddown")
        assert package["proposer"] == "pm" and package["status"] == "ELECTED", package
        assert room.view("pm")["winddown"] == room.view("mp")["winddown"] == declared == package["terms"]["day"]
        for _ in range(400):
            v = room.view("pm")
            if v["clock"]["finished"]:
                break
            liquidate(v)
            room.ready_both()
        end = room.view("pm")
        assert end["clock"]["finished"] and end["outcome"]["label"] == "WINDDOWN", end["outcome"]
        assert end["winddown"] == declared, end["winddown"]
        time.sleep(3)  # let both clients poll the ending and build the debrief before they are stopped
    finally:
        errors = stop_clients(clients)
    assert not errors, errors
    return {"room": room.id, "declared_day": declared, "package": package, "outcome": end["outcome"]["label"],
            "verify": room.verify()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--server", default="http://127.0.0.1:8011")
    p.add_argument("--godot", required=True)
    p.add_argument("--exported", action="store_true", help="--godot is an exported FundForge.x86_64")
    p.add_argument("--output", default="campaign-acceptance.json")
    a = p.parse_args()
    a.server = a.server.rstrip("/")
    try:
        evidence = {"kind": "HTTP setup and headless programmatic button presses", "graphical_human_playtest": False,
                    "admission": admission(a), "winddown": winddown(a)}
    except AssertionError as e:
        print(f"campaign acceptance FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    Path(a.output).write_text(json.dumps(evidence, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: {f: v[f] for f in v if f != "package"} for k, v in evidence.items() if isinstance(v, dict)}, indent=1))
    print(f"campaign acceptance passed; evidence in {a.output}")
