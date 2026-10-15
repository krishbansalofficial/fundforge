"""End-to-end check of the Kafka pipeline against the real stack in deploy/kafka/compose.yaml.

Run from ml/ after `deploy/kafka/fetch-debezium.sh` and `docker compose -f ../deploy/kafka/compose.yaml up -d`:
    uv run --group stream python scripts/kafka_e2e.py

1. Plays part of a solo game through Store on the compose Postgres, registers the Debezium
   outbox connector, consumes every fundforge.* topic from offset 0 with a fresh consumer group,
   and requires the streamed seat features to equal the batch features of the outbox table.
2. Stops the Kafka broker, finishes the game (the game must not notice) and verifies the books.
3. Starts Kafka again, restarts the single Connect worker (its documented recovery step), lets
   Debezium resume from its replication slot, re-reads from offset 0,
   and requires streamed == batch and every outbox event delivered. Writes results/kafka_e2e.json.
"""

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from confluent_kafka import Consumer
from fundforge.store import Store

from fundforge_ml import stream

ML = Path(__file__).parents[1]
COMPOSE = ["docker", "compose", "-f", str(ML.parent / "deploy" / "kafka" / "compose.yaml")]
ENVELOPE = ("event_id", "contract_version", "room_id", "seq", "idx", "kind", "audience", "rules_version",
            "tape_digest", "day", "phase", "sim_date", "chain_head")


def _body(raw: bytes) -> Any:
    try:
        return json.loads(raw or b"null")
    except ValueError:  # e.g. Connect's REST server answers with plain text/HTML while starting up
        return raw.decode(errors="replace")


def http(method: str, url: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, _body(r.read())
    except urllib.error.HTTPError as e:
        return e.code, _body(e.read())


def wait_connector(connect: str, timeout: float = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            code, st = http("GET", f"{connect}/connectors/fundforge-outbox/status")
            if code == 200 and st["connector"]["state"] == "RUNNING" and st["tasks"] and all(
                    t["state"] == "RUNNING" for t in st["tasks"]):
                return
            if code == 200 and any(t["state"] == "FAILED" for t in st["tasks"]):
                http("POST", f"{connect}/connectors/fundforge-outbox/restart?includeTasks=true&onlyFailed=true")
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError("Debezium connector did not reach RUNNING")


def register(connect: str) -> None:
    deadline = time.time() + 180
    while True:
        try:
            code, _ = http("GET", f"{connect}/connectors")
            if code == 200:
                break
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        if time.time() > deadline:
            raise TimeoutError("Kafka Connect REST did not come up")
        time.sleep(2)
    spec = json.loads((ML.parent / "deploy" / "kafka" / "outbox-connector.json").read_text("utf-8"))
    code, body = http("POST", f"{connect}/connectors", spec)
    if code not in (201, 409):
        raise RuntimeError(f"connector registration failed: {code} {body}")
    wait_connector(connect)


def consume_all(bootstrap: str, idle: float = 15.0) -> list[dict[str, Any]]:
    """Every message on fundforge.* from offset 0, with a fresh group (no committed offsets)."""
    c = Consumer({"bootstrap.servers": bootstrap, "group.id": f"e2e-{time.time_ns()}",
                  "auto.offset.reset": "earliest", "enable.auto.commit": False,
                  "topic.metadata.refresh.interval.ms": 2000})
    c.subscribe(["^fundforge\\..*s$"])
    out, last = [], time.time()
    try:
        while time.time() - last < idle:
            msg = c.poll(1.0)
            if msg is None or msg.error():
                continue
            v = json.loads(msg.value())
            out.append({**{k: v[k] for k in ENVELOPE}, "payload": v["payload"], "_topic": msg.topic()})
            last = time.time()
    finally:
        c.close()
    return out


def ready_rounds(st: Store, rid: str, pm: str, rounds: int, tag: str) -> None:
    for k in range(rounds):
        v, s, _ = st.session(rid)
        if s.e.finished():
            return
        st.apply(rid, pm, f"{tag}{k}", {"type": "ready", "version": v})


def check(rid: str, streamed: list[dict[str, Any]], batch: list[dict[str, Any]]) -> dict[str, Any]:
    mine = [e for e in streamed if e["room_id"] == rid]
    wrong_topic = [e for e in mine if e["_topic"] != f"fundforge.{e['kind']}s"]
    ok = (stream.features(rid, mine) == stream.features(rid, batch)
          and {e["event_id"] for e in mine} == {e["event_id"] for e in batch} and not wrong_topic)
    return {"ok": ok, "messages": len(mine), "distinct_events": len({e["event_id"] for e in mine}),
            "outbox_rows": len(batch), "wrong_topic": len(wrong_topic)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="postgresql://fundforge:fundforge@127.0.0.1:55432/fundforge")
    ap.add_argument("--bootstrap", default="127.0.0.1:29092")
    ap.add_argument("--connect", default="http://127.0.0.1:8083")
    args = ap.parse_args()
    st = Store(args.dsn)
    st.init()  # migrations first: the connector's publication needs the outbox table
    register(args.connect)
    r = st.create_room("case1", "Ana", "", variant="base", solo_role="pm")
    rid, pm = r["room_id"], st.auth(r["room_id"], r["tokens"]["pm"])
    ready_rounds(st, rid, pm, 4, "a")
    phase1 = check(rid, consume_all(args.bootstrap), st.outbox(rid))
    print("phase 1 (live):", phase1, flush=True)

    subprocess.run([*COMPOSE, "stop", "kafka"], check=True, capture_output=True)
    t0 = time.perf_counter()
    ready_rounds(st, rid, pm, 40, "b")
    v, s, _ = st.session(rid)
    verified = st.verify(rid)
    offline = {"finished": s.e.finished(), "version": v, "verified_version": verified["version"],
               "seconds": round(time.perf_counter() - t0, 2)}
    print("kafka stopped, game continued:", offline, flush=True)

    subprocess.run([*COMPOSE, "start", "kafka"], check=True, capture_output=True)
    # A single Connect worker coordinates through the broker, so after an outage its source task
    # cannot stop cleanly; the documented recovery is restarting the worker. Debezium then resumes
    # from its committed offset and the Postgres replication slot (at-least-once; deduped by event_id).
    time.sleep(10)
    subprocess.run([*COMPOSE, "restart", "connect"], check=True, capture_output=True)
    wait_connector(args.connect)
    phase2 = check(rid, consume_all(args.bootstrap, idle=30.0), st.outbox(rid))
    print("phase 2 (after restart, from offset 0):", phase2, flush=True)
    st.close()
    result = {"room": rid, "phase1_live": phase1, "kafka_stopped": offline, "phase2_recovered": phase2,
              "feature_version": stream.FEATURE_VERSION}
    (ML / "results").mkdir(exist_ok=True)
    (ML / "results" / "kafka_e2e.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not (phase1["ok"] and phase2["ok"] and offline["finished"]):
        raise SystemExit("kafka e2e failed")


if __name__ == "__main__":
    main()
