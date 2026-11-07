"""Track D tests (spec 0001 AT9-AT10 and the section 1.3 case rule)."""
from analysis import shares


def test_disclosed_levels():
    assert shares.disclosed("dc_eval_cyber", 2) and not shares.disclosed("dc_eval_cyber", 1)
    assert shares.disclosed("framework_threshold", 2) and not shares.disclosed("framework_threshold", 1)
    assert shares.disclosed("ext_test_any", 1) and not shares.disclosed("ext_test_any", 0)


def test_wilson_bounds():
    lo, hi = shares.wilson(5, 10)
    assert 0.2 < lo < 0.5 < hi < 0.8
    assert shares.wilson(0, 0) == (0.0, 0.0)


def test_late_card_discloses_nothing_at_launch():
    recs = shares.load()
    for r in recs:
        if not r["card_at_launch"]:
            assert not any(r[v] for v, _ in shares.ITEMS), r["release_id"]


def test_every_release_counted_once_per_half():
    recs = shares.load()
    t = shares.share_table(recs)
    for item, _ in shares.ITEMS:
        assert sum(row["n"] for row in t if row["item"] == item) == len(recs) == 87


def test_at9_coverage_five_labs_six_halves():
    recs = shares.load()
    wide = [lab for lab in shares.LABS if len({r["half"] for r in recs if r["lab"] == lab}) >= 6]
    assert len(wide) >= 5


def test_drops_follow_lab_sequence():
    d = shares.drops(shares.load())
    assert d and all(x["n_lost"] >= 1 for x in d)
    assert d == sorted(d, key=lambda x: (x["n_lost"], x["to_date"]), reverse=True)  # spec 1.3: ties to the later date
