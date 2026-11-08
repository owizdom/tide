"""Track B: capture each release's card as it stood at launch (spec 0001, section 1.2).

Input: cards/discovery.csv (one row per document found for a release).
Output: cards/manifest.csv (one row per release), bytes in ~/.tide-cache/, text in ~/.tide-cache/text/.

Source order for the bytes: a URL pinned to a commit (GitHub or Hugging Face revision), else the
earliest Wayback 200 capture fetched in raw `id_` mode (no live subresources), else the live URL,
flagged unverified.

Usage: python3 -m cards.fetch [--only RELEASE_ID ...] [--write]
"""
from __future__ import annotations

import argparse
import os
import csv
import datetime as dt
import hashlib
import html
import io
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".tide-cache"
GRACE_DAYS = 2
CARD_KINDS = {"system_card", "model_card", "tech_report", "hf_card", "github_card", "addendum"}
UA = "tide-research/0.1 (academic study of model card disclosure)"

MANIFEST_FIELDS = [
    "release_id", "doc_kind", "card_url", "source", "archive_url", "capture_ts",
    "card_date", "card_date_src", "card_days_after_launch", "card_at_launch",
    "launch_version_unverified", "digest_change_dates", "sha256", "bytes", "text_path",
    "words", "pages", "text_flag", "fetched_at", "search_log", "other_docs",
]


# ---- pure helpers (unit tested) -------------------------------------------------

def raw_url(ts: str, url: str) -> str:
    return f"https://web.archive.org/web/{ts}id_/{url}"


def earliest(caps: list[tuple[str, str]]) -> tuple[str, str]:
    return min(caps, key=lambda c: c[0])


def ts_date(ts: str) -> str:
    return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"


def days_between(a: str, b: str) -> int:
    return (dt.date.fromisoformat(b[:10]) - dt.date.fromisoformat(a[:10])).days


def launch_status(launch: str, card_date: str, capture_ts: str, date_eff: str = "") -> dict:
    """card_at_launch: the card was public by launch + GRACE (documented date first, else capture).
    launch_version_unverified: the coded bytes were captured more than GRACE days after the later
    of launch and publication, so they may be an edited version."""
    cap = ts_date(capture_ts) if capture_ts else ""
    known = [d for d in (card_date, cap, date_eff) if d]
    pub = min(known) if known else ""
    if not pub:
        return {"card_at_launch": 0, "launch_version_unverified": 1, "card_days_after_launch": ""}
    days = days_between(launch, pub)
    ref = pub if pub > launch else launch
    unverified = 0 if cap and days_between(ref, cap) <= GRACE_DAYS else 1
    return {
        "card_at_launch": 1 if days <= GRACE_DAYS else 0,
        "launch_version_unverified": unverified,
        "card_days_after_launch": days,
    }


def digest_change_dates(caps: list[tuple[str, str]]) -> list[str]:
    out, prev = [], None
    for ts, dg in sorted(caps):
        if prev is not None and dg != prev:
            out.append(ts_date(ts))
        prev = dg
    return out


KIND_RANK = {"system_card": 0, "model_card": 1, "tech_report": 2, "addendum": 3, "hf_card": 4, "github_card": 5}


def _cap(r: dict) -> str:
    s = re.sub(r"\D", "", r.get("wayback_first_200") or "")
    return s[:8] if len(s) >= 8 else "99999999"


def _d(r: dict) -> str:
    return r.get("card_date") or r.get("date_eff") or ""


def ranked_candidates(rows: list[dict], launch: str, kinds: set | None = None) -> list[dict]:
    """All cards in preference order for the version available at launch (spec 1.2):
    1. cards dated in [launch, launch + GRACE], richest kind first, then earliest;
    2. then cards dated before launch, latest first;
    3. then later cards, earliest first; undated cards (no printed date, no capture) last.
    A card's date is its printed date, or its first Wayback capture when it prints none.
    Later entries are fallbacks when an earlier one cannot be retrieved."""
    kinds = kinds or CARD_KINDS
    cards = [r for r in rows if r["doc_kind"] in kinds and r.get("card_url")]
    rank = lambda r: KIND_RANK.get(r["doc_kind"], 9)
    window = sorted((r for r in cards if _d(r) and 0 <= days_between(launch, _d(r)) <= GRACE_DAYS),
                    key=lambda r: (rank(r), _d(r), _cap(r)))
    before = sorted((r for r in cards if _d(r) and days_between(launch, _d(r)) < 0),
                    key=lambda r: (_d(r), -rank(r), [-int(c) for c in _cap(r)]), reverse=True)
    later = sorted((r for r in cards if r not in window and r not in before),
                   key=lambda r: (_d(r) or "9999", rank(r), _cap(r)))
    return window + before + later


