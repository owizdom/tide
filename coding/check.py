"""Track C checks (spec 0001 AT6-AT8).

A coding pass writes one JSON file per release to coding/passes/<pass>/<release_id>.json:
  {"release_id": ..., "codes": {<variable>: {"value": int, "quote": str, "locator": str, "note": str}}}
Every value above 0 needs a quote that appears verbatim (after normalisation) in the coded card text.

Usage: python3 -m coding.check [--agreement A B]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THREE_LEVEL = ["dc_eval_cbrn", "dc_eval_cyber", "dc_eval_autonomy", "dc_eval_persuasion", "dc_eval_scheming",
               "framework_threshold"]
BINARY = ["ext_test_any", "ext_test_named_org", "ext_test_government", "ext_test_timing_stated",
          "safeguards_training", "safeguards_runtime", "safeguards_access", "safeguards_weights"]
VARIABLES = THREE_LEVEL + BINARY

KEYWORDS = {
    "dc_eval_cbrn": r"biolog|bioweapon|chemical weapon|cbrn|radiolog|nuclear|virolog|pathogen",
    "dc_eval_cyber": r"cyber|\bctf\b|capture the flag|exploit|vulnerabilit|offensive security",
    "dc_eval_autonomy": r"autonom|self-replicat|ai r&d|research and development|self-improv|\bara\b",
    "dc_eval_persuasion": r"persuas|manipulat|influence operation",
    "dc_eval_scheming": r"decept|sabotage|sandbag|scheming|alignment faking|evaluation awareness|exfiltrat|reward hack",
    "ext_test_any": r"external|third-party|third party|red team",
    "ext_test_named_org": r"\bmetr\b|apollo|external|third-party|third party",
    "ext_test_government": r"\baisi\b|\bcaisi\b|safety institute|government",
    "ext_test_timing_stated": r"pre-deployment|predeployment|prior to (?:release|deployment|launch)|before (?:release|deployment|launch)",
    "framework_threshold": r"responsible scaling|preparedness framework|frontier safety framework|frontier ai framework|risk management framework|asl-|critical capability level|\bccl",
    "safeguards_training": r"refus|safety training|rlhf|harmless|constitution",
    "safeguards_runtime": r"classifier|filter|moderation|monitor",
    "safeguards_access": r"trusted access|kyc|staged|rollout|access",
    "safeguards_weights": r"weight security|model weights|security of",
}


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("­", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"-\s*\n\s*", "", s)  # hyphenated line breaks
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def quote_found(quote: str, text: str) -> bool:
    q = norm(quote)
    return bool(q) and q in norm(text)


def keyword_hits(text: str) -> dict[str, bool]:
    low = text.lower()
    return {v: bool(re.search(p, low)) for v, p in KEYWORDS.items()}


def kappa(a: list[int], b: list[int]) -> float:
    """Cohen's kappa for two coders over the same items."""
    n = len(a)
    assert n == len(b) and n > 0
    po = sum(x == y for x, y in zip(a, b)) / n
    cats = sorted(set(a) | set(b))
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


def validate(rec: dict) -> list[str]:
    probs = []
    rid = rec.get("release_id", "?")
    codes = rec.get("codes", {})
    for v in VARIABLES:
        c = codes.get(v)
        if c is None:
            probs.append(f"{rid}: missing {v}")
            continue
        allowed = {0, 1, 2} if v in THREE_LEVEL else {0, 1}
        if c.get("value") not in allowed:
            probs.append(f"{rid}: {v} value {c.get('value')!r} not in {sorted(allowed)}")
        elif c["value"] > 0 and not (c.get("quote") or "").strip():
            probs.append(f"{rid}: {v}={c['value']} without a quote")
    return probs


def manifest() -> dict[str, dict]:
    return {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open(encoding="utf-8"))}


def load_pass(d: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))}


def verify_all(passes_dir: Path) -> list[str]:
    """AT6 over every pass on disk; AT7 notes are reported by zero_screen()."""
    probs = []
    if not passes_dir.exists():
        return probs
    man = manifest()
    for d in sorted(p for p in passes_dir.iterdir() if p.is_dir()):
        for rid, rec in load_pass(d).items():
            probs += [f"[{d.name}] {p}" for p in validate(rec)]
            m = man.get(rid)
            if m is None or not m["text_path"]:
                probs.append(f"[{d.name}] {rid}: no coded card text in manifest")
                continue
            text = Path(m["text_path"]).read_text(encoding="utf-8", errors="replace")
            for v, c in rec.get("codes", {}).items():
                if c.get("value", 0) > 0 and not quote_found(c.get("quote", ""), text):
                    probs.append(f"[{d.name}] {rid}: {v} quote not found: {c.get('quote','')[:80]!r}")
    return probs


def zero_screen(pass_dir: Path) -> list[str]:
    """AT7: zeros whose keywords occur in the text and that carry no note."""
    out = []
    man = manifest()
    for rid, rec in load_pass(pass_dir).items():
        text = Path(man[rid]["text_path"]).read_text(encoding="utf-8", errors="replace")
        hits = keyword_hits(text)
        for v, c in rec["codes"].items():
            if c["value"] == 0 and hits.get(v) and not (c.get("note") or "").strip():
                out.append(f"{rid}: {v}=0 but keywords present and no note")
    return out


def agreement(a_dir: Path, b_dir: Path) -> dict[str, tuple[float, int]]:
    a, b = load_pass(a_dir), load_pass(b_dir)
    common = sorted(set(a) & set(b))
    res = {}
    for v in VARIABLES:
        xa = [a[r]["codes"][v]["value"] for r in common]
        xb = [b[r]["codes"][v]["value"] for r in common]
        res[v] = (round(kappa(xa, xb), 3), sum(x != y for x, y in zip(xa, xb)))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agreement", nargs=2)
    a = ap.parse_args(argv)
    probs = verify_all(ROOT / "coding" / "passes")
    for p in probs:
        print("AT6", p)
    for d in sorted((ROOT / "coding" / "passes").glob("*")):
        for z in zero_screen(d):
            print(f"AT7 [{d.name}]", z)
    if a.agreement:
        for v, (k, dis) in agreement(*(ROOT / "coding" / "passes" / x for x in a.agreement)).items():
            print(f"{v:22s} kappa {k:6.3f}  disagreements {dis}")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
