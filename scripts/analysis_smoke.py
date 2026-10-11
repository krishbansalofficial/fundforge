"""Two-seat local HTTP validation of liquidity drafts and completed-run replay.

Prints public evidence only. Seat tokens remain in memory, never in the output.
Run against a local API with PostgreSQL: python scripts/analysis_smoke.py
"""

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8011")
    parser.add_argument("--broker-challenge", action="store_true")
    args = parser.parse_args()

    def call(path, token=None, body=None, key=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if key:
            headers["Idempotency-Key"] = key
        request = Request(args.server + path, headers=headers,
                          data=json.dumps(body).encode() if body is not None else None)
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    room = call("/api/rooms", body={"pm_name": "Lab PM", "mp_name": "Lab MP",
                                   "scenario": "case1-controls" if args.broker_challenge else "case1"})
    path = "/api/rooms/" + room["room_id"]
    pm, mp = room["tokens"]["pm"], room["tokens"]["mp"]
    if args.broker_challenge:
        queue = call(path + "/terminal", mp)["risk"]["controls"]["statement_queue"]
        assert queue[0]["revision"] == 1 and not queue[0]["can_resolve"]
    call(path + "/commands", mp, {"type": "visit", "location": "broker", "assignment": "borrow"}, "borrow")
    call(path + "/commands", pm, {"type": "visit", "location": "research", "assignment": "demand_survey"}, "demand")

    def view():
        return call(path + "/view", pm)

    def advance():
        for token in (pm, mp):
            version = view()["version"]
            call(path + "/commands", token, {"type": "ready", "version": version}, f"ready-{version}")

    try:
        call(path + "/debrief", pm, {"version": view()["version"]})
        raise AssertionError("unfinished room exposed replay")
    except HTTPError as error:
        assert error.code == 422
    while view()["clock"]["day"] < 13:
        advance()
    review_seq = None
    if args.broker_challenge:
        before_review = call(path + "/verify", mp)
        terminal = call(path + "/terminal", mp)
        review_seq = terminal["version"] + 1
        call(path + "/commands", mp, {"type": "resolve_statement", "statement_id": "opening-cash", "revision": 2,
                                      "version": terminal["version"]}, "review-statement")
        after_review = call(path + "/verify", mp)
        assert before_review["journal_digest"] == after_review["journal_digest"]
        queue = call(path + "/terminal", mp)["risk"]["controls"]["statement_queue"]
        assert queue[0]["status"] == "resolved" and len(queue[0]["history"]) == 2

    def borrow_news(token):
        return [n for n in call(path + "/terminal", token)["news"]
                if n["code"] == "research_reveal" and n["refs"]["topic"] == "borrow"]

    assert borrow_news(mp) and not borrow_news(pm)
    call(path + "/commands", mp, {"type": "share_research", "topic": "borrow"}, "share-borrow")
    assert borrow_news(pm) == borrow_news(mp)
    decision_seq = view()["version"] + 1
    call(path + "/commands", pm, {"type": "ticket", "order_id": "analysis-cover", "sym": "BRIN",
                                  "side": "COVER", "qty": 1250}, "cover")
    while view()["clock"]["day"] < 16:
        advance()
    version = view()["version"]
    verification = call(path + "/verify", pm)
    lab = call(path + "/liquidity", pm, {"version": version, "long_shock": "-0.60", "short_shock": "0.80"})
    assert lab["version"] == version and len(lab["comparisons"]) == 2
    assert call(path + "/verify", mp) == verification
    assert view()["version"] == version
    count = 0
    while not view()["clock"]["finished"]:
        advance()
        count += 1
        assert count < 30
    version = view()["version"]
    before = call(path + "/verify", pm)
    admin = call(path + "/terminal", mp)["risk"]["controls"]["administrator"]
    assert admin["status"] == "checked" and admin["close_count"] == 13 and admin["claim_count"] == 1
    baseline = call(path + "/debrief", pm, {"version": version})
    branch = call(path + "/debrief", mp, {"version": version, "omit_seq": decision_seq})
    assert baseline["state"]["journal_digest"] == before["journal_digest"]
    assert baseline["nav_difference"] == "0.00"
    assert any(i["code"] == "forced_recall" for i in branch["incidents"])
    assert call(path + "/verify", pm) == before and before["ok"]
    if review_seq is not None:
        no_review = call(path + "/debrief", mp, {"version": version, "omit_seq": review_seq})
        assert no_review["finished"] and any(i["code"] == "dealing_blocked" for i in no_review["incidents"])
        assert call(path + "/verify", pm) == before
    print(json.dumps({"ok": True, "rules": baseline["rules_version"], "version": version,
                      "liquidity_strategies": len(lab["comparisons"]), "baseline_exact": True,
                      "counterfactual_finished": branch["finished"], "omitted_decision": decision_seq,
                      "counterfactual_nav_difference": branch["nav_difference"],
                      "counterfactual_forced_recall": True, "live_books_unchanged": True,
                      "private_evidence_then_explicit_sharing": True,
                      "broker_challenge": args.broker_challenge,
                      "independent_lp_checks": admin["status"], "checked_redemptions": admin["claim_count"],
                      "omitted_review_blocks_dealing": review_seq is not None}, indent=2))


if __name__ == "__main__":
    main()
