"""Merge passes A and B into coding/codes.csv (spec 0001 seam) and list disagreements.

Agreed values are final. Disagreements go to coding/disagreements.csv for adjudication; an
adjudicated value in coding/adjudication.csv (release_id, variable, value, quote, reason) wins.
Releases with no card get every item 0 and no_card=1.

Usage: python3 -m coding.merge
"""
import csv
import io
from pathlib import Path

from coding import check

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rel = list(csv.DictReader((ROOT / "releases" / "frontier.csv").open()))
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    a = check.load_pass(ROOT / "coding" / "passes" / "A")
    b = check.load_pass(ROOT / "coding" / "passes" / "B")
    adj = {}
    p = ROOT / "coding" / "adjudication.csv"
    if p.exists():
        for r in csv.DictReader(p.open()):
            adj[(r["release_id"], r["variable"])] = r
    rows, dis, missing = [], [], []
    for r in rel:
        rid = r["release_id"]
        out = {"release_id": rid, "lab": r["lab"], "available_date": r["available_date"],
               "no_card": 0 if man[rid]["sha256"] else 1}
        for v in check.VARIABLES:
            if out["no_card"]:
                out[v] = 0
                continue
            if rid not in a or rid not in b:
                missing.append(rid)
                out[v] = ""
                continue
            va, vb = a[rid]["codes"][v]["value"], b[rid]["codes"][v]["value"]
            if (rid, v) in adj:
                out[v] = int(adj[(rid, v)]["value"])
            elif va == vb:
                out[v] = va
            else:
                out[v] = ""
                dis.append({"release_id": rid, "variable": v, "A": va, "B": vb,
                            "quote_A": a[rid]["codes"][v].get("quote", ""), "note_A": a[rid]["codes"][v].get("note", ""),
                            "quote_B": b[rid]["codes"][v].get("quote", ""), "note_B": b[rid]["codes"][v].get("note", "")})
        rows.append(out)

    def write(path, recs, fields):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(recs)
        path.write_text(buf.getvalue(), encoding="utf-8")

    write(ROOT / "coding" / "codes_v11.csv", rows, ["release_id", "lab", "available_date", "no_card"] + check.VARIABLES)
    write(ROOT / "coding" / "disagreements.csv", dis,
          ["release_id", "variable", "A", "B", "quote_A", "note_A", "quote_B", "note_B"])
    print(f"releases {len(rows)}  disagreements {len(dis)}  missing passes {len(set(missing))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
