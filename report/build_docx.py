"""Build the Challenge 4 write-up as a .docx for upload to Google Docs.

Text comes from docs/methods.md (so every number is the one analysis.verify_claims checks), with
repository file paths swapped for reader-facing wording. The release table is computed from the
coded data. The script asserts every methods.md claim phrase is present in the output.

Usage: python3 -m report.build_docx [OUT.docx]
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from analysis import shares, verify_claims

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "out" / "Challenge 4 - disclosure series.docx"
FONT = "Arial"
GREY = RGBColor(0x59, 0x59, 0x59)
LINK = RGBColor(0x11, 0x55, 0xCC)
TITLE_FILL = "F1C232"
REPO = "https://github.com/owizdom/tide"
LAB_NAME = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
            "xai": "xAI", "mistral": "Mistral", "deepseek": "DeepSeek"}

# repository paths in methods.md -> reader wording (each must match exactly once)
SWAPS = [
    (" (export of 5 November 2026, sha256 pinned in `releases/epoch/SOURCE.txt`)", " (export of 5 November 2026, pinned by sha256)"),
    ("The rule and every include or exclude decision (`releases/ladders.yaml`) were frozen", "The rule and every include or exclude decision were frozen"),
    ("; every exclusion is logged with its reason in `cards/discovery/disc2_excluded.csv`.", "; every exclusion is logged with its reason."),
    (" The codebook is `coding/codebook.md`.", " Appendix B gives each definition."),
    (" They are listed in `cards/no_card_launch_docs.csv`.", ""),
    ("Card length is reported separately in `cards/manifest.csv` and never enters a share.", "Card length is reported separately and never enters a share."),
]
LEADS = {  # findings paragraphs get a short bold label, like the brief's run-in heads
    "Far more frontier releases": "Rising.",
    "Outside testing has not kept pace.": "Outside testing.",
    "Disclosure is concentrated.": "Concentrated.",
    "Cards are often late or missing.": "Late and missing cards.",
}
LIMIT_LEADS = ["Unarchived papers.", "Unproven first versions.", "Two images.", "Small half-years.", "Partial half-year."]


def methods_sections() -> dict[str, list[str]]:
    text = (ROOT / "docs" / "methods.md").read_text(encoding="utf-8")
    for a, b in SWAPS:
        assert text.count(a) == 1, f"swap target not found once: {a!r}"
        text = text.replace(a, b)
    secs, cur = {}, None
    for block in text.split("\n\n"):
        block = block.strip()
        if block.startswith("## "):
            cur = block[3:]
            secs[cur] = []
        elif cur and block:
            secs[cur].extend(block.split("\n") if block.startswith(("- ", "1. ")) else [block])
    return secs


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

def release_rows():
    recs = shares.load()
    man = {r["release_id"]: r for r in csv.DictReader((ROOT / "cards" / "manifest.csv").open())}
    rows = []
    for r in recs:
        m = man[r["release_id"]]
        if r["card_at_launch"]:
            card = "at launch"
        elif r["has_card"]:
            card = f"+{int(m['card_days_after_launch'])} days"
        else:
            card = "none"
        res = " ".join(l for v, l in zip(shares.DC, "BCAPD") if r[v]) or "none"
        out = " ".join(l for v, l in zip(["ext_test_any", "ext_test_named_org", "ext_test_government", "ext_test_timing_stated"], "ONGT") if r[v]) or "none"
        sg = " ".join(l for v, l in zip(["safeguards_training", "safeguards_runtime", "safeguards_access", "safeguards_weights"], "TRAW") if r[v]) or "none"
        rows.append({"lab": r["lab"], "model": r["model"], "date": r["date"], "card": card, "res": res,
                     "thr": "yes" if r["framework_threshold"] else "no", "out": out, "sg": sg,
                     "words": f"{r['card_words']:,}" if r["has_card"] and r["card_words"] else "",
                     "_rec": r})
    order = {l: i for i, l in enumerate(shares.LABS)}
    rows.sort(key=lambda x: (order[x["lab"]], x["date"]))
    return rows


def check_rows(rows):
    recs = [x["_rec"] for x in rows]
    assert len(rows) == 87
    assert sum(x["card"] == "at launch" for x in rows) == sum(r["card_at_launch"] for r in recs)
    assert sum(x["res"] != "none" for x in rows) == sum(r["any_dc"] for r in recs)
    assert sum("O" in x["out"].split() for x in rows) == sum(r["ext_test_any"] for r in recs)


DEFS = [
    ("Card at launch", "A system card, model card, technical report or repository model card public no later than two days after launch."),
    ("B  Bio, chemical or nuclear", "A launch document reports at least one result for this model in the domain: a score, a pass or fail against a task set, a threshold determination, or a described finding from a named test. Naming the domain without a result does not count. The same rule applies to C, A, P and D."),
    ("C  Cyber", "Offensive cyber capability: capture-the-flag tasks, vulnerability discovery and exploitation, cyber ranges. Prompt-injection robustness alone is not cyber capability."),
    ("A  Autonomy or AI R&D", "Autonomous replication, automation of AI research and development, self-improvement, or long-horizon autonomous tasks evaluated as a risk."),
    ("P  Persuasion", "Persuasion, manipulation or influence operations."),
    ("D  Deception or scheming", "Deception, sabotage, sandbagging, evaluation awareness, alignment faking, self-exfiltration or reward hacking evaluated as a misalignment risk."),
    ("Framework threshold", "The document states where this model sits against a named threshold or level of a safety framework (ASL-3 required or not, \"High\" or \"Critical\" in a category, a Critical Capability Level reached or not). Naming the framework alone does not count."),
    ("O  Outside testing", "People outside the lab tested this model before release (red teamers, testers, partners), named or not, unless the document says the testing came after release. Capability-benchmark vendors are not outside safety testing."),
    ("N  Named organisation", "The document names at least one outside organisation that tested this model."),
    ("G  Government", "The document says a government body tested this model (US CAISI or AISI, UK AISI, another state institute)."),
    ("T  Pre-release timing stated", "The document states that some outside testing of this model happened before its release."),
    ("T  Safety training", "Safety training or fine-tuning for refusals, harmlessness or policy compliance."),
    ("R  Runtime safeguards", "A named mechanism applied at inference or in production: classifiers, filters, moderation or monitoring."),
    ("A  Access restrictions", "Access restrictions the document ties to risk or safety: trusted access programmes, identity checks, usage tiers, limited availability for safety reasons. Consumer age gates do not count."),
    ("W  Weight security", "A stated protection of this model's weights against theft or exfiltration."),
]


def build(out: Path) -> str:
    secs = methods_sections()
    for k, v in secs.items():
        for b in v:
            assert "`" not in b, f"code span left in {k}: {b[:80]}"
    rows = release_rows()
    check_rows(rows)
    recs = [x["_rec"] for x in rows]
    top2 = sum(r["any_dc"] for r in recs if r["lab"] in ("anthropic", "openai"))
    alldc = sum(r["any_dc"] for r in recs)

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

    # title, highlighted like the brief
    t = doc.add_paragraph()
    t.paragraph_format.space_after = Pt(6)
    r = set_font(t.add_run("Challenge 4: Are labs disclosing more or less with each model release?"), 20, bold=True)
    shade_run(r, TITLE_FILL)
    para(doc, "Wisdom Okechukwu · 8 November 2026", size=10, color=GREY, after=14)

    f = secs["Findings"]
    lo_ext = re.search(r"between (\d+)% and", f[1]).group(1)
    hi_ext = re.search(r"and (\d+)% across", f[1]).group(1)
    answer = (f"Both rising and concentrating. {f[0].split('. ', 1)[1]} Anthropic and OpenAI account for "
              f"{top2} of the {alldc} releases that did so, Mistral for none, and outside testing has stayed "
              f"between {lo_ext}% and {hi_ext}% of releases.")
    para(doc, answer, lead="Answer.")
    para(doc, "Every frontier release from seven labs, January 2023 to October 2026, coded from the developer's own documents as they stood at launch for 14 safety disclosure items. A release counts as disclosing an item only if a document public within two days of launch reports it.", lead="What this is.")

    picture(doc, ROOT / "analysis" / "out" / "01_trend.png",
            "Line chart by half-year, H1 2023 to H2 2026, of the share of frontier releases whose launch documents report any dangerous-capability test result (20, 12, 30, 25, 42, 57, 62, 71 percent) and any outside safety testing (20, 50, 50, 25, 33, 36, 46, 41 percent).")
    heading(doc, "Findings")
    for b in f:
        lead = next(v for k, v in LEADS.items() if b.startswith(k))
        para(doc, b, lead=lead)
        if lead == "Concentrated.":
            picture(doc, ROOT / "analysis" / "out" / "02_by_lab.png",
                    "Bar chart of the share of each lab's frontier releases reporting a dangerous-capability result at launch: Anthropic 82% (14 of 17), OpenAI 80% (12 of 15), Meta 45% (5 of 11), Google 38% (5 of 13), xAI 27% (3 of 11), DeepSeek 11% (1 of 9), Mistral 0% (0 of 11), all labs 46% (40 of 87).")

    heading(doc, "Three drops between successive releases")
    d = secs["Three drops between successive releases"]
    para(doc, d[0])
    for b in d[1:]:
        body = re.sub(r"^\d+\. ", "", b)
        lead, rest = body.split(". ", 1)
        para(doc, rest, lead=lead + ".", style="List Number", after=8)

    heading(doc, "What was measured")
    for b in secs["What was measured"]:
        if b.startswith("Card length is reported separately"):
            para(doc, "Recorded in words for every card and never part of any share.", lead="Card length.")
            continue
        lead, rest = b.split(". ", 1)
        para(doc, rest, lead=lead + ".")

    heading(doc, "How the documents were coded")
    for b in secs["How the documents were coded"]:
        lead, rest = b.split(". ", 1)
        para(doc, rest, lead=lead + ".")

    heading(doc, "Limits")
    lim = secs["Limits"]
    para(doc, lim[0])
    bullets = [b[2:] for b in lim[1:]]
    assert len(bullets) == len(LIMIT_LEADS)
    for lead, b in zip(LIMIT_LEADS, bullets):
        para(doc, b, lead=lead, style="List Bullet", after=6)

    heading(doc, "Sources")
    p = para(doc, "", after=6)
    add_inline(p, "Model and system cards, technical reports and model-specific safety reports from the seven labs as archived at launch, via the ")
    link(p, "Wayback Machine", "https://web.archive.org/")
    add_inline(p, ", ")
    link(p, "Hugging Face", "https://huggingface.co/models")
    add_inline(p, ", GitHub and arXiv. Epoch AI, ")
    link(p, "Data on AI models", "https://epoch.ai/data/ai-models")
    add_inline(p, " (CC BY 4.0). Stanford CRFM, ")
    link(p, "Foundation Model Transparency Index", "https://crfm.stanford.edu/fmti/")
    add_inline(p, " (December 2025), for indicator alignment. Free Systems, ")
    link(p, "Model Cards: collect 'em all", "https://freesystems.substack.com/p/model-cardscollect-em-all")
    add_inline(p, ".")
    p = para(doc, "", lead="Data and code.")
    add_inline(p, "The release-by-release table, every code with its supporting quote, the codebook and the code behind each figure: ")
    link(p, REPO, REPO)
    add_inline(p, ". Every document is pinned by source URL, archive capture and sha256.")

    # Appendix A
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    heading(doc, "Appendix A. Every item by half-year, and every lab by half-year")
    para(doc, "Each cell is the percent of that half-year's frontier releases whose documents public at launch disclose the item. The number of releases in each half-year is under its label.")
    picture(doc, ROOT / "analysis" / "out" / "share_by_half.png",
            "Grid of 15 rows (card at launch and 14 disclosure items) by 8 half-years, each cell the percent of frontier releases disclosing the item at launch.")
    picture(doc, ROOT / "analysis" / "out" / "lab_by_half_any_dc.png",
            "Grid of 7 labs by 8 half-years, each cell the percent of that lab's frontier releases in the half-year reporting a dangerous-capability result at launch.")

    # Appendix C
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    heading(doc, "Appendix B. What counts as disclosed")
    para(doc, "Short form of the codebook. Each item is judged on every document about the model public within two days of launch, including tables and figures, and every positive code carries a quote or a figure citation from that document.")
    tc = doc.add_table(rows=1, cols=2)
    tc.style = "Table Grid"
    for c, h in zip(tc.rows[0].cells, ["Item", "Counts as disclosed when"]):
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
    return answer


def main(argv=None) -> int:
    out = Path(argv[0]) if argv else OUT
    build(out)
    import subprocess
    text = subprocess.run(["pandoc", "-t", "plain", "--wrap=none", str(out)], capture_output=True, text=True, check=True).stdout
    flat = re.sub(r"\s+", " ", text)
    missing = [c for c in verify_claims.claims() if re.sub(r"\s+", " ", c) not in flat]
    for c in missing:
        print("MISSING IN DOCX:", c)
    print(f"wrote {out}; {len(verify_claims.claims()) - len(missing)} of {len(verify_claims.claims())} methods claims present")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
