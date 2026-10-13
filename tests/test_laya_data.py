"""Unit tests for the Laya data files (training/build_laya_data.py): the state Laya reads, the split."""

from training.build_laya_data import split_by_group, state


def test_state_starts_with_the_subdomain_when_known():
    assert state("Title", "Text", ("6.5", "Governance failure")) == "Risk subdomain: 6.5 Governance failure\nTitle\nText"
    assert state("Title", "Text") == "Title\nText"
    assert state("", "Text") == "Text"


def test_split_by_group_keeps_each_group_on_one_side():
    rows = [{"id": f"{g:02d}.{c:02d}.{k:02d}"} for g in range(10) for c in range(3) for k in range(4)]
    fit, val = split_by_group(rows, 0.15, 0)
    group = lambda r: ".".join(r["id"].split(".")[:2])
    assert {group(r) for r in fit}.isdisjoint(group(r) for r in val)
    assert len(fit) + len(val) == len(rows) and len(val) >= 0.15 * len(rows)


def test_no_risk_entries_are_recognised_by_their_title():
    from training.build_laya_data import NO_RISK

    assert NO_RISK.match("Nessun rischio significativo di disinformazione")
    assert NO_RISK.match("No significant risk of toxic content")
    assert not NO_RISK.match("Risk of no human oversight") and not NO_RISK.match("Rischio di nessun controllo umano")