def pick_primary(rows: list[dict], launch: str) -> dict | None:
    c = ranked_candidates(rows, launch)
    return c[0] if c else None


DATE_PAT = re.compile(
    r"(?:Date|Last updated|Published|Updated|Date of Release)\s*:?\s*"
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d\d"
    r"|20\d\d-\d\d-\d\d|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d)",
    re.I)


def printed_date(text: str) -> str:
    """A full date printed near the top of the card after a date label; empty if none."""
    m = DATE_PAT.search(text[:4000])
    if not m:
        return ""
    s = re.sub(r"\s+", " ", m.group(1))
    for fmt in ("%B %d, %Y", "%Y-%m-%d", "%d %B %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def original_from_location(loc: str) -> str:
    m = re.match(r"^(?:https?://web\.archive\.org)?/web/\d+(?:[a-z_]+)?/(.*)$", loc)
    return m.group(1) if m else loc


def decompress(data: bytes) -> bytes:
    if data[:4] == b"\x28\xb5\x2f\xfd":
        return subprocess.run(["zstd", "-dc", "-q"], input=data, capture_output=True, check=True).stdout
    if data[:2] == b"\x1f\x8b":
        import gzip
        return gzip.decompress(data)
    return data


def cache_path(sha: str, url: str) -> Path:
    low = url.lower().split("?")[0]
    ext = ".pdf" if low.endswith(".pdf") else ".md" if low.endswith(".md") else ".html"
    return CACHE / f"{sha}{ext}"


# ---- network ----------------------------------------------------------------------

def _get(url: str, tries: int = 4) -> bytes:
    import requests

    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=90)
            if r.status_code == 200:
                return r.content
            last = f"HTTP {r.status_code}"
            if r.status_code == 404:
                break
        except Exception as e:  # network errors are retried, then raised
            last = repr(e)
        time.sleep(15 * (2 ** i))  # Wayback answers bursts with 429; back off hard
    raise RuntimeError(f"{url}: {last}")


def cdx_query(url: str) -> str:
    from urllib.parse import quote

    bare = quote(re.sub(r"^https?://", "", url), safe=":/%~@!$'()*+,;=")
    return f"https://web.archive.org/cdx/search/cdx?url={bare}&output=json&fl=timestamp,statuscode,digest&limit=2000"


class CdxError(Exception):
    pass


def cdx_all(url: str) -> list[tuple[str, str, str]]:
    """All captures (timestamp, status, digest). Raises CdxError when the CDX call itself fails,
    so a Wayback outage never silently turns into a live fetch."""
    import json

    q = cdx_query(url)
    time.sleep(1)
    try:
        body = _get(q)
    except Exception as e:
        raise CdxError(f"{url}: {e}")
    rows = json.loads(body or b"[]")
    return [(r[0], r[1], r[2]) for r in rows[1:]]


def resolve_captures(url: str, depth: int = 2) -> tuple[str, list[tuple[str, str]]]:
    """200 captures for url; if it only has 3xx captures, follow the earliest redirect target."""
    import requests

    caps = cdx_all(url)
    ok = [(ts, dg) for ts, st, dg in caps if st == "200"]
    if ok or depth == 0:
        return url, ok
    redir = sorted(ts for ts, st, _ in caps if st.startswith("3"))
    for ts in redir[:3]:
        try:
            r = requests.get(raw_url(ts, url), headers={"User-Agent": UA}, timeout=60, allow_redirects=False)
        except Exception:
            continue
        loc = r.headers.get("Location", "")
        if loc:
            target = original_from_location(loc)
            if target and target != url:
                return resolve_captures(target, depth - 1)
    return url, []


def cdx(url: str) -> list[tuple[str, str]]:
    return resolve_captures(url)[1]


# ---- text extraction --------------------------------------------------------------

def extract_text(data: bytes, url: str) -> tuple[str, int]:
    if data[:5] == b"%PDF-":
        tmp = CACHE / f"tmp-{os.getpid()}.pdf"
        tmp.write_bytes(data)
        txt = subprocess.run(["pdftotext", "-layout", str(tmp), "-"], capture_output=True).stdout.decode("utf-8", "replace")
        info = subprocess.run(["pdfinfo", str(tmp)], capture_output=True).stdout.decode("utf-8", "replace")
        m = re.search(r"^Pages:\s+(\d+)", info, re.M)
        return txt, int(m.group(1)) if m else 0
    s = data.decode("utf-8", "replace")
    if url.lower().split("?")[0].endswith(".md") or "/raw/" in url or "raw.githubusercontent" in url:
        return s, 0
    s = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return html.unescape(re.sub(r"[ \t\r\f\v]+", " ", s)), 0


