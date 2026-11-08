"""Supplement pass (codebook v1.2): work files, checks, and merge into coding/codes.csv.

  python3 -m coding.supplement --plan N        write N balanced work files to coding/supplement/work/
  python3 -m coding.supplement --check A|B     validate a coder's files (schema, quotes, coverage)
  python3 -m coding.supplement --merge         final = max(current code, agreed supplement value);
                                               A/B disagreements -> coding/supplement/disagreements.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from coding import check
from coding.pages import open_items

ROOT = Path(__file__).resolve().parents[1]
SUP = ROOT / "coding" / "supplement"


def load_ctx():
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    base = {r["release_id"]: r for r in csv.DictReader((ROOT / "coding" / "codes_v11.csv").open())}
    secp = ROOT / "cards" / "secondary.csv"
    sec = list(csv.DictReader(secp.open())) if secp.exists() else []
    pages = list(csv.DictReader((ROOT / "coding" / "pages_manifest.csv").open()))
    return man, base, sec, pages


def texts_for(rid, man, sec):
    t = {man[rid]["sha256"]: man[rid]["text_path"]}
    for s in sec:
        if s["release_id"] == rid and s["sha256"]:
            t[s["sha256"]] = s["text_path"]
    return t


def plan(n: int) -> None:
    man, base, sec, pages = load_ctx()
    rel = [rid for rid in man if man[rid]["sha256"] and open_items(base[rid])]
    load = []
    for rid in rel:
        np_ = sum(1 for p in pages if p["release_id"] == rid)
        nw = sum(int(s["words"] or 0) for s in sec if s["release_id"] == rid and s["sha256"] and not s["dup_of"])
        load.append((np_ * 600 + nw, rid))
    load.sort(reverse=True)
    bins = [[] for _ in range(n)]
    w = [0] * n
    for c, rid in load:
        i = w.index(min(w))
        bins[i].append(rid)
        w[i] += c
    (SUP / "work").mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(bins, 1):
        lines = []
        for rid in b:
            cur = base[rid]
            lines.append(f"## {rid}")
            lines.append("open items: " + ", ".join(f"{v}={cur[v]}" for v in open_items(cur)))
            lines.append(f"primary card text (already coded; use it to read figure captions): {man[rid]['text_path']}")
            for s in sec:
                if s["release_id"] == rid and s["sha256"] and not s["dup_of"]:
                    lines.append(f"extra document to read in full: sha {s['sha256']} text {s['text_path']} ({s['doc_kind']}, {s['card_url']})")
            for p in pages:
                if p["release_id"] == rid:
                    lines.append(f"page image: doc {p['doc_sha']} page {p['page']} {p['png']} ({p['reason'][:40]})")
            lines.append("")
        (SUP / "work" / f"w{i:02d}.txt").write_text("\n".join(lines), encoding="utf-8")
    print("work files", n, "loads", w)


def check_coder(letter: str) -> list[str]:
    man, base, sec, pages = load_ctx()
    probs = []
    d = SUP / letter
    for f in sorted(d.glob("*.json")):
        rec = json.loads(f.read_text())
        rid = rec.get("release_id", f.stem)
        if rid not in base:
            probs.append(f"{rid}: unknown release")
            continue
        want = set(open_items(base[rid]))
        got = set(rec.get("items", {}))
        if want - got:
            probs.append(f"{rid}: missing items {sorted(want - got)}")
        texts = texts_for(rid, man, sec)
        for v, c in rec.get("items", {}).items():
            cur = int(base[rid][v])
            top = 2 if v in check.THREE_LEVEL else 1
            val = c.get("value")
            if not isinstance(val, int) or val < cur or val > top:
                probs.append(f"{rid}: {v} value {val!r} outside [{cur}, {top}]")
                continue
            src = c.get("source")
            if val > cur:
                if src not in ("text", "figure"):
                    probs.append(f"{rid}: {v} raised without text or figure source")
                    continue
                tp = texts.get(c.get("doc_sha", ""))
                if not tp:
                    probs.append(f"{rid}: {v} doc_sha not a launch document of this release")
                    continue
                text = Path(tp).read_text(encoding="utf-8", errors="replace")
                if src == "text" and not check.quote_found(c.get("quote", ""), text):
                    probs.append(f"{rid}: {v} text quote not found")
                if src == "figure":
                    if not c.get("page") or not c.get("description"):
                        probs.append(f"{rid}: {v} figure needs page and description")
                    elif not str(c["page"]).startswith("img") and not check.quote_found(c.get("quote", ""), text):
                        probs.append(f"{rid}: {v} figure label quote not found in the document text layer")
    return probs


def merge() -> None:
    man, base, sec, pages = load_ctx()
    a = {f.stem: json.loads(f.read_text()) for f in (SUP / "A").glob("*.json")}
    b = {f.stem: json.loads(f.read_text()) for f in (SUP / "B").glob("*.json")}
    adjp = SUP / "adjudication.csv"
    adj = {(r["release_id"], r["variable"]): r for r in csv.DictReader(adjp.open())} if adjp.exists() else {}
    out, dis, raised = [], [], []
    for rid, row in base.items():
        new = dict(row)
        for v in open_items(row) if row["no_card"] == "0" else []:
            if rid not in a or rid not in b:
                raise SystemExit(f"supplement missing for {rid}")
            va, vb = a[rid]["items"][v]["value"], b[rid]["items"][v]["value"]
            if (rid, v) in adj:
                final = int(adj[(rid, v)]["value"])
            elif va == vb:
                final = va
            else:
                dis.append({"release_id": rid, "variable": v, "current": row[v], "A": va, "B": vb,
                            "A_evidence": json.dumps(a[rid]["items"][v])[:600], "B_evidence": json.dumps(b[rid]["items"][v])[:600]})
                final = int(row[v])
            if final > int(row[v]):
                raised.append((rid, v, row[v], final))
            new[v] = final
        out.append(new)
    fields = list(next(iter(base.values())).keys())
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    (ROOT / "coding" / "codes.csv").write_text(buf.getvalue(), encoding="utf-8")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["release_id", "variable", "current", "A", "B", "A_evidence", "B_evidence"], lineterminator="\n")
    w.writeheader()
    w.writerows(dis)
    (SUP / "disagreements.csv").write_text(buf.getvalue(), encoding="utf-8")
    print(f"raised {len(raised)}  disagreements {len(dis)}")
    for r in raised:
        print("  raised", *r)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=int)
    ap.add_argument("--check")
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args(argv)
    if a.plan:
        plan(a.plan)
    if a.check:
        p = check_coder(a.check)
        for x in p:
            print(x)
        return 1 if p else 0
    if a.merge:
        merge()
    return 0


if __name__ == "__main__":
    sys.exit(main())
