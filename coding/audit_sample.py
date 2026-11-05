"""Pick the 15-release hand-audit sample (spec 0001 AT8): stratified by lab, then spread over years,
from releases that have a card. Seeded, so the sample is reproducible and not hand-picked.

Usage: python3 -m coding.audit_sample
"""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261105
N = 15


def sample() -> list[str]:
    rel = {r["release_id"]: r for r in csv.DictReader((ROOT / "releases" / "frontier.csv").open())}
    man = [r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open()) if r["sha256"]]
    by_lab: dict[str, list[str]] = {}
    for r in man:
        by_lab.setdefault(rel[r["release_id"]]["lab"], []).append(r["release_id"])
    rng = random.Random(SEED)
    for ids in by_lab.values():
        ids.sort(key=lambda i: rel[i]["available_date"])
    picks: list[str] = []
    labs = sorted(by_lab)
    # two per lab (one from each half of its timeline), then fill to N at random
    for lab in labs:
        ids = by_lab[lab]
        half = max(1, len(ids) // 2)
        picks.append(rng.choice(ids[:half]))
        if len(ids) > 1:
            picks.append(rng.choice(ids[half:]))
    rest = [i for lab in labs for i in by_lab[lab] if i not in picks]
    while len(picks) < N and rest:
        picks.append(rest.pop(rng.randrange(len(rest))))
    return sorted(picks[:N])


if __name__ == "__main__":
    for i in sample():
        print(i)
