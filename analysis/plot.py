"""Track D charts in Free Systems house style (spec 0001 AT10): one command rebuilds both from the CSVs.

Usage: python3 -m analysis.plot
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "fs_kit" / "scripts"))
from fs_charts import GRAY, INK, MONO, PAPER, RED, RULE, Page, mono_ticks  # noqa: E402
from fs_extras import bars, pct  # noqa: E402

from analysis import shares  # noqa: E402

OUT = ROOT / "analysis" / "out"
HALF_LABEL = {"2023H1": "H1 23", "2023H2": "H2 23", "2024H1": "H1 24", "2024H2": "H2 24",
              "2025H1": "H1 25", "2025H2": "H2 25", "2026H1": "H1 26", "2026H2": "H2 26*"}
LAB_LABEL = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
             "xai": "xAI", "mistral": "Mistral", "deepseek": "DeepSeek"}


def cell(p, x, y, w, h, k, n, show_n=False):
    if n == 0:
        p.text(x + w / 2, y + h / 2 - 11, "–", 18, GRAY, MONO, anchor="middle")
        return
    s = k / n
    p.rect(x + 2, y + 2, w - 4, h - 4, RULE)
    if s > 0:
        p.ax.add_patch(__import__("matplotlib").pyplot.Rectangle(
            (x + 2, p._y(y + 2)), w - 4, h - 4, color=RED, alpha=0.12 + 0.88 * s, lw=0, zorder=3.5))
    col = PAPER if s >= 0.5 else INK
    if show_n:
        p.text(x + w / 2, y + h / 2 - 19, f"{round(100 * s)}%", 19, col, MONO, anchor="middle")
        p.text(x + w / 2, y + h / 2 + 3, f"{n} release{'s' if n != 1 else ''}", 13, col, MONO, anchor="middle")
    else:
        p.text(x + w / 2, y + h / 2 - 11, f"{round(100 * s)}%", 19, col, MONO, anchor="middle")


def items_by_half(recs):
    t = shares.share_table(recs)
    halves = sorted({r["half"] for r in recs})
    any_dc = [sum(1 for r in recs if r["half"] == h and r["any_dc"]) for h in halves]
    n = [sum(1 for r in recs if r["half"] == h) for h in halves]
    title = (f"Frontier releases with dangerous-capability results at launch\n"
             f"rose from {round(100 * any_dc[0] / n[0])}% in early 2023 to {round(100 * any_dc[-1] / n[-1])}% in late 2026")
    p = Page(title, "Percent of frontier AI releases whose model or system card, public at launch, discloses each item",
             height=1290)
    x0, y0, lw, cw, rh = 64, 270, 400, 134, 50
    for j, h in enumerate(halves):
        p.text(x0 + lw + j * cw + cw / 2, y0 - 66, HALF_LABEL[h], 18, INK, MONO, anchor="middle")
        p.text(x0 + lw + j * cw + cw / 2, y0 - 40, f"{n[j]} releases", 15, GRAY, MONO, anchor="middle")
    for i, (var, label) in enumerate(shares.ITEMS):
        y = y0 + i * rh + (18 if i >= 1 else 0) + (18 if i >= 7 else 0) + (18 if i >= 11 else 0)
        p.text(x0 + lw - 18, y + rh / 2 - 13, label, 21, INK, anchor="end")
        for j, h in enumerate(halves):
            row = next(r for r in t if r["item"] == var and r["half"] == h)
            cell(p, x0 + lw + j * cw, y, cw, rh, row["k"], row["n"])
    p.notes([
        "Each cell is the percent of that half-year's frontier releases whose card at launch discloses the item. A late card or no card counts as not disclosed. *H2 26 runs to 31 October.",
        "Frontier release: each lab's top-tier general model per new version (rule frozen before collection), 87 releases from 7 labs, from Epoch AI's database.",
        "Cards coded by two independent passes (agreement kappa 0.83 to 1.00), disagreements adjudicated. Independent Claude check of 80 codes: 78 correct, 0 wrong.",
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
    x0, y0, lw, cw, rh = 64, 250, 250, 136, 62
    for j, h in enumerate(halves):
        p.text(x0 + lw + j * cw + cw / 2, y0 - 46, HALF_LABEL[h], 18, INK, MONO, anchor="middle")
    p.text(x0 + lw + len(halves) * cw + 70, y0 - 46, "ALL", 18, INK, MONO, anchor="middle")
    for i, lab in enumerate(shares.LABS):
        y = y0 + i * rh
        p.text(x0 + lw - 18, y + rh / 2 - 13, LAB_LABEL[lab], 22, INK, anchor="end")
        for j, h in enumerate(halves):
            g = [r for r in recs if r["lab"] == lab and r["half"] == h]
            cell(p, x0 + lw + j * cw, y, cw, rh, sum(1 for r in g if r["any_dc"]), len(g), show_n=True)
        n = sum(1 for r in recs if r["lab"] == lab)
        p.text(x0 + lw + len(halves) * cw + 70, y + rh / 2 - 11, f"{tot[lab]}/{n}", 18, INK, MONO, anchor="middle")
    p.notes([
        "Each cell is the percent of that lab's frontier releases in the half-year whose card at launch reports a dangerous-capability result. – means no release. *H2 26 runs to 31 October.",
        "Independent Claude check of 80 sampled codes: 78 correct, 0 wrong, 2 unsure. No human audit.",
        "Source: lab model and system cards as archived at launch; Epoch AI, Data on AI models (CC BY).",
    ])
    p.save(str(OUT / "lab_by_half_any_dc"))


def trend(recs):
    halves = sorted({r["half"] for r in recs})
    n = [sum(1 for r in recs if r["half"] == h) for h in halves]
    dc = [100 * sum(1 for r in recs if r["half"] == h and r["any_dc"]) / k for h, k in zip(halves, n)]
    ext = [100 * sum(1 for r in recs if r["half"] == h and r["ext_test_any"]) / k for h, k in zip(halves, n)]
    title = (f"Model cards now report dangerous-capability tests at launch\n"
             f"for {dc[-1]:.0f}% of frontier releases, up from {dc[0]:.0f}% in early 2023")
    p = Page(title, "Share of frontier AI model releases whose card, public at launch, discloses each item", height=960)
    p.legend(64, 177, "Any dangerous-capability test result", RED)
    p.legend(700, 177, "Any outside safety testing", INK)
    ax = p.axes(150, 270, 1300, 470)
    xs = list(range(len(halves)))
    ax.plot(xs, dc, color=RED, lw=3, marker="o", ms=7, zorder=4)
    ax.plot(xs, ext, color=INK, lw=3, marker="o", ms=7, zorder=4)
    for x, a, b in zip(xs, dc, ext):
        ax.annotate(f"{a:.0f}%", (x, a), textcoords="offset points", xytext=(0, 11 if a >= b else -22),
                    ha="center", color=RED, fontsize=13, family=MONO)
        ax.annotate(f"{b:.0f}%", (x, b), textcoords="offset points", xytext=(0, -22 if a >= b else 11),
                    ha="center", color=INK, fontsize=13, family=MONO)
    ax.set_ylim(0, 100); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xticks(xs); ax.set_xticklabels([HALF_LABEL[h] for h in halves])
    ax.set_xlim(-0.3, len(halves) - 0.7)
    mono_ticks(ax); p.baseline(ax)
    p.notes([
        "Dangerous-capability test: a reported result on bio, chem or nuclear, cyber, autonomy, persuasion, or deception risk. Releases per half-year: " + ", ".join(str(k) for k in n) + ". *H2 26 runs to 31 October.",
        "87 frontier releases from Anthropic, OpenAI, Google, Meta, xAI, Mistral and DeepSeek. A card published after launch, or no card, counts as no disclosure. 80-code Claude check: 78 correct, 0 wrong.",
        "Source: model and system cards as archived at launch (Wayback Machine, Hugging Face, GitHub); Epoch AI, Data on AI models (CC BY).",
    ])
    p.save(str(OUT / "01_trend"))


def by_lab(recs):
    rows = []
    for lab in shares.LABS:
        g = [r for r in recs if r["lab"] == lab]
        rows.append((LAB_LABEL[lab], f"{sum(r['any_dc'] for r in g)} of {len(g)} releases", 100 * sum(r["any_dc"] for r in g) / len(g), RED))
    rows.sort(key=lambda r: -r[2])
    allv = 100 * sum(r["any_dc"] for r in recs) / len(recs)
    rows.append(("All labs", f"{sum(r['any_dc'] for r in recs)} of {len(recs)} releases", allv, INK))
    top = rows[:2]
    title = f"{top[0][0]} and {top[1][0]} report dangerous-capability tests at launch\nfor about 80% of their releases, Mistral for none"
    p = Page(title, "Share of each lab's frontier releases, 2023 to October 2026, whose card at launch reports a dangerous-capability test result", height=1080)
    bars(p, 64, 230, rows, 100, [0, 25, 50, 75, 100], pct, label_w=400, w=990)
    p.notes([
        "Dangerous-capability test: a reported result on bio, chem or nuclear, cyber, autonomy, persuasion, or deception risk. A late card or no card counts as none.",
        "Independent Claude check of 80 sampled codes: 78 correct, 0 wrong, 2 unsure. No human audit.",
        "Source: model and system cards as archived at launch; Epoch AI, Data on AI models (CC BY).",
    ])
    p.save(str(OUT / "02_by_lab"))


def main() -> int:
    recs = shares.load()
    trend(recs)
    by_lab(recs)
    items_by_half(recs)
    lab_by_half(recs)
    print("wrote", OUT / "01_trend.png", OUT / "02_by_lab.png", "and the appendix tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
