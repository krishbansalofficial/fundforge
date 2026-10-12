"""P3 acceptance: two partners split across two crises, then meet to present a package.

Two real headless Godot clients join one room and walk scripted routes. The portfolio manager goes to
the research library (the BRIN demand survey) and the managing partner crosses to the prime broker
(the borrow recall); then both walk to the committee room. Presence observers (an extra socket per seat)
record where each avatar actually is. The run asserts:

1. both partners stand in different crisis locations at the same moment;
2. each takes that location's assignment in the same decision window (engine-checked ``visit`` commands);
3. both reach the committee room, where one proposes a package and the other countersigns it;
4. the room still verifies (presence traffic never touched the books).

Run from backend/ against a running API (FUNDFORGE_CLOCK=0 keeps time still):
    uv run python ../scripts/coop_acceptance.py --server http://127.0.0.1:8011 --godot /path/to/godot
    (--exported to run an exported FundForge.x86_64 instead of the editor binary)
Writes an evidence JSON (no seat tokens) and exits non-zero on any failed assertion.
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

import websockets

GAME = Path(__file__).resolve().parents[1] / "game"
HTTP = build_opener(ProxyHandler({}))


def call(server, path, token=None, body=None, key=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    data = json.dumps(body).encode() if body is not None else None
    with HTTP.open(Request(server + path, headers=headers, data=data), timeout=15) as r:
        return json.load(r)


class Observer:
    """A second socket for one seat; it sees the *other* seat's avatar."""

    def __init__(self, url, token):
        self.url, self.token = url, token
        self.where: dict[str, str] = {}
        self.timeline: list[tuple[float, str, str, float, float]] = []

    async def run(self, t0, stop):
        async with websockets.connect(self.url, proxy=None) as ws:
            await ws.send(json.dumps({"type": "hello", "token": self.token}))
            while not stop.is_set():
                try:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), 0.5))
                except TimeoutError:
                    continue
                moves = {r: p for r, p in msg["partners"].items()} if msg["type"] == "welcome" else (
                    {msg["role"]: msg} if msg["type"] == "presence" else {})
                for role, pos in moves.items():  # the welcome carries positions sent before this socket joined
                    if self.where.get(role) != pos["location"]:
                        self.timeline.append((round(time.monotonic() - t0, 2), role, pos["location"], pos["x"], pos["z"]))
                    self.where[role] = pos["location"]


def stop_clients(clients):
    """Terminate the Godot clients and return any script or engine errors they printed."""
    errors = []
    for c in clients:
        if c.poll() is None:
            c.terminate()
    for c in clients:
        try:
            _, err = c.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            c.kill()
            _, err = c.communicate()
        except ValueError:  # already collected
            continue
        errors += [line for line in (err or "").splitlines() if "SCRIPT ERROR" in line or line.startswith("ERROR")]
    return errors


async def wait_for(cond, seconds, what):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if cond():
            return
        await asyncio.sleep(0.1)
    raise AssertionError(f"timed out after {seconds} s waiting for {what}")


ROUTES = {"pm": "research@1,committee@14", "mp": "broker@1,committee@14"}


def start(args):
    """Create the room and launch both Godot clients (blocking work, done before the event loop starts)."""
    server = args.server.rstrip("/")
    room = call(server, "/api/rooms", body={"pm_name": "Ana", "mp_name": "Ben"})
    base = [args.godot, "--headless", "--max-fps", "30"] + ([] if args.exported else ["--path", str(GAME)])
    clients = [subprocess.Popen(base + ["--", f"--server={server}", f"--join={room['room_id']}:{room['tokens'][r]}",
                                        f"--goto={ROUTES[r]}"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True) for r in ("pm", "mp")]
    return server, room, clients, time.monotonic()


async def main(args, server, room, clients, t0):
    rid, pm, mp = room["room_id"], room["tokens"]["pm"], room["tokens"]["mp"]
    prefix = f"/api/rooms/{rid}"

    async def api(*a):  # HTTP off the event loop, so the observers' sockets keep being serviced
        return await asyncio.to_thread(call, server, *a)

    ws_url = server.replace("http", "ws", 1) + prefix + "/presence"
    sees_mp, sees_pm = Observer(ws_url, pm), Observer(ws_url, mp)

    def where(role):
        return (sees_pm if role == "pm" else sees_mp).where.get(role, "")

    stop = asyncio.Event()
    tasks = [asyncio.create_task(o.run(t0, stop)) for o in (sees_mp, sees_pm)]
    evidence = {"room": rid, "routes": ROUTES}
    try:
        await wait_for(lambda: where("pm") == "research" and where("mp") == "broker", 25,
                       "the partners to split up (PM in research, MP at the broker)")
        evidence["split_at_s"] = round(time.monotonic() - t0, 2)
        visits = [await api(prefix + "/commands", pm, {"type": "visit", "location": "research",
                                                       "assignment": "demand_survey"}, "visit-pm"),
                  await api(prefix + "/commands", mp, {"type": "visit", "location": "broker",
                                                       "assignment": "borrow"}, "visit-mp")]
        attention = (await api(prefix + "/view", pm))["attention"]
        claims = attention["partners"]
        assert {r: (c["location"], c["window"]) for r, c in claims.items()} == {
            "pm": ("research", attention["window"]), "mp": ("broker", attention["window"])}, claims
        evidence["assignments"] = {"window": attention["window"], "accepted": visits}

        await wait_for(lambda: where("pm") == where("mp") == "committee", 30, "both partners in the committee room")
        evidence["met_at_s"] = round(time.monotonic() - t0, 2)
        cover = [{"order_id": "cover-recall", "sym": "BRIN", "side": "COVER", "qty": 1250}]
        package = await api(prefix + "/commands", pm, {"type": "propose", "package_id": "committee", "orders": cover},
                            "propose")
        signed = await api(prefix + "/commands", mp, {"type": "sign", "package_id": "committee",
                                                      "digest": package["digest"]}, "sign")
        assert signed["status"] == "AUTHORIZED_QUEUED", signed
        evidence["package"] = {"digest": package["digest"], "status": signed["status"]}
        verified = await api(prefix + "/verify", pm)
        assert verified["ok"] and verified["version"] == 4, verified  # two visits, propose, sign: nothing else
        evidence["verify"] = {k: verified[k] for k in ("ok", "version", "journal_digest", "chain_head")}
    finally:
        errors = await asyncio.to_thread(stop_clients, clients)
        stop.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        evidence["timeline"] = sorted(sees_mp.timeline + sees_pm.timeline)
        evidence["client_errors"] = errors
        Path(args.output).write_text(json.dumps(evidence, indent=1) + "\n", encoding="utf-8")
    assert not errors, errors
    print(json.dumps({k: evidence[k] for k in ("split_at_s", "met_at_s", "package", "verify")}, indent=1))
    print(f"co-op acceptance passed; evidence in {args.output}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--server", default="http://127.0.0.1:8011")
    p.add_argument("--godot", required=True)
    p.add_argument("--exported", action="store_true", help="--godot is an exported FundForge.x86_64")
    p.add_argument("--output", default="coop-acceptance.json")
    a = p.parse_args()
    server, room, clients, t0 = start(a)
    try:
        asyncio.run(main(a, server, room, clients, t0))
    except AssertionError as e:
        stop_clients(clients)
        print(f"co-op acceptance FAILED: {e}", file=sys.stderr)
        sys.exit(1)
