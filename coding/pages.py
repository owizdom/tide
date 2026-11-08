"""Render the pages coders must look at (codebook v1.2 clarification 4): for every release with an
item below its top level, every page of every launch document that holds an image, plus every page
whose text mentions an open item (tables that garble in the text layer). Images in web and markdown
cards are fetched too.

Output: coding/pages_manifest.csv (release_id, doc_sha, page, png, reason) and PNGs under
~/.tide-cache/pages/.

Usage: python3 -m coding.pages
"""
from __future__ import annotations

import csv
import io
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin

from cards import fetch
from coding import check

ROOT = Path(__file__).resolve().parents[1]
PAGES = fetch.CACHE / "pages"
DPI = "90"


def open_items(code_row: dict) -> list[str]:
    return [v for v in check.VARIABLES if int(code_row[v]) < (2 if v in check.THREE_LEVEL else 1)]


def docs_for(rid: str, man: dict, sec: list[dict]) -> list[dict]:
    out = [{"sha": man[rid]["sha256"], "url": man[rid]["card_url"], "text": man[rid]["text_path"]}]
    out += [{"sha": s["sha256"], "url": s["card_url"], "text": s["text_path"]}
            for s in sec if s["release_id"] == rid and s["sha256"] and not s["dup_of"]]
    return out


def pdf_pages(path: Path, text_path: str, items: list[str]) -> list[tuple[int, str]]:
    out = subprocess.run(["pdfimages", "-list", str(path)], capture_output=True, text=True).stdout.splitlines()[2:]
    img = {int(l.split()[0]) for l in out
           if len(l.split()) > 4 and l.split()[2] == "image" and int(l.split()[3]) >= 150 and int(l.split()[4]) >= 100}
    pages = Path(text_path).read_text(encoding="utf-8", errors="replace").split("\f")
    pat = "|".join(check.KEYWORDS[v] for v in items)
    kw = {i + 1 for i, pg in enumerate(pages) if re.search(pat, pg, re.I)}
    return [(p, "image" if p in img else "keyword") for p in sorted(img | kw)]


def web_images(path: Path, base: str) -> list[str]:
    s = path.read_bytes().decode("utf-8", "replace")
    srcs = re.findall(r'<img[^>]+src="([^"]+)"', s) + re.findall(r"!\[[^\]]*\]\(([^)\s]+)", s)
    srcs = [x for x in srcs if not re.search(r"\.svg|logo|icon|avatar|favicon|badge|shields\.io|data:", x, re.I)]
    out = []
    for x in srcs:
        u = urljoin(base, x)
        if "huggingface.co" in u:
            u = u.replace("/blob/", "/resolve/")
        if "github.com" in u and "/blob/" in u:
            u = u.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        out.append(u)
    return list(dict.fromkeys(out))


def main() -> int:
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    codes = {r["release_id"]: r for r in csv.DictReader((ROOT / "coding" / "codes.csv").open())}
    secp = ROOT / "cards" / "secondary.csv"
    sec = list(csv.DictReader(secp.open())) if secp.exists() else []
    rows, errors = [], []
    for rid, m in man.items():
        if not m["sha256"]:
            continue
        items = open_items(codes[rid])
        if not items:
            continue
        for d in docs_for(rid, man, sec):
            f = next(fetch.CACHE.glob(d["sha"] + ".*"))
            outdir = PAGES / d["sha"]
            outdir.mkdir(parents=True, exist_ok=True)
            if f.read_bytes()[:5] == b"%PDF-":
                for p, why in pdf_pages(f, d["text"], items):
                    png = outdir / f"p{p:04d}.png"
                    if not png.exists():
                        subprocess.run(["pdftoppm", "-r", DPI, "-png", "-singlefile", "-f", str(p), "-l", str(p),
                                        str(f), str(png)[:-4]], check=True)
                    rows.append({"release_id": rid, "doc_sha": d["sha"], "page": p, "png": str(png), "reason": why})
            else:
                for i, u in enumerate(web_images(f, d["url"]), 1):
                    png = outdir / f"img{i:03d}{Path(u.split('?')[0]).suffix or '.png'}"
                    try:
                        if not png.exists():
                            png.write_bytes(fetch._get(u))
                        rows.append({"release_id": rid, "doc_sha": d["sha"], "page": f"img{i}", "png": str(png), "reason": "web image " + u[:120]})
                    except Exception as e:
                        errors.append(f"{rid} {u}: {e}")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["release_id", "doc_sha", "page", "png", "reason"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (ROOT / "coding" / "pages_manifest.csv").write_text(buf.getvalue(), encoding="utf-8")
    print(f"pages {len(rows)} releases {len({r['release_id'] for r in rows})} errors {len(errors)}")
    for e in errors:
        print("ERROR", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
