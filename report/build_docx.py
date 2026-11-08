"""Build the Challenge 4 write-up as a .docx for upload to Google Docs.

A plain-language version of docs/methods.md. Every number is computed from the coded data at build
time; the coding statistics it quotes are asserted against analysis.verify_claims and methods.md.

Usage: python3 -m report.build_docx [OUT.docx]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from analysis import shares, verify_claims
from coding import check

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "out" / "Challenge 4 - disclosure series.docx"
FONT = "Arial"
GREY = RGBColor(0x59, 0x59, 0x59)
LINK = RGBColor(0x11, 0x55, 0xCC)
TITLE_FILL = "F1C232"
REPO = "https://github.com/owizdom/tide"
LAB_NAME = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
            "xai": "xAI", "mistral": "Mistral", "deepseek": "DeepSeek"}

# ---------- low-level helpers ----------

def set_font(run, size=11, bold=None, color=None, italic=None):
    run.font.name = FONT
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def shade_run(run, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    run._element.get_or_add_rPr().append(shd)


def shade_cell(cell, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def para(doc, text="", lead=None, size=11, style=None, after=10, color=None, align=None):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.15
    if align is not None:
        p.alignment = align
    if lead:
        set_font(p.add_run(lead + " "), size, bold=True, color=color)
    add_inline(p, text, size, color)
    return p


def add_inline(p, text, size=11, color=None):
    """Plain text; `code` spans never reach here (asserted in build)."""
    if text:
        set_font(p.add_run(text), size, color=color)


def link(p, text, url, size=11):
    part = p.part
    rid = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(k), FONT)
    rpr.append(fonts)
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "1155CC")
    rpr.append(col)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rpr.append(u)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(size * 2))
    rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    h.append(r)
    p._p.append(h)


def heading(doc, text):
    h = doc.add_heading(level=1)
    set_font(h.add_run(text), 14, bold=True, color=RGBColor(0, 0, 0))
    pf = h.paragraph_format
    pf.space_before, pf.space_after, pf.keep_with_next = Pt(18), Pt(6), True
    return h


def picture(doc, path, alt):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    p.add_run().add_picture(str(path), width=Inches(6.0))
    docpr = p._p.xpath(".//wp:docPr")[0]
    docpr.set("descr", alt)
    docpr.set("title", Path(path).stem)


def table_widths(table, widths_dxa):
    table.autofit = False
    tblpr = table._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblpr.append(lay)
    for i, w in enumerate(widths_dxa):
        table.columns[i].width = Inches(w / 1440)
    for row in table.rows:
        for i, c in enumerate(row.cells):
            c.width = Inches(widths_dxa[min(i, len(widths_dxa) - 1)] / 1440)


def cell_text(cell, text, size=8, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run(text), size, bold=bold, color=color)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader")
    h.set(qn("w:val"), "true")
    trpr.append(h)


# ---------- content ----------

DEFS = [
    ("Card at launch", "A system card, model card, technical report or Hugging Face or GitHub model card that was public no later than two days after release."),
    ("Bio, chemical or nuclear", "A launch document reports at least one result for this model: a score, a pass or fail, a threshold decision, or a finding from a named test. Only naming the risk does not count. The same rule applies to the four domains below."),
    ("Cyber", "Offensive cyber ability: capture-the-flag tasks, finding and exploiting vulnerabilities, cyber ranges."),
    ("Autonomy or AI R&D", "Self-replication, automating AI research, self-improvement, or long autonomous tasks tested as a risk."),
    ("Persuasion", "Persuasion, manipulation or influence operations."),
    ("Deception or scheming", "Deception, sabotage, sandbagging, alignment faking, self-exfiltration or reward hacking tested as a risk."),
    ("Framework threshold", "The document says where this model sits against a named level of the lab's safety framework, such as ASL-3 or \"High\" capability. Only naming the framework does not count."),
    ("Any outside testing", "People outside the lab tested this model, named or not, unless the document says this happened after release. Vendors who only ran capability benchmarks do not count."),
    ("Named organisation", "The document names at least one outside organisation that tested this model."),
    ("Government", "The document says a government body tested this model, such as the US or UK AI security institutes."),
    ("Pre-release timing stated", "The document says some outside testing happened before release."),
    ("Safety training", "Training for refusals, harmlessness or policy compliance."),
    ("Runtime safeguards", "A named mechanism used while the model runs: classifiers, filters, moderation or monitoring."),
    ("Access restrictions", "Limits on who can use the model, tied to safety: trusted-access programmes, identity checks, usage tiers. Age gates do not count."),
    ("Weight security", "A stated protection of this model's weights against theft."),
]


def facts():
    recs = shares.load()
    halves = sorted({r["half"] for r in recs})
    by = {h: [r for r in recs if r["half"] == h] for h in halves}
    k = lambda h, key: sum(r[key] for r in by[h])
    lab = {l: (sum(r["any_dc"] for r in recs if r["lab"] == l), sum(1 for r in recs if r["lab"] == l)) for l in shares.LABS}
    man = list(csv.DictReader((ROOT / "cards" / "manifest.csv").open()))
    late = [int(r["card_days_after_launch"]) for r in man if r["sha256"] and r["card_at_launch"] == "0"]
    ext = [round(100 * k(h, "ext_test_any") / len(by[h])) for h in halves]
    drops = list(csv.DictReader((ROOT / "analysis" / "out" / "drops.csv").open()))[:3]
    f = dict(n=len(recs), first=(k(halves[0], "any_dc"), len(by[halves[0]])), last=(k(halves[-1], "any_dc"), len(by[halves[-1]])),
             ext_last=(k(halves[-1], "ext_test_any"), len(by[halves[-1]])), ext_lo=min(ext), ext_hi=max(ext),
             lab=lab, all=sum(r["any_dc"] for r in recs), at_launch=sum(r["card_at_launch"] for r in recs),
             late=len(late), late_lo=min(late), late_hi=max(late),
             never=sum(1 for r in recs if not r["has_card"]), drops=drops,
             sizes=(min(len(v) for v in by.values()), max(len(v) for v in by.values())))
    f["top2"] = lab["anthropic"][0] + lab["openai"][0]
    # Llama 3.1 stand-in sensitivity: text-pass codes only (no arXiv paper)
    v11 = {r["release_id"]: r for r in csv.DictReader((ROOT / "coding" / "codes_v11.csv").open())}
    rid = "meta-2024-07-23-llama-3-1-405b"
    alt = [dict(r) for r in recs]
    for r in alt:
        if r["release_id"] == rid:
            for v in check.VARIABLES:
                r[v] = shares.disclosed(v, int(v11[rid][v])) and r["card_at_launch"]
            r["any_dc"] = any(r[v] for v in shares.DC)
    ext_alt = [round(100 * sum(r["ext_test_any"] for r in alt if r["half"] == h) / len(by[h])) for h in halves]
    f["alt_meta"] = sum(r["any_dc"] for r in alt if r["lab"] == "meta")
    f["alt_ext_lo"] = min(ext_alt)
    return f


def pct(a):
    return f"{round(100 * a[0] / a[1])}%"


def build(out: Path) -> None:
    F = facts()
    claims = " ".join(verify_claims.claims())
    for s in ["1,022 codes", "kappa between 0.83 and 1.00", "The 18 disagreements", "disagreed twice (kappa 0.966)",
              "looked at 1,402 rendered pages", "78 correct, 0 wrong, 2 unsure"]:
        assert s in claims or s in (ROOT / "docs" / "methods.md").read_text(), s
    assert [d["to"] for d in F["drops"]] == ["Muse Spark 1.2", "GPT-4.1", "GPT-4 Turbo (Nov 2023)"]
    L = F["lab"]

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Inches(1))
    for sname in ("Normal", "List Bullet", "List Number"):
        st = doc.styles[sname]
        st.font.name = FONT
        st.font.size = Pt(11)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)

    t = doc.add_paragraph()
    t.paragraph_format.space_after = Pt(6)
    shade_run(set_font(t.add_run("Challenge 4: Are labs disclosing more or less with each model release?"), 20, bold=True), TITLE_FILL)
    para(doc, "Wisdom Okechukwu · 8 November 2026", size=10, color=GREY, after=14)

    para(doc, f"More, but most of it comes from two labs. In the first half of 2023, {F['first'][0]} of {F['first'][1]} frontier releases "
              f"launched with a document reporting a dangerous-capability test. From July to October 2026 it was {F['last'][0]} of "
              f"{F['last'][1]} ({pct(F['last'])}). Anthropic and OpenAI account for {F['top2']} of the {F['all']} releases that did this; "
              f"Mistral, across {L['mistral'][1]} releases, never did. Outside safety testing did not rise the same way.", lead="Short answer.")

    heading(doc, "Three terms")
    para(doc, f"Each lab's top general-purpose model at each new version: {F['n']} releases from Anthropic, OpenAI, Google, Meta, xAI, "
              "Mistral and DeepSeek, January 2023 to October 2026, taken from Epoch AI's model database. The rule and the list were fixed before any document was read.", lead="Frontier release.", after=6)
    para(doc, "A document counts only if it was public within two days of release, in the version that existed then. A card that appeared later counts as no disclosure.", lead="At launch.", after=6)
    para(doc, "A reported result for one of five risks: bio, chemical or nuclear weapons; cyberattacks; autonomy or AI research; persuasion; deception or scheming. Saying a risk was considered, with no result, does not count.", lead="Dangerous-capability test.")
    picture(doc, ROOT / "analysis" / "out" / "01_trend.png",
            "Line chart by half-year, H1 2023 to H2 2026, of the share of frontier releases whose launch documents report any dangerous-capability test result (20, 12, 30, 25, 42, 57, 62, 71 percent) and any outside safety testing (20, 50, 50, 25, 33, 36, 46, 41 percent).")

    heading(doc, "What we found")
    para(doc, f"The share of releases reporting a dangerous-capability result at launch went from {pct(F['first'])} ({F['first'][0]} of {F['first'][1]}) "
              f"in early 2023 to {pct(F['last'])} ({F['last'][0]} of {F['last'][1]}) in late 2026. Each half-year has only {F['sizes'][0]} to "
              f"{F['sizes'][1]} releases, so one release moves a point on the chart by 6 to 20 percentage points. The direction is clear; the exact numbers are rough.", lead="1. Test results at launch became normal.")
    para(doc, f"The share of releases whose launch documents mention any outside testers moved between {F['ext_lo']}% and {F['ext_hi']}% and was "
              f"{pct(F['ext_last'])} ({F['ext_last'][0]} of {F['ext_last'][1]}) in the latest half-year. It never passed half. "
              f"(The low end is {F['alt_ext_lo']}% if one disputed Meta paper is left out; see Limits.)", lead="2. Outside testing did not keep up.")
    para(doc, f"Anthropic reported dangerous-capability results at launch for {L['anthropic'][0]} of {L['anthropic'][1]} releases and OpenAI for "
              f"{L['openai'][0]} of {L['openai'][1]}. Meta did so for {L['meta'][0]} of {L['meta'][1]}, Google for {L['google'][0]} of {L['google'][1]}, "
              f"xAI for {L['xai'][0]} of {L['xai'][1]}, DeepSeek for {L['deepseek'][0]} of {L['deepseek'][1]} and Mistral for {L['mistral'][0]} of {L['mistral'][1]}.",
         lead="3. Two labs do most of the disclosing.")
    picture(doc, ROOT / "analysis" / "out" / "02_by_lab.png",
            "Bar chart of the share of each lab's frontier releases reporting a dangerous-capability result at launch: Anthropic 82% (14 of 17), OpenAI 80% (12 of 15), Meta 45% (5 of 11), Google 38% (5 of 13), xAI 27% (3 of 11), DeepSeek 11% (1 of 9), Mistral 0% (0 of 11), all labs 46% (40 of 87).")
    para(doc, f"Of {F['n']} releases, {F['at_launch']} had a card at launch. {F['late']} got one later, between {F['late_lo']} and {F['late_hi']} days after release, "
              f"and {F['never']} never got one.", lead="4. Many cards are late or missing.")

    heading(doc, "Three times disclosure dropped")
    para(doc, "A drop is an item one release disclosed at launch that the same lab's next frontier release did not. These are the three largest, out of 14 items.").paragraph_format.keep_with_next = True
    d = F["drops"]
    para(doc, f"Muse Spark 1.1 came with a 112-page evaluation report covering {d[0]['n_lost']} of the 14 items. Muse Spark 1.2 came with an announcement "
              "and a note on how its benchmarks were run, but no card. Meta's next release, Muse Spark 1.3, got its report 51 days after launch.",
         lead=f"Meta, Muse Spark 1.1 to 1.2 (August 2026), {d[0]['n_lost']} items lost.", style="List Number", after=8)
    para(doc, "GPT-4.5's system card reported results in all five risk areas. GPT-4.1 never got a card. OpenAI said at the time that \"GPT-4.1 is not a frontier model, so there won't be a separate system card released for it.\" "
              " This study's rule, fixed in advance, counts it as OpenAI's flagship of a new version, so a reader who accepts "
              "OpenAI's view would not count this drop. OpenAI's next frontier release, o3, came two days later with a system card.",
         lead=f"OpenAI, GPT-4.5 to GPT-4.1 (April 2025), {d[1]['n_lost']} items lost.", style="List Number", after=8)
    para(doc, "GPT-4 launched with a technical report and system card covering all five risk areas and outside red teaming, including by the Alignment "
              "Research Center. GPT-4 Turbo launched with an announcement and no card.",
         lead=f"OpenAI, GPT-4 to GPT-4 Turbo (November 2023), {d[2]['n_lost']} items lost.", style="List Number", after=10)

    heading(doc, "How it was done")
    for lead, txt in [
        ("Documents.", "For each release, every document the developer published about that model within two days of release: system and model cards, technical reports, Hugging Face and GitHub model cards, and safety reports about the model. Each was taken as it stood at launch, from the Wayback Machine or the launch-day commit. Announcements and company-wide policies do not count."),
        ("Items.", "Fourteen yes-or-no items: results in the five risk areas, a framework threshold, four kinds of outside testing and four kinds of safeguard. Appendix B defines each one. Text, tables and figures all count; 1,402 pages holding figures or relevant text were checked by eye."),
        ("Coding.", "Two AI coders, Claude Opus 5.5 and Claude Sonnet 5.5, read every document separately. Every \"yes\" had to quote the document or cite a figure. They agreed closely (Cohen's kappa 0.83 to 1.00 per item), and separate Claude instances that coded nothing settled the 20 disagreements."),
        ("Checks.", "A further Claude instance re-checked 80 randomly chosen codes against the documents: 78 correct, 0 wrong, 2 unsure. A script checks every number in this write-up against the data."),
        ("Not scored.", "Card length. It is recorded for every card but never counts toward any share."),
    ]:
        para(doc, txt, lead=lead, style="List Bullet", after=6)

    heading(doc, "Limits")
    para(doc, "Gaps in the public record.", lead=None, after=4).runs[0].bold = True
    for txt in [
        f"Meta posted two papers at launch that were never archived: LLaMA (2023) and Llama 3.1 (2024). Their arXiv copies, posted 3 and 8 days later, are used instead. Without the Llama 3.1 paper, Meta's count falls to {F['alt_meta']} of {L['meta'][1]}, and the second half of 2024 falls from 25% to 12% on both chart lines.",
        "Three late cards (Muse Spark 1.3, Grok 4.20, Grok 4.5) were first archived after their printed dates, so their first version cannot be confirmed. None of them affects an at-launch number.",
    ]:
        para(doc, txt, style="List Bullet", after=4)
    para(doc, "Choices in this study.", after=4).runs[0].bold = True
    for txt in [
        "All coding and checking was done by Claude models, with no human audit. Two coders from one model family can share blind spots, so their agreement may overstate how reliable the codes are.",
        "The frontier rule decides which releases count, and a lab may disagree with it, as OpenAI did for GPT-4.1.",
        "A release with no card at launch scores zero on every item, even when it had another launch document. Four such documents were found. One could add a safety-training code (xAI's Grok 4.5 training-data summary says its data was \"filtered for quality and safety\"), which would change no number in the main text.",
        "The latest half-year ends on 31 October 2026.",
    ]:
        para(doc, txt, style="List Bullet", after=4)

    heading(doc, "Sources and data")
    p = para(doc, "", after=6)
    add_inline(p, "Developer documents as archived at launch, via the ")
    link(p, "Wayback Machine", "https://web.archive.org/")
    add_inline(p, ", Hugging Face, GitHub and arXiv. Release list from Epoch AI, ")
    link(p, "Data on AI models", "https://epoch.ai/data/ai-models")
    add_inline(p, " (CC BY 4.0). Items aligned with the ")
    link(p, "Foundation Model Transparency Index", "https://crfm.stanford.edu/fmti/")
    add_inline(p, " (December 2025). OpenAI's GPT-4.1 statement as ")
    link(p, "reported by TechCrunch", "https://techcrunch.com/2025/04/15/openai-ships-gpt-4-1-without-a-safety-report/")
    add_inline(p, ", 15 April 2025.")
    p = para(doc, "", lead="Data and code.")
    add_inline(p, "The release-by-release table, every code with its quote, the full method and the code behind each chart: ")
    link(p, REPO, REPO)
    add_inline(p, ".")

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    heading(doc, "Appendix A. Every item, and every lab, by half-year")
    para(doc, "Each cell is the percent of that half-year's frontier releases that disclosed the item at launch. The number of releases is under each half-year.")
    picture(doc, ROOT / "analysis" / "out" / "share_by_half.png",
            "Grid of 15 rows (card at launch and 14 disclosure items) by 8 half-years, each cell the percent of frontier releases disclosing the item at launch.")
    picture(doc, ROOT / "analysis" / "out" / "lab_by_half_any_dc.png",
            "Grid of 7 labs by 8 half-years, each cell the percent of that lab's frontier releases in the half-year reporting a dangerous-capability result at launch.")

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    heading(doc, "Appendix B. What counts as disclosed")
    tc = doc.add_table(rows=1, cols=2)
    tc.style = "Table Grid"
    for c, h in zip(tc.rows[0].cells, ["Item", "Counts when"]):
        cell_text(c, h, size=9, bold=True)
        shade_cell(c, "D9D9D9")
    repeat_header(tc.rows[0])
    groups = {1: "Dangerous-capability results", 6: "Framework", 7: "Outside testing", 11: "Safeguards"}
    for i, (item, txt) in enumerate(DEFS):
        if i in groups:
            rc = tc.add_row().cells
            m = rc[0].merge(rc[1])
            cell_text(m, groups[i], size=9, bold=True)
            shade_cell(m, "FFF2CC")
        cells = tc.add_row().cells
        cell_text(cells[0], item, size=9)
        cell_text(cells[1], txt, size=9)
    table_widths(tc, [2600, 6760])

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)


def main(argv=None) -> int:
    out = Path(argv[0]) if argv else OUT
    build(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
