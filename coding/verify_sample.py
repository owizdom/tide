"""Draw the human verification sample (Wisdom, 2026-11-07, replaces the 15-release blind audit):
about 80 final codes, seeded, stratified by item: 50 positives with their supporting quote and
30 zeros with keyword-in-context snippets from the card.

Usage: python3 -m coding.verify_sample   (needs coding/codes.csv with no blank cells)
"""
import csv
import random
import re
from pathlib import Path

from coding import check

ROOT = Path(__file__).resolve().parents[1]
SEED, N_POS, N_ZERO = 20261107, 50, 30


def snippets(text: str, pattern: str, k: int = 3, width: int = 160) -> list[str]:
    out = []
    for m in re.finditer(pattern, text, re.I):
        s = re.sub(r"\s+", " ", text[max(0, m.start() - width): m.end() + width])
        out.append("..." + s + "...")
        if len(out) >= k:
            break
    return out


def main() -> int:
    codes = list(csv.DictReader((ROOT / "coding" / "codes.csv").open()))
    assert all(r[v] != "" for r in codes for v in check.VARIABLES), "unresolved disagreements"
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    a = check.load_pass(ROOT / "coding" / "passes" / "A")
    b = check.load_pass(ROOT / "coding" / "passes" / "B")
    adj = {(r["release_id"], r["variable"]): r for r in csv.DictReader((ROOT / "coding" / "adjudication.csv").open())}
    rng = random.Random(SEED)
    pos = {v: [] for v in check.VARIABLES}
    zer = {v: [] for v in check.VARIABLES}
    for r in codes:
        if r["no_card"] == "1":
            continue
        for v in check.VARIABLES:
            (pos if int(r[v]) > 0 else zer)[v].append(r)

    def draw(pool, n):
        picked, items = [], list(check.VARIABLES)
        while len(picked) < n and any(pool[v] for v in items):
            for v in items:
                if pool[v] and len(picked) < n:
                    picked.append((v, pool[v].pop(rng.randrange(len(pool[v])))))
        return picked

    rows = []
    for kind, (v, r) in [("positive", x) for x in draw(pos, N_POS)] + [("zero", x) for x in draw(zer, N_ZERO)]:
        rid = r["release_id"]
        text = Path(man[rid]["text_path"]).read_text(encoding="utf-8", errors="replace")
        if (rid, v) in adj:
            ev = adj[(rid, v)]["quote"]
        else:
            ev = a[rid]["codes"][v].get("quote") or b[rid]["codes"][v].get("quote") or ""
        if kind == "zero":
            ev = " | ".join(snippets(text, check.KEYWORDS[v])) or "(no keyword hits in the card)"
        rows.append({"n": len(rows) + 1, "release_id": rid, "item": v, "value": r[v], "kind": kind,
                     "evidence": ev, "archive_url": man[rid]["archive_url"], "verdict": "", "comment": ""})
    with (ROOT / "coding" / "verify_sample.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "codes drawn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
