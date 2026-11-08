"""Merge the scouts' raw discovery CSVs into cards/discovery.csv (Track B).

Normalises card dates to YYYY-MM-DD (empty when the document is undated), derives the
searched-source tags only from what each scout wrote, and pins Hugging Face and GitHub cards
to the commit the scout identified.

Usage: python3 -m cards.merge
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "cards" / "discovery" / "raw"
OUT = ROOT / "cards" / "discovery.csv"
FIELDS = ["release_id", "doc_kind", "card_url", "card_date", "date_eff", "card_date_src", "wayback_first_200",
          "announcement_url", "status", "search_log", "notes", "pinned_url", "pinned_date", "scout_file"]
ISO = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")
SHA = re.compile(r"\b([0-9a-f]{40})\b")
LAB_HOSTS = ("anthropic.com", "openai.com", "x.ai", "mistral.ai", "deepseek.com", "deepmind", "blog.google",
             "ai.meta.com", "meta.ai", "llama.com", "grok.com", "docs.")


def norm_date(s: str) -> str:
    s = (s or "").strip()
    if re.match(r"^(undated|not printed|no )", s, re.I):
        return ""
    m = ISO.search(s)
    return m.group(1) if m and s.startswith(m.group(1)) else ""


NEG = re.compile(r"not run|not fetched|not searched|not queried|not checked|not attempted|on sibling|not retried", re.I)


def search_tokens(log: str, announcement: str = "") -> set[str]:
    """Award a source only from a clause that reports it was searched, never from a clause that
    says it was not run (spec AT3)."""
    toks = set()
    for clause in re.split(r"[;\n]", log or ""):
        low = clause.lower()
        if not low.strip():
            continue
        neg = bool(NEG.search(low))
        def give(tok, hit):
            if hit and not neg:
                toks.add(tok)
        give("lab", any(h in low for h in LAB_HOSTS) or "lab site" in low or "epoch link" in low or "announcement" in low)
        give("announcement", "announcement" in low or "blog" in low or "post" in low)
        give("hf", bool(re.search(r"\bhf\b|hugging", low)))
        give("github", "github" in low)
        give("arxiv", "arxiv" in low)
        give("wayback", "wayback" in low or "cdx" in low)
    if announcement:
        toks.add("announcement")
    return toks


def canonical_url(url: str) -> str:
    m = re.match(r"^https?://arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?$", url or "")
    if m:
        return f"https://arxiv.org/pdf/{m.group(1)}v1"
    return re.sub(r"(huggingface\.co/[^/]+/[^/]+)/blob/", r"\1/resolve/", url or "")


def capture_date(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"^(20\d\d)(\d\d)(\d\d)\d{0,6}$", s) or re.match(r"^(20\d\d)-(\d\d)-(\d\d)", s)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def pin(r: dict) -> tuple[str, str]:
    url, src = r.get("card_url", ""), r.get("card_date_src", "")
    if url.startswith("https://arxiv.org/pdf/") and url.endswith("v1"):
        return url, norm_date(r.get("card_date", ""))
    if re.search(r"huggingface\.co/[^/]+/[^/]+/resolve/[0-9a-f]{40}/", url):
        m = re.search(r"committed (20\d\d-\d\d-\d\d)", src)
        return url, (m.group(1) if m else norm_date(r.get("card_date", "")))
    if "raw.githubusercontent.com" in url and SHA.search(url):
        m = re.search(r"committed (20\d\d-\d\d-\d\d)", src)
        return url, (m.group(1) if m else norm_date(r.get("card_date", "")))
    hf = re.match(r"^https://huggingface\.co/([^/]+/[^/]+)/?$", url)
    m = re.search(r"HF commit ([0-9a-f]{40}).*?(20\d\d-\d\d-\d\d)", src)
    if hf and m:
        return f"https://huggingface.co/{hf.group(1)}/raw/{m.group(1)}/README.md", m.group(2)
    if re.search(r"/(?:raw|resolve|blob)/[0-9a-f]{40}/|githubusercontent\.com/[^/]+/[^/]+/[0-9a-f]{40}/", url):
        return url, norm_date(r.get("card_date", ""))
    return "", ""


def load_overrides() -> list[dict]:
    p = ROOT / "cards" / "discovery" / "overrides.csv"
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def main() -> int:
    rows = []
    ovs = load_overrides()
    for f in sorted(RAW.glob("*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            r = {k: (v or "") for k, v in r.items()}
            for o in ovs:
                field = o.get("match_field") or "card_url"
                if o["release_id"] == r["release_id"] and o["match"] and o["match"] in r.get(field, ""):
                    r[o["field"]] = o["value"]
                    r["notes"] = (r.get("notes", "") + f" [override: {o['field']}={o['value']}: {o['reason']}]").strip()
            r["card_url"] = canonical_url(r["card_url"])
            r["card_date"] = norm_date(r["card_date"])
            r["date_eff"] = r["card_date"] or capture_date(r.get("wayback_first_200", ""))
            r["pinned_url"], r["pinned_date"] = pin(r)
            r["search_log"] = "; ".join(sorted(search_tokens(r["search_log"], r["announcement_url"])))
            r["scout_file"] = f.name
            rows.append({k: r.get(k, "") for k in FIELDS})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    OUT.write_text(buf.getvalue(), encoding="utf-8")
    print(f"{len(rows)} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
