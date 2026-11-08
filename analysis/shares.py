"""Track D: disclosure shares by half-year and lab, and drop case studies (spec 0001 sections 1.2, 1.3).

An item is disclosed when its code is 2 (dangerous-capability domains, framework threshold) or 1
(binary items). At launch means the card was public by launch + 2 days (cards/manifest.csv
card_at_launch); a release with a late card or no card discloses nothing at launch. The
first-card measure ignores timing and counts the first card whenever it appeared.

Usage: python3 -m analysis.shares
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path

from coding import check
from releases.rule import half_year

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "out"

ITEMS = [
    ("card_at_launch", "Card public at launch"),
    ("dc_eval_cbrn", "Bio, chem or nuclear result"),
    ("dc_eval_cyber", "Cyber result"),
    ("dc_eval_autonomy", "Autonomy or AI R&D result"),
    ("dc_eval_persuasion", "Persuasion result"),
    ("dc_eval_scheming", "Deception or scheming result"),
    ("framework_threshold", "Framework threshold stated"),
    ("ext_test_any", "Outside testing"),
    ("ext_test_named_org", "Named outside tester"),
    ("ext_test_government", "Government testing"),
    ("ext_test_timing_stated", "Pre-release timing stated"),
    ("safeguards_training", "Safety training"),
    ("safeguards_runtime", "Runtime safeguards"),
    ("safeguards_access", "Access restrictions"),
    ("safeguards_weights", "Weight security"),
]
LABS = ["anthropic", "openai", "google", "meta", "xai", "mistral", "deepseek"]
DC = ["dc_eval_cbrn", "dc_eval_cyber", "dc_eval_autonomy", "dc_eval_persuasion", "dc_eval_scheming"]


def disclosed(var: str, value: int) -> bool:
    return value >= (2 if var in check.THREE_LEVEL else 1)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load() -> list[dict]:
    codes = {r["release_id"]: r for r in csv.DictReader((ROOT / "coding" / "codes.csv").open())}
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    rel = list(csv.DictReader((ROOT / "releases" / "frontier.csv").open()))
    out = []
    for r in rel:
        rid = r["release_id"]
        c, m = codes[rid], man[rid]
        at_launch = m["card_at_launch"] == "1"
        rec = {"release_id": rid, "lab": r["lab"], "model": r["model"], "date": r["available_date"],
               "half": half_year(r["available_date"]), "has_card": c["no_card"] == "0",
               "card_at_launch": at_launch, "card_words": int(m["words"] or 0)}
        for v in check.VARIABLES:
            d = c["no_card"] == "0" and disclosed(v, int(c[v]))
            rec[v + "__first"] = d
            rec[v] = d and at_launch
        rec["card_at_launch__first"] = rec["has_card"]
        rec["any_dc"] = any(rec[v] for v in DC)
        out.append(rec)
    return out


def share_table(recs: list[dict], measure: str = "") -> list[dict]:
    halves = sorted({r["half"] for r in recs})
    rows = []
    for var, label in ITEMS:
        key = var + measure if var != "card_at_launch" or measure else var
        for h in halves:
            g = [r for r in recs if r["half"] == h]
            k = sum(1 for r in g if r[key])
            lo, hi = wilson(k, len(g))
            rows.append({"item": var, "label": label, "half": h, "n": len(g), "k": k,
                         "share": round(k / len(g), 4) if g else "", "lo": round(lo, 4), "hi": round(hi, 4)})
    return rows


def lab_table(recs: list[dict], key: str = "any_dc") -> list[dict]:
    halves = sorted({r["half"] for r in recs})
    rows = []
    for lab in LABS:
        for h in halves:
            g = [r for r in recs if r["lab"] == lab and r["half"] == h]
            rows.append({"lab": lab, "half": h, "n": len(g), "k": sum(1 for r in g if r[key])})
    return rows


def drops(recs: list[dict]) -> list[dict]:
    """Spec 1.3: items disclosed at launch by one release and not by the lab's next release."""
    out = []
    for lab in LABS:
        seq = sorted((r for r in recs if r["lab"] == lab), key=lambda r: r["date"])
        for prev, nxt in zip(seq, seq[1:]):
            lost = [v for v, _ in ITEMS if v != "card_at_launch" and prev[v] and not nxt[v]]
            if lost:
                out.append({"lab": lab, "from": prev["model"], "from_date": prev["date"], "to": nxt["model"],
                            "to_date": nxt["date"], "n_lost": len(lost), "lost": " ".join(lost)})
    out.sort(key=lambda d: (d["n_lost"], d["to_date"]), reverse=True)  # most items lost; ties to the later date
    return out


def write(path: Path, rows: list[dict]) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    recs = load()
    write(OUT / "share_by_half.csv", share_table(recs))
    write(OUT / "share_by_half_first_card.csv", share_table(recs, "__first"))
    write(OUT / "lab_by_half_any_dc.csv", lab_table(recs))
    write(OUT / "drops.csv", drops(recs))
    write(OUT / "releases_coded.csv", [{k: v for k, v in r.items() if not k.endswith("__first")} for r in recs])
    print(f"releases {len(recs)}  halves {len({r['half'] for r in recs})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
