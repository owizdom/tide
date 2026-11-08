"""Capture every other developer document about a release that was public by launch + 2 days
(codebook v1.2 clarification 5), with the same provenance rules as the primary card.

Output: cards/secondary.csv, one row per extra document; dup_of marks a copy of the primary
(same bytes, or the same text at 90% shingle overlap), which is not coded again.

Usage: python3 -m cards.secondary [--write]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import re
import sys
from pathlib import Path

from cards import fetch

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["release_id", "doc_kind", "card_url", "source", "archive_url", "capture_ts", "card_date",
          "sha256", "text_path", "words", "pages", "dup_of", "fetched_at", "error"]


def shingles(text: str, k: int = 5) -> set:
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def overlap(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


def in_window(d: dict, launch: str) -> bool:
    date = d.get("card_date") or d.get("date_eff")
    return bool(date) and fetch.days_between(launch, date) <= fetch.GRACE_DAYS


def capture_one(d: dict) -> dict:
    url, pinned = d["card_url"], d.get("pinned_url") or ""
    if pinned:
        data, src, cap, arch = fetch._get(pinned), "commit", (d.get("pinned_date") or "").replace("-", ""), pinned
        final = url
    else:
        target, caps = fetch.resolve_captures(url)
        if caps:
            cap, _ = fetch.earliest(caps)
            arch = fetch.raw_url(cap, target)
            data, src, final = fetch._get(arch), "wayback", target
        else:
            data, src, cap, arch, final = fetch._get(url), "live", "", url, url
    data = fetch.decompress(data)
    sha = hashlib.sha256(data).hexdigest()
    fetch.cache_path(sha, final).write_bytes(data)
    text, pages = fetch.extract_text(data, final)
    tp = fetch.CACHE / "text" / f"{sha}.txt"
    tp.write_text(text, encoding="utf-8")
    return {"doc_kind": d["doc_kind"], "card_url": final, "source": src, "archive_url": arch, "capture_ts": cap,
            "card_date": d.get("card_date") or d.get("date_eff", ""), "sha256": sha, "text_path": str(tp),
            "words": str(len(text.split())), "pages": str(pages or "")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    rel = {r["release_id"]: r for r in csv.DictReader((ROOT / "releases" / "frontier.csv").open())}
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    disc = fetch.load_discovery(ROOT / "cards" / "discovery.csv")
    rows = []
    for rid, docs in disc.items():
        m = man[rid]
        if not m["sha256"]:
            continue
        launch = rel[rid]["available_date"]
        primary_text = Path(m["text_path"]).read_text(encoding="utf-8", errors="replace")
        seen = {m["card_url"]}
        for d in fetch.ranked_candidates(docs, launch):
            if d["card_url"] in seen or not in_window(d, launch):
                continue
            seen.add(d["card_url"])
            now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            row = {k: "" for k in FIELDS}
            row.update(release_id=rid, doc_kind=d["doc_kind"], card_url=d["card_url"], fetched_at=now)
            try:
                row.update(capture_one(d))
                if row["sha256"] == m["sha256"]:
                    row["dup_of"] = "primary:same-bytes"
                else:
                    ov = overlap(Path(row["text_path"]).read_text(encoding="utf-8", errors="replace"), primary_text)
                    if ov >= 0.9:
                        row["dup_of"] = f"primary:text-overlap-{ov:.2f}"
                    else:
                        for prev in rows:
                            if prev["release_id"] == rid and prev["sha256"] == row["sha256"]:
                                row["dup_of"] = "secondary:same-bytes"
            except Exception as e:
                row["error"] = str(e)[:200]
            rows.append(row)
            print(f"{rid:50s} {row['doc_kind']:12s} {row['source']:8s} words={row['words']:>6s} dup={row['dup_of'] or '-'} {row['error'][:60]}")
    if a.write:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        (ROOT / "cards" / "secondary.csv").write_text(buf.getvalue(), encoding="utf-8")
    return 1 if any(r["error"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
