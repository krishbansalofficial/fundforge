"""Two-seat HTTP terminal smoke against a LOCAL running API.

Creates a paused disposable room, signs and fills a package, advances to day 16,
and verifies the books. Artifacts include seat tokens: keep the output private.
Usage: python scripts/terminal_smoke.py --server http://127.0.0.1:8011 --output artifacts/terminal-smoke
"""

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=Path("artifacts/terminal-smoke"))
    args = parser.parse_args()

    def request(path, token=None, body=None, key=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if key:
            headers["Idempotency-Key"] = key
        req = Request(args.server.rstrip("/") + path, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
        with urlopen(req, timeout=15) as response:
            return json.load(response)

    room = request("/api/rooms", body={"pm_name": "Terminal PM", "mp_name": "Terminal MP"})
    prefix = "/api/rooms/" + room["room_id"]
    pm, mp = room["tokens"]["pm"], room["tokens"]["mp"]
    try:
        request(prefix + "/terminal")
        raise AssertionError("terminal accepted an unauthenticated read")
    except HTTPError as error:
        assert error.code == 401
    initial, initial_mp = request(prefix + "/terminal", pm), request(prefix + "/terminal", mp)
    assert (initial.pop("role"), initial_mp.pop("role")) == ("pm", "mp")
    assert initial == initial_mp  # nothing private exists before any research assignment
    proposed = request(prefix + "/commands", pm, {"type": "propose", "package_id": "smoke-package",
                       "orders": [{"order_id": "smoke-cover", "sym": "BRIN", "side": "COVER", "qty": 1250}]}, "propose")
    assert request(prefix + "/terminal", pm)["orders"] == []
    signature = {"type": "sign", "package_id": "smoke-package", "digest": proposed["digest"]}
    try:
        request(prefix + "/commands", pm, signature, "self-sign")
        raise AssertionError("self-signature authorized a package")
    except HTTPError as error:
        assert error.code == 422
    request(prefix + "/commands", mp, signature, "partner-sign")
    queued = request(prefix + "/terminal", pm)
    assert queued["orders"][0]["filled"] == 0
    count = 0
    while request(prefix + "/view", pm)["clock"]["day"] < 16:
        for actor, token in [("pm", pm), ("mp", mp)]:
            version = request(prefix + "/view", token)["version"]
            request(prefix + "/commands", token, {"type": "ready", "version": version}, f"ready-{count}-{actor}")
        count += 1
        assert count < 30, "scenario did not reach day 16"
    final = request(prefix + "/terminal", pm)
    assert final["orders"][0]["filled"] == 1250
    verified = request(prefix + "/verify", pm)
    assert verified["ok"]
    assert final["version"] == request(prefix + "/terminal", mp)["version"] == verified["version"]
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [("room", room), ("snapshot", final), ("verification", verified)]:
        (args.output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "day": final["as_of"]["day"], "observations": len(final["history"]),
                      "quotes": len(final["quotes"]), "version": final["version"],
                      "cover_filled": final["orders"][0]["filled"], "books_verified": True}))


if __name__ == "__main__":
    main()
