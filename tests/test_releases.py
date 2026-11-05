"""Acceptance tests for Track A (spec 0001, section 1.1): the frozen frontier list.

AT1: rule.py on the pinned Epoch zip and ladders.yaml reproduces frontier.csv byte for byte.
Plus the consistency checks that make every judgement in ladders.yaml mechanically checkable.
"""
import csv
import hashlib
import io
from pathlib import Path

import pytest

from releases import rule

ROOT = Path(__file__).resolve().parents[1]
PINNED_ZIP_SHA256 = "a31aafbf290549655ca57ef4d6f207cdc9bc036dfbde183c14ba5114323d6ee4"
LABS = {"anthropic", "openai", "google", "meta", "xai", "mistral", "deepseek"}


@pytest.fixture(scope="module")
def built():
    return rule.build(rule.default_zip_path(), ROOT / "releases" / "ladders.yaml")


def test_pinned_input_hash():
    assert rule.sha256_file(rule.default_zip_path()) == PINNED_ZIP_SHA256


def test_wrong_zip_hash_is_refused(tmp_path):
    fake = tmp_path / "ai_models.zip"
    fake.write_bytes(b"not the pinned export")
    with pytest.raises(rule.InputMismatch):
        rule.load_candidates(fake)


def test_candidate_filter_bounds(built):
    cands = built.candidates
    assert cands, "no candidates"
    for c in cands:
        assert c.lab in LABS
        assert "2023-01-01" <= c.epoch_date <= "2026-10-31"
        assert not c.accessibility.startswith("Unreleased")


def test_every_candidate_has_exactly_one_decision(built):
    names = [c.epoch_name for c in built.candidates]
    assert len(names) == len(set(names)), "duplicate Epoch names in candidate pool"
    decided = set(built.decisions)
    assert set(names) == decided, (
        f"undecided: {sorted(set(names) - decided)[:10]} ; unknown in yaml: {sorted(decided - set(names))[:10]}"
    )


def test_reason_codes_are_from_frozen_vocabulary(built):
    for name, d in built.decisions.items():
        assert d.reason in rule.INCLUDE_REASONS | rule.EXCLUDE_REASONS, (name, d.reason)


def test_consistency_checks_pass(built):
    problems = rule.check_consistency(built)
    assert problems == [], "\n".join(problems)


def test_consistency_checker_catches_a_bad_higher_tier(built):
    import copy

    bad = copy.deepcopy(built)
    # Opus 4.5 is HIGHER_TIER over Sonnet 4.5; point it at a model of another version.
    d = bad.decisions["Claude Opus 4.5"]
    assert d.reason == "HIGHER_TIER"
    d.ref = "Claude 3 Opus"
    assert rule.check_consistency(bad), "checker accepted a HIGHER_TIER ref of another version"


def test_consistency_checker_catches_an_include_of_a_small_tier(built):
    import copy

    bad = copy.deepcopy(built)
    d = bad.decisions["GPT-4o mini"]
    d.reason, d.ref = "NEW_VERSION", None
    assert rule.check_consistency(bad), "checker accepted a small tier as a frontier release"


def test_one_event_per_lab_per_day(built):
    keys = [(e.lab, e.available_date) for e in built.events]
    assert len(keys) == len(set(keys))


def test_release_ids_unique_and_stable_format(built):
    ids = [e.release_id for e in built.events]
    assert len(ids) == len(set(ids))
    for e in built.events:
        assert e.release_id.startswith(f"{e.lab}-{e.available_date}-")


def test_frozen_csv_reproduces_byte_for_byte(built):
    frozen = ROOT / "releases" / "frontier.csv"
    assert frozen.exists(), "frontier.csv not generated yet"
    assert rule.render_csv(built.events) == frozen.read_text(encoding="utf-8")


def _freeze_entry():
    """The JOURNAL line `FREEZE frontier.csv sha256 <hex> at <ISO time>` written when Wisdom approves."""
    import re

    text = (ROOT / "docs" / "JOURNAL.md").read_text(encoding="utf-8")
    m = re.search(r"^- FREEZE frontier\.csv sha256 ([0-9a-f]{64}) at (\S+)", text, re.M)
    return (m.group(1), m.group(2)) if m else None


def test_at1_hash_matches_journal_freeze_entry(built):
    entry = _freeze_entry()
    assert entry, "list not frozen: no FREEZE entry in docs/JOURNAL.md"
    assert entry[0] == hashlib.sha256(rule.render_csv(built.events).encode("utf-8")).hexdigest()


def test_at2_freeze_precedes_every_card_fetch():
    entry = _freeze_entry()
    assert entry, "list not frozen: no FREEZE entry in docs/JOURNAL.md"
    manifest = ROOT / "cards" / "manifest.csv"
    if manifest.exists():
        for row in csv.DictReader(manifest.open(encoding="utf-8")):
            assert row["fetched_at"] > entry[1], (row["release_id"], row["fetched_at"], entry[1])


def test_available_date_overrides_carry_a_source(built):
    for name, d in built.decisions.items():
        if d.available:
            assert d.available_src, name


def test_o3_dated_at_public_release(built):
    ev = {e.model: e for e in built.events}
    assert ev["o3"].available_date == "2025-04-16"
    assert ev["o3"].epoch_date == "2024-12-20"


def test_coverage_at_least_five_labs_in_six_halves(built):
    halves = {}
    for e in built.events:
        halves.setdefault(e.lab, set()).add(rule.half_year(e.epoch_date))
    wide = [lab for lab, hs in halves.items() if len(hs) >= 6]
    assert len(wide) >= 5, {lab: sorted(hs) for lab, hs in halves.items()}


def test_csv_columns_match_seam_contract(built):
    rows = list(csv.DictReader(io.StringIO(rule.render_csv(built.events))))
    assert list(rows[0].keys()) == [
        "release_id", "lab", "model", "epoch_name", "epoch_date", "available_date",
        "tier", "rule_reason", "event_models",
    ]
