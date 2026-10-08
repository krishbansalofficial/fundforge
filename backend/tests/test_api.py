import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")


def test_two_seat_flow_over_http():
    from fastapi.testclient import TestClient

    from fundforge.api import app

    c = TestClient(app)
    r = c.post("/api/rooms", json={"pm_name": "Ana", "mp_name": "Ben"}).json()
    rid, pm, mp = r["room_id"], r["tokens"]["pm"], r["tokens"]["mp"]
    h = lambda t, k=None: {"Authorization": f"Bearer {t}", **({"Idempotency-Key": k} if k else {})}  # noqa: E731
    assert c.get(f"/api/rooms/{rid}/view").status_code == 401
    assert c.get(f"/api/rooms/{rid}/view", headers=h("forged")).status_code == 401
    v = c.get(f"/api/rooms/{rid}/view", headers=h(pm)).json()
    assert v["role"] == "pm" and v["clock"]["day"] == 12
    bad = c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k1"),
                 json={"type": "ticket", "order_id": "x", "sym": "ALTO", "side": "SELL", "qty": 1})
    assert bad.status_code == 422
    assert c.post(f"/api/rooms/{rid}/commands", headers=h(pm, "k2"), json={"type": "ready"}).json()["advanced"] is False
    assert c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k3"), json={"type": "ready"}).json()["advanced"] is True
    reuse = c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k3"), json={"type": "research", "topic": "borrow"})
    assert reuse.status_code == 409
    led = c.get(f"/api/rooms/{rid}/ledger?entity=firm", headers=h(mp)).json()
    assert led["entries"][0]["memo"] == "Management company opening book"
