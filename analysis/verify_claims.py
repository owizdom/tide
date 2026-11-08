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
        (f"Agreement across {len(a) * len(check.VARIABLES):,} codes", True),
        (f"between {min(kap):.2f} and {max(kap):.2f} for every item", True),
        (f"The {adj} disagreements", True),
        (f"Half-years hold {min(len(v) for v in by.values())} to {max(len(v) for v in by.values())} releases", True),
    ]
    lead = {"anthropic": "Anthropic reported dangerous-capability results at launch for {} of {}",
            "openai": "OpenAI for {} of {}", "google": "Google did so for {} of {}", "meta": "Meta for {} of {}",
            "xai": "xAI for {} of {}", "deepseek": "DeepSeek for {} of {}", "mistral": "Mistral for {} of {}"}
    for l, g in lab.items():
        out.append((lead[l].format(sum(r["any_dc"] for r in g), len(g)), True))
    d = {(x["from"], x["to"]): x for x in shares.drops(recs)}
    mus = d[("Muse Spark 1.1", "Muse Spark 1.2")]
    gpt41 = d[("GPT-4.5", "GPT-4.1")]
    turbo = d[("GPT-4 (Mar 2023)", "GPT-4 Turbo (Nov 2023)")]
    top3 = [(x["from"], x["to"]) for x in shares.drops(recs)[:3]]
    out += [
        (f"so all {mus['n_lost']} dropped", top3[0] == ("Muse Spark 1.1", "Muse Spark 1.2")),
        (f"no card has appeared since. {gpt41['n_lost']} of the 14 items dropped", top3[1] == ("GPT-4.5", "GPT-4.1")),
        (f"announcement and no card. {turbo['n_lost']} of the 14 items dropped", top3[2] == ("GPT-4 (Mar 2023)", "GPT-4 Turbo (Nov 2023)")),
        (f"got its evaluation report {[x for x in man if x['release_id'] == 'meta-2026-09-02-muse-spark-1-3'][0]['card_days_after_launch']} days after launch", True),
        (f"every one of the {len(a)} cards", True),
    ]
    import json, glob
    sec = [r for r in csv.DictReader((ROOT / "cards" / "secondary.csv").open()) if r["sha256"] and not r["dup_of"]]
    pm = list(csv.DictReader((ROOT / "coding" / "pages_manifest.csv").open()))
    SA = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(ROOT / "coding" / "supplement" / "A" / "*.json"))}
    SB = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(ROOT / "coding" / "supplement" / "B" / "*.json"))}
    xa = [SA[k]["items"][v]["value"] for k in SA for v in SA[k]["items"]]
    xb = [SB[k]["items"][v]["value"] for k in SA for v in SA[k]["items"]]
    base = {r["release_id"]: r for r in csv.DictReader((ROOT / "coding" / "codes_v11.csv").open())}
    final = {r["release_id"]: r for r in csv.DictReader((ROOT / "coding" / "codes.csv").open())}
    raised = sum(1 for rid in final for v in check.VARIABLES if final[rid][v] != base[rid][v])
    disc = sum(1 for r in csv.DictReader((ROOT / "cards" / "discovery.csv").open()) if r["card_url"])
    unv = [r for r in man if r["sha256"] and r["launch_version_unverified"] == "1"]
    out += [
        (f"read {len(sec)} extra launch documents across {len({r['release_id'] for r in sec})} releases", True),
        (f"looked at {len(pm):,} rendered pages", True),
        (f"Across {len(xa)} item codes the two passes disagreed twice (kappa {check.kappa(xa, xb):.3f})", sum(x != y for x, y in zip(xa, xb)) == 2),
        (f"{['Zero','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten'][raised]} codes rose", True),
        (f"found {disc} candidate documents", True),
        (f"{['zero','one','two','three','four'][len(unv)].capitalize()} late cards were first archived after the date printed on them", all(r["card_at_launch"] == "0" for r in unv)),
    ]
    bad = [c for c, must in out if not must]
    assert not bad, f"case ranking changed: {bad}"
    return [c for c, _ in out]


def main() -> int:
    text = (ROOT / "docs" / "methods.md").read_text(encoding="utf-8")
    missing = [c for c in claims() if c not in text]
    for c in missing:
        print("NOT IN methods.md or WRONG:", c)
    print(f"{len(claims()) - len(missing)} of {len(claims())} claims match the data")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