# ---- build ------------------------------------------------------------------------

def load_discovery(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        out.setdefault(r["release_id"], []).append(r)
    return out


def capture(release: dict, docs: list[dict]) -> dict:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log = sorted({s.strip() for d in docs for s in (d.get("search_log") or "").split(";") if s.strip()})
    row = {k: "" for k in MANIFEST_FIELDS}
    row.update(release_id=release["release_id"], fetched_at=now, search_log="; ".join(log))
    cands = ranked_candidates(docs, release["available_date"])
    if not cands:
        row["doc_kind"] = "announcement_only" if any(d["doc_kind"] == "announcement_only" for d in docs) else "none"
        row["card_at_launch"] = "0"
        return row
    failed = []
    for prim in cands:
        url = prim["card_url"]
        pinned = prim.get("pinned_url") or ""
        try:
            target, caps = (url, []) if pinned else resolve_captures(url)
            if pinned:
                data, src, cap_ts, arch = _get(pinned), "commit", (prim.get("pinned_date") or "").replace("-", ""), pinned
            elif caps:
                cap_ts, _ = earliest(caps)
                arch = raw_url(cap_ts, target)
                data, src = _get(arch), "wayback"
                row["digest_change_dates"] = " ".join(digest_change_dates(caps))
            else:
                data, src, cap_ts, arch = _get(url), "live", "", url
            break
        except CdxError:
            raise
        except Exception as e:
            failed.append(f"{url}: {str(e)[:120]}")
    else:
        raise RuntimeError("all candidates failed: " + " | ".join(failed))
    final_url = target if (not pinned and caps) else url
    others = [f"{d['doc_kind']}:{d.get('card_date','')}:{d['card_url']}" for d in cands if d is not prim]
    row.update(doc_kind=prim["doc_kind"], card_url=final_url, card_date=prim.get("card_date", ""),
               card_date_src=prim.get("card_date_src", ""), other_docs=" | ".join(others),
               text_flag=("fallback after: " + " | ".join(failed)) if failed else "")
    data = decompress(data)
    sha = hashlib.sha256(data).hexdigest()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "text").mkdir(exist_ok=True)
    cache_path(sha, final_url).write_bytes(data)
    text, pages = extract_text(data, final_url)
    tpath = CACHE / "text" / f"{sha}.txt"
    tpath.write_text(text, encoding="utf-8")
    words = len(text.split())
    pd = printed_date(text)
    if pd and pd != row["card_date"]:
        row["card_date_src"] = f"printed in coded bytes: {pd} (discovery said {row['card_date'] or 'undated'}; {row['card_date_src']})"
        row["card_date"] = pd
    elif not row["card_date"] and prim.get("date_eff"):
        row["card_date_src"] = f"undated; first Wayback capture {prim['date_eff']} is an upper bound"
    st = launch_status(release["available_date"], row["card_date"], cap_ts, prim.get("date_eff", ""))
    row.update(source=src, archive_url=arch, capture_ts=cap_ts, sha256=sha, bytes=str(len(data)),
               text_path=str(tpath), words=str(words), pages=str(pages or ""),
               text_flag=(row["text_flag"] + " low_words_per_page").strip() if pages and words / pages < 40 else row["text_flag"],
               **{k: str(v) for k, v in st.items()})
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discovery", type=Path, default=ROOT / "cards" / "discovery.csv")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    rel = list(csv.DictReader((ROOT / "releases" / "frontier.csv").open(encoding="utf-8")))
    disc = load_discovery(a.discovery)
    old = {}
    mpath = ROOT / "cards" / "manifest.csv"
    if mpath.exists():
        old = {r["release_id"]: r for r in csv.DictReader(mpath.open(encoding="utf-8"))}
    rows, errors = [], []
    for r in rel:
        rid = r["release_id"]
        if a.only and rid not in a.only and rid in old:
            rows.append(old[rid])
            continue
        try:
            rows.append(capture(r, disc.get(rid, [])))
            m = rows[-1]
            print(f"{rid:55s} {m['doc_kind']:17s} {m['source']:8s} at_launch={m['card_at_launch']} unver={m['launch_version_unverified']} words={m['words']}")
        except Exception as e:
            errors.append(f"{rid}: {e}")
            if rid in old:
                rows.append(old[rid])
    for e in errors:
        print("ERROR", e, file=sys.stderr)
    if a.write:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        mpath.write_text(buf.getvalue(), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
