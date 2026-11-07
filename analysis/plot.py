"""Track D charts in Free Systems house style (spec 0001 AT10): one command rebuilds both from the CSVs.

Usage: python3 -m analysis.plot
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "fs_kit" / "scripts"))
from fs_charts import GRAY, INK, MONO, PAPER, RED, RULE, Page  # noqa: E402

from analysis import shares  # noqa: E402

OUT = ROOT / "analysis" / "out"
HALF_LABEL = {"2023H1": "H1 23", "2023H2": "H2 23", "2024H1": "H1 24", "2024H2": "H2 24",
              "2025H1": "H1 25", "2025H2": "H2 25", "2026H1": "H1 26", "2026H2": "H2 26*"}
LAB_LABEL = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
             "xai": "xAI", "mistral": "Mistral", "deepseek": "DeepSeek"}


def cell(p, x, y, w, h, k, n):
    if n == 0:
        p.text(x + w / 2, y + h / 2 - 11, "–", 18, GRAY, MONO, anchor="middle")
        return
    s = k / n
    p.rect(x + 2, y + 2, w - 4, h - 4, RULE)
    if s > 0:
        p.ax.add_patch(__import__("matplotlib").pyplot.Rectangle(
            (x + 2, p._y(y + 2)), w - 4, h - 4, color=RED, alpha=0.12 + 0.88 * s, lw=0, zorder=3.5))
    p.text(x + w / 2, y + h / 2 - 11, f"{k}/{n}", 18, PAPER if s >= 0.5 else INK, MONO, anchor="middle")


def items_by_half(recs):
    t = shares.share_table(recs)
    halves = sorted({r["half"] for r in recs})
    any_dc = [sum(1 for r in recs if r["half"] == h and r["any_dc"]) for h in halves]
    n = [sum(1 for r in recs if r["half"] == h) for h in halves]
    title = (f"Frontier releases with dangerous-capability results at launch\n"
             f"rose from {any_dc[0]} in {n[0]} in early 2023 to {any_dc[-1]} in {n[-1]} in late 2026")
    p = Page(title, "Releases disclosing each item in the model or system card public by launch day + 2, by half-year",
             height=1270)
    x0, y0, lw, cw, rh = 64, 250, 400, 134, 50
    for j, h in enumerate(halves):
        p.text(x0 + lw + j * cw + cw / 2, y0 - 46, HALF_LABEL[h], 18, INK, MONO, anchor="middle")
    for i, (var, label) in enumerate(shares.ITEMS):
        y = y0 + i * rh + (18 if i >= 1 else 0) + (18 if i >= 7 else 0) + (18 if i >= 11 else 0)
        p.text(x0 + lw - 18, y + rh / 2 - 13, label, 21, INK, anchor="end")
        for j, h in enumerate(halves):
            row = next(r for r in t if r["item"] == var and r["half"] == h)
            cell(p, x0 + lw + j * cw, y, cw, rh, row["k"], row["n"])
    p.notes([
        "Each cell is releases disclosing the item over frontier releases in the half-year. A late card or no card counts as not disclosed. *H2 26 runs to 31 October.",
        "Frontier release: each lab's top-tier general model per new version (rule frozen before collection), 87 releases from 7 labs, from Epoch AI's database.",
        "Cards coded by two independent passes (agreement kappa 0.83 to 1.00), disagreements adjudicated. UNAUDITED DRAFT pending human verification.",
        "Source: lab model and system cards as archived at launch (Wayback Machine, Hugging Face, GitHub); Epoch AI, Data on AI models (CC BY).",
    ])
    p.save(str(OUT / "share_by_half"))


def lab_by_half(recs):
    halves = sorted({r["half"] for r in recs})
    tot = {lab: sum(1 for r in recs if r["lab"] == lab and r["any_dc"]) for lab in shares.LABS}
    all_dc = sum(tot.values())
    top2 = sorted(tot, key=tot.get, reverse=True)[:2]
    title = (f"{LAB_LABEL[top2[0]]} and {LAB_LABEL[top2[1]]} account for {tot[top2[0]] + tot[top2[1]]} of the {all_dc}"
             f" releases\nthat reported dangerous-capability results at launch")
    p = Page(title, "Releases with at least one bio, chem, nuclear, cyber, autonomy, persuasion or deception result at launch",
             height=820)
    x0, y0, lw, cw, rh = 64, 250, 250, 136, 56
    for j, h in enumerate(halves):
        p.text(x0 + lw + j * cw + cw / 2, y0 - 46, HALF_LABEL[h], 18, INK, MONO, anchor="middle")
    p.text(x0 + lw + len(halves) * cw + 70, y0 - 46, "ALL", 18, INK, MONO, anchor="middle")
    for i, lab in enumerate(shares.LABS):
        y = y0 + i * rh
        p.text(x0 + lw - 18, y + rh / 2 - 13, LAB_LABEL[lab], 22, INK, anchor="end")
        for j, h in enumerate(halves):
            g = [r for r in recs if r["lab"] == lab and r["half"] == h]
            cell(p, x0 + lw + j * cw, y, cw, rh, sum(1 for r in g if r["any_dc"]), len(g))
        n = sum(1 for r in recs if r["lab"] == lab)
        p.text(x0 + lw + len(halves) * cw + 70, y + rh / 2 - 11, f"{tot[lab]}/{n}", 18, INK, MONO, anchor="middle")
    p.notes([
        "Each cell is releases with a dangerous-capability result in the card public by launch day + 2, over that lab's frontier releases in the half-year. – means no release. *H2 26 runs to 31 October.",
        "UNAUDITED DRAFT pending human verification of a sample of codes.",
        "Source: lab model and system cards as archived at launch; Epoch AI, Data on AI models (CC BY).",
    ])
    p.save(str(OUT / "lab_by_half_any_dc"))


def main() -> int:
    recs = shares.load()
    items_by_half(recs)
    lab_by_half(recs)
    print("wrote", OUT / "share_by_half.png", OUT / "lab_by_half_any_dc.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
