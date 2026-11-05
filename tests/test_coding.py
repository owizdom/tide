"""Track C tests (spec 0001 AT6, AT7, AT8): quote-gated codes, keyword screen on zeros, agreement."""
import json
from pathlib import Path

from coding import check

ROOT = Path(__file__).resolve().parents[1]


def test_normalise_collapses_whitespace_quotes_and_hyphen_breaks():
    a = check.norm("We  evaluated\nthe model’s “cyber”\ncapa-\nbilities")
    b = check.norm('we evaluated the model\'s "cyber" capabilities')
    assert a == b


def test_zero_width_characters_ignored():
    assert check.quote_found("System Card: Claude", "System Card:\u200b Claude Opus")


def test_quote_found_and_not_found():
    text = "Section 4. We ran CTF challenges and the model solved 12 of 40.\n"
    assert check.quote_found("the model solved 12 of 40", text)
    assert not check.quote_found("the model solved 40 of 40", text)
    assert not check.quote_found("", text)


def test_keyword_hits_by_item():
    text = "We assessed biological risk and offensive cyber capability. No persuasion tests."
    hits = check.keyword_hits(text)
    assert hits["dc_eval_cbrn"] and hits["dc_eval_cyber"] and hits["dc_eval_persuasion"]
    assert not hits["dc_eval_autonomy"]


def test_cohen_kappa_perfect_and_chance():
    assert check.kappa([1, 0, 2, 1], [1, 0, 2, 1]) == 1.0
    assert abs(check.kappa([1, 0, 1, 0], [0, 1, 0, 1]) - (-1.0)) < 1e-9
    assert check.kappa([1, 1, 1], [1, 1, 1]) == 1.0  # no variance, full agreement


def test_validate_pass_record_schema():
    good = {"release_id": "x", "codes": {v: {"value": 0, "quote": "", "locator": ""} for v in check.VARIABLES}}
    assert check.validate(good) == []
    bad = json.loads(json.dumps(good))
    bad["codes"]["dc_eval_cyber"]["value"] = 3
    bad["codes"].pop("safeguards_weights")
    probs = check.validate(bad)
    assert any("dc_eval_cyber" in p for p in probs) and any("safeguards_weights" in p for p in probs)


def test_positive_without_quote_is_a_problem():
    rec = {"release_id": "x", "codes": {v: {"value": 0, "quote": "", "locator": ""} for v in check.VARIABLES}}
    rec["codes"]["framework_threshold"] = {"value": 2, "quote": "", "locator": "p.3"}
    assert any("framework_threshold" in p for p in check.validate(rec))


def test_at6_every_positive_code_quote_is_in_the_card():
    passes = ROOT / "coding" / "passes"
    assert passes.exists() and any(passes.iterdir()), "no coding passes yet"
    probs = check.verify_all(passes)
    assert probs == [], "\n".join(probs[:20])


def test_passes_are_independent():
    """Two independent coders never share most of their free-text notes for one release."""
    a_dir, b_dir = ROOT / "coding" / "passes" / "A", ROOT / "coding" / "passes" / "B"
    a, b = check.load_pass(a_dir), check.load_pass(b_dir)
    bad = []
    for rid in sorted(set(a) & set(b)):
        same = sum(1 for v in check.VARIABLES
                   if a[rid]["codes"].get(v, {}).get("note") and
                   a[rid]["codes"][v]["note"] == b[rid]["codes"].get(v, {}).get("note"))
        if same >= 4:
            bad.append((rid, same))
    assert bad == [], bad
