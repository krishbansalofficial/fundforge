"""Real HTTP and headless Godot acceptance of withheld case1-controls dealing.

Requires a local clock-disabled API with test variants enabled. No statement is
resolved. Evidence contains no seat tokens. Headless label checks are programmatic
client evidence, not a graphical human playtest.

python scripts/certification_acceptance.py --server http://127.0.0.1:8030 --godot godot_console.exe
"""

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

GAME = Path(__file__).resolve().parents[1] / "game"
HTTP = build_opener(ProxyHandler({}))


def call(server, path, token=None, body=None, key=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    data = json.dumps(body).encode() if body is not None else None
    with HTTP.open(Request(server + path, headers=headers, data=data), timeout=30) as response:
        return json.load(response)


def capture(args, room, role, output):
    command = [args.godot, "--headless", "--max-fps", "30"]
    if not args.exported:
        command += ["--path", str(GAME)]
    command += ["--", f"--server={args.server}",
                f"--join={room['room_id']}:{room['tokens'][role]}",
                f"--certification-evidence={output}"]
    # Never include the command in errors: its join argument holds a seat token.
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
    except subprocess.TimeoutExpired:
        raise AssertionError(f"{role} Godot evidence capture timed out") from None
    logs = process.stdout + process.stderr
    assert process.returncode == 0, f"{role} Godot evidence capture failed"
    assert "SCRIPT ERROR" not in logs and "ERROR:" not in logs, f"{role} Godot reported an engine error"
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["role"] == role and evidence["certification"] == "broken"
    assert "Latest dealing-close: Broken" in evidence["hud_stats"]
    assert "Latest dealing was withheld" in evidence["hud_stats"]
    assert "Not a new check of current NAV." in evidence["hud_stats"]
    assert any("CERTIFICATION: BROKEN" in label for label in evidence["risk_labels"])
    assert any("Certification blocked: broker statement" in label for label in evidence["risk_labels"])
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8030")
    parser.add_argument("--godot", required=True)
    parser.add_argument("--exported", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("artifacts/certification-acceptance"))
    args = parser.parse_args()
    args.server = args.server.rstrip("/")
    room = call(args.server, "/api/rooms", body={"scenario": "case1-controls", "variant": "base",
                                               "pm_name": "Certification PM", "mp_name": "Certification MP"})
    prefix = "/api/rooms/" + room["room_id"]
    tokens = room["tokens"]
    for role in ("pm", "mp"):
        assert call(args.server, prefix + "/view", tokens[role])["certification"] == "pending"
    for step in range(100):
        view = call(args.server, prefix + "/view", tokens["pm"])
        if view["clock"]["day"] >= 21:
            break
        assert view["outcome"] is None, "scenario ended before dealing-close acceptance"
        for role in ("pm", "mp"):
            version = call(args.server, prefix + "/view", tokens[role])["version"]
            call(args.server, prefix + "/commands", tokens[role],
                 {"type": "ready", "version": version}, f"cert-ready-{step}-{role}")
    else:
        raise AssertionError("scenario did not reach day 21")
    terminals = {role: call(args.server, prefix + "/terminal", tokens[role]) for role in ("pm", "mp")}
    certificate = terminals["pm"]["risk"]["certification"]
    assert certificate == terminals["mp"]["risk"]["certification"]
    assert certificate["status"] == "broken"
    assert certificate["certificates"][-1]["reasons"] == ["broker_statement"]
    assert terminals["pm"]["risk"]["controls"]["administrator"]["claims"] == [], "withheld dealing created an LP claim"
    views = {role: call(args.server, prefix + "/view", tokens[role]) for role in ("pm", "mp")}
    assert all(view["certification"] == "broken" for view in views.values())
    assert any(event["code"] == "dealing_blocked" for event in views["pm"]["incident_events"])
    assert not any(decision["type"] == "resolve_statement" for decision in views["mp"]["decisions"])
    verified = call(args.server, prefix + "/verify", tokens["pm"])
    assert verified["ok"]
    args.output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(capture, args, room, role, (args.output / f"{role}-godot.json").resolve())
                   for role in ("pm", "mp")]
        clients = [future.result() for future in futures]
    assert all(client["version"] == verified["version"] for client in clients)
    evidence = {"room": room["room_id"], "kind": "HTTP and headless programmatic label evidence",
                "graphical_human_playtest": False, "statement_resolution_omitted": True,
                "as_of": terminals["pm"]["as_of"], "withheld_lp_claim_count": 0,
                "certification": certificate, "clients": clients,
                "verify": {key: verified[key] for key in ("ok", "version", "journal_digest", "chain_head")}}
    encoded = json.dumps(evidence, indent=2) + "\n"
    assert all(token not in encoded for token in tokens.values()), "evidence unexpectedly contains a seat token"
    (args.output / "acceptance.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({"ok": True, "certification": "broken", "seats": ["pm", "mp"],
                      "books_verified": True, "graphical_human_playtest": False,
                      "evidence": str(args.output)}))


if __name__ == "__main__":
    main()
