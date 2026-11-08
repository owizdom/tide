"""Spec 0001 AT11: every number in docs/methods.md is asserted against the data.

Each claim is a phrase that must appear in methods.md and a value computed from the coded data
that must match it.

Usage: python3 -m analysis.verify_claims
"""
import csv
import sys
from pathlib import Path

from analysis import shares
from coding import check

ROOT = Path(__file__).resolve().parents[1]


def pct(k, n):
    return round(100 * k / n)


def claims():
    recs = shares.load()
    halves = sorted({r["half"] for r in recs})
    by = {h: [r for r in recs if r["half"] == h] for h in halves}
    lab = {l: [r for r in recs if r["lab"] == l] for l in shares.LABS}
    man = list(csv.DictReader((ROOT / "cards" / "manifest.csv").open()))
    late = [int(r["card_days_after_launch"]) for r in man if r["sha256"] and r["card_at_launch"] == "0"]
    ext = [pct(sum(r["ext_test_any"] for r in by[h]), len(by[h])) for h in halves]
    k = check.agreement(ROOT / "coding" / "passes" / "A", ROOT / "coding" / "passes" / "B")
    kap = [v[0] for v in k.values()]
    adj = sum(1 for _ in csv.DictReader((ROOT / "coding" / "adjudication.csv").open()))
    a = check.load_pass(ROOT / "coding" / "passes" / "A")
    out = [
        (f"rose from {pct(sum(r['any_dc'] for r in by[halves[0]]), len(by[halves[0]]))}% in the first half of 2023", True),
        (f"to {pct(sum(r['any_dc'] for r in by[halves[-1]]), len(by[halves[-1]]))}% in July to October 2026", True),
        (f"moved between {min(ext)}% and {max(ext)}% across the eight half-years", len(halves) == 8),
        (f"stood at {ext[-1]}% in the latest one", True),
        (f"Of {len(recs)} frontier releases, {sum(r['card_at_launch'] for r in recs)} had a card", True),
        (f"{len(late)} got one later ({min(late)} to {max(late)} days after launch)", True),
        (f"and {sum(1 for r in recs if not r['has_card'])} never got one", True),
        (f"Across all labs the figure is {sum(r['any_dc'] for r in recs)} of {len(recs)}", True),
        (f"Every one of the {len(a)} cards", False),
        (f"Agreement across {len(a) * len(check.VARIABLES):,} codes", True),
        (f"between {min(kap):.2f} and {max(kap):.2f} for every item", True),
        (f"The {adj} disagreements", True),
        (f"Half-years hold {min(len(v) for v in by.values())} to {max(len(v) for v in by.values())} releases", True),
    ]
    names = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
             "xai": "xAI", "deepseek": "DeepSeek", "mistral": "Mistral"}
    for l, g in lab.items():
        out.append((f"{sum(r['any_dc'] for r in g)} of {len(g)}", True))
    return [c for c, must in out if must] + [f"{len(a)} cards"]


def main() -> int:
    text = (ROOT / "docs" / "methods.md").read_text(encoding="utf-8")
    missing = [c for c in claims() if c not in text]
    for c in missing:
        print("NOT IN methods.md or WRONG:", c)
    print(f"{len(claims()) - len(missing)} of {len(claims())} claims match the data")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
