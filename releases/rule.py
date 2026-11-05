"""Frontier release rule (spec 0001, section 1.1).

Mechanical part: lab, window, domain and public-access filters over Epoch's full database.
Judgement part: one decision per surviving candidate in ladders.yaml, with a reason code from
a frozen vocabulary and, where the reason is relative, a `ref` to the model it is relative to.
check_consistency() verifies reference links (same lab, date order, ref included) for every
relative reason, and version and tier rank for HIGHER_TIER. Non-relative exclusions rest on
their note and on human review of decisions.csv.

Usage: python3 -m releases.rule [--zip PATH] [--write]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PINNED_ZIP_SHA256 = "a31aafbf290549655ca57ef4d6f207cdc9bc036dfbde183c14ba5114323d6ee4"
WINDOW = ("2023-01-01", "2026-10-31")

LAB_PATTERNS = [
    ("anthropic", r"Anthropic"),
    ("openai", r"OpenAI"),
    ("google", r"Google|DeepMind"),
    ("meta", r"Meta AI|Facebook AI Research"),
    ("xai", r"xAI"),
    ("mistral", r"Mistral"),
    ("deepseek", r"DeepSeek"),
]

INCLUDE_REASONS = {"NEW_VERSION", "HIGHER_TIER", "SAME_EVENT"}
EXCLUDE_REASONS = {
    "LOWER_TIER",      # below an included model of the same lab released on or before it
    "SMALL_TIER",      # a tier the ladder marks small (mini, nano, lite, haiku, small)
    "SNAPSHOT",        # dated re-release or experimental checkpoint of an included model
    "INFERENCE_MODE",  # Pro, Deep Think, Thinking, Instant: a mode of an included model
    "DOMAIN_VARIANT",  # code, cyber, math, vision-only, voice, image, embedding, OCR, safety classifier
    "SECONDARY_LINE",  # a smaller parallel line while the lab has a larger flagship line (Gemma, gpt-oss)
    "THIRD_PARTY",     # fine-tune or derivative by another organisation
    "NOT_GENERAL",     # research artifact, not a general-purpose model product
    "NOT_PUBLIC",      # limited or trusted access only at launch
    "AGENT_PRODUCT",   # agent product built on models already in the pool
}
NEEDS_REF = {"HIGHER_TIER", "SAME_EVENT", "LOWER_TIER", "SNAPSHOT", "INFERENCE_MODE"}


class InputMismatch(Exception):
    pass


@dataclass
class Candidate:
    epoch_name: str
    lab: str
    epoch_date: str
    accessibility: str
    domain: str
    available_date: str = ""

    def date(self) -> str:
        return self.available_date or self.epoch_date


@dataclass
class Decision:
    reason: str
    version: str | None = None
    tier: str | None = None
    ref: str | None = None
    note: str | None = None
    available: str | None = None
    available_src: str | None = None


@dataclass
class Event:
    release_id: str
    lab: str
    model: str
    epoch_name: str
    epoch_date: str
    available_date: str
    tier: str
    rule_reason: str
    event_models: list[str] = field(default_factory=list)


@dataclass
class Built:
    candidates: list[Candidate]
    decisions: dict[str, Decision]
    ladders: dict[str, dict]
    events: list[Event]


def default_zip_path() -> Path:
    return ROOT / "releases" / "epoch" / "ai_models.zip"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lab_of(org: str) -> str | None:
    for key, pat in LAB_PATTERNS:
        if re.search(pat, org):
            return key
    return None


def load_candidates(zip_path: Path) -> list[Candidate]:
    got = sha256_file(zip_path)
    if got != PINNED_ZIP_SHA256:
        raise InputMismatch(f"{zip_path} sha256 {got} != pinned {PINNED_ZIP_SHA256}")
    with zipfile.ZipFile(zip_path) as z:
        text = z.read("all_ai_models.csv").decode("utf-8")
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        lab = lab_of(row["Organization"])
        date = row["Publication date"]
        if not lab or not (WINDOW[0] <= date <= WINDOW[1]):
            continue
        domain = row["Domain"]
        if domain and not re.search(r"Language|Multimodal", domain):
            continue
        if row["Model accessibility"].startswith("Unreleased"):
            continue
        out.append(Candidate(row["Model"], lab, date, row["Model accessibility"], domain))
    out.sort(key=lambda c: (c.lab, c.epoch_date, c.epoch_name))
    return out


def load_ladders(path: Path) -> tuple[dict[str, dict], dict[str, Decision]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    ladders, decisions = {}, {}
    for lab, spec in data.items():
        ladders[lab] = {"tiers": spec["tiers"], "small": set(spec.get("small", []))}
        for name, d in spec["models"].items():
            if name in decisions:
                raise ValueError(f"{name} decided twice")
            decisions[name] = Decision(
                reason=d["r"], version=d.get("v"), tier=d.get("t"), ref=d.get("ref"), note=d.get("n"),
                available=str(d["a"]) if d.get("a") else None, available_src=d.get("src"),
            )
    return ladders, decisions


def half_year(date: str) -> str:
    return f"{date[:4]}H{1 if int(date[5:7]) <= 6 else 2}"


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def tier_rank(ladders: dict, lab: str, tier: str | None) -> int:
    tiers = ladders[lab]["tiers"]
    return tiers.index(tier) if tier in tiers else -1


def build_events(cands: list[Candidate], decisions: dict[str, Decision], ladders: dict) -> list[Event]:
    by_name = {c.epoch_name: c for c in cands}
    groups: dict[tuple[str, str], list[str]] = {}
    for c in cands:
        d = decisions.get(c.epoch_name)
        if d and d.reason in INCLUDE_REASONS:
            groups.setdefault((c.lab, c.date()), []).append(c.epoch_name)
    events = []
    for (lab, date), names in sorted(groups.items()):
        heads = [n for n in names if decisions[n].reason != "SAME_EVENT"]
        head = max(heads, key=lambda n: (tier_rank(ladders, lab, decisions[n].tier), n))
        d = decisions[head]
        events.append(
            Event(
                release_id=f"{lab}-{date}-{slug(head)}",
                lab=lab,
                model=head,
                epoch_name=head,
                epoch_date=by_name[head].epoch_date,
                available_date=date,
                tier=d.tier or "",
                rule_reason=d.reason,
                event_models=sorted(names),
            )
        )
    return events


def build(zip_path: Path, ladders_path: Path) -> Built:
    cands = load_candidates(zip_path)
    ladders, decisions = load_ladders(ladders_path)
    for c in cands:
        d = decisions.get(c.epoch_name)
        if d and d.available:
            c.available_date = d.available
    return Built(cands, decisions, ladders, build_events(cands, decisions, ladders))


def check_consistency(b: Built) -> list[str]:
    """Return a list of problems; empty means every relative judgement checks out."""
    probs = []
    by_name = {c.epoch_name: c for c in b.candidates}
    included = {n for n, d in b.decisions.items() if d.reason in INCLUDE_REASONS}
    for name, d in b.decisions.items():
        c = by_name.get(name)
        if c is None:
            probs.append(f"{name}: not in candidate pool")
            continue
        lad = b.ladders[c.lab]
        if d.reason not in INCLUDE_REASONS | EXCLUDE_REASONS:
            probs.append(f"{name}: unknown reason {d.reason}")
            continue
        if d.tier is not None and d.tier not in lad["tiers"]:
            probs.append(f"{name}: tier {d.tier} not in {c.lab} ladder")
        if d.reason in INCLUDE_REASONS and d.tier in lad["small"]:
            probs.append(f"{name}: small tier {d.tier} cannot be included")
        if d.reason in {"NEW_VERSION", "HIGHER_TIER"} and (not d.version or not d.tier):
            probs.append(f"{name}: {d.reason} needs version and tier")
        if d.reason == "SMALL_TIER" and d.tier not in lad["small"]:
            probs.append(f"{name}: SMALL_TIER but tier {d.tier} is not marked small")
        if d.available and not d.available_src:
            probs.append(f"{name}: available date override needs a src")
        if d.reason in NEEDS_REF:
            r = by_name.get(d.ref) if d.ref else None
            rd = b.decisions.get(d.ref) if d.ref else None
            if r is None or rd is None:
                probs.append(f"{name}: {d.reason} needs a ref in the pool, got {d.ref!r}")
                continue
            if r.lab != c.lab:
                probs.append(f"{name}: ref {d.ref} is another lab")
            if d.ref not in included:
                probs.append(f"{name}: ref {d.ref} is not an included model")
            if d.reason == "SAME_EVENT" and r.date() != c.date():
                probs.append(f"{name}: SAME_EVENT ref {d.ref} has another date")
            if d.reason in {"LOWER_TIER", "SNAPSHOT", "INFERENCE_MODE"} and r.date() > c.date():
                probs.append(f"{name}: ref {d.ref} is dated after it")
            if d.reason == "HIGHER_TIER":
                if r.date() >= c.date():
                    probs.append(f"{name}: HIGHER_TIER ref {d.ref} not earlier")
                if rd.version != d.version:
                    probs.append(f"{name}: HIGHER_TIER ref {d.ref} has version {rd.version} != {d.version}")
                if tier_rank(b.ladders, c.lab, rd.tier) >= tier_rank(b.ladders, c.lab, d.tier):
                    probs.append(f"{name}: HIGHER_TIER but ref tier {rd.tier} >= {d.tier}")
            if d.reason == "LOWER_TIER" and rd.version == d.version and d.tier and rd.tier:
                if tier_rank(b.ladders, c.lab, rd.tier) < tier_rank(b.ladders, c.lab, d.tier):
                    probs.append(f"{name}: LOWER_TIER but ref tier {rd.tier} < {d.tier}")
        elif d.reason in EXCLUDE_REASONS - {"SMALL_TIER"} and not d.note:
            probs.append(f"{name}: {d.reason} needs a note")
        if d.reason == "NEW_VERSION":
            for other, od in b.decisions.items():
                oc = by_name.get(other)
                if (
                    other != name and oc and oc.lab == c.lab and od.version == d.version
                    and od.reason in {"NEW_VERSION", "HIGHER_TIER"} and oc.date() < c.date()
                ):
                    probs.append(f"{name}: NEW_VERSION but {other} has version {d.version} earlier")
    return probs


CSV_FIELDS = [
    "release_id", "lab", "model", "epoch_name", "epoch_date", "available_date",
    "tier", "rule_reason", "event_models",
]


def render_csv(events: list[Event]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n")
    w.writeheader()
    for e in events:
        w.writerow({**e.__dict__, "event_models": " | ".join(e.event_models)})
    return buf.getvalue()


def render_decisions_csv(b: Built) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["lab", "epoch_date", "epoch_name", "accessibility", "decision", "reason", "version", "tier", "ref", "note"])
    for c in b.candidates:
        d = b.decisions[c.epoch_name]
        w.writerow([
            c.lab, c.epoch_date, c.epoch_name, c.accessibility,
            "include" if d.reason in INCLUDE_REASONS else "exclude",
            d.reason, d.version or "", d.tier or "", d.ref or "", d.note or "",
        ])
    return buf.getvalue()


SENS_LOW = re.compile(r"\b(mini|nano|lite|small|haiku|instant|fast|glimmer|ministral|scout|turbo instruct)\b|gpt-3\.5|flash-lite|\bE\d+B\b", re.I)
SENS_SPEC = re.compile(r"codex|cyber|math|coder|codestral|devstral|rosalind|voice|image|guard|embed|robotics|decisions|ocr|prover|vla|funsearch|cua|computer-using|movie|music|sora|veo|imagen|whisper|chirp|lyria|genie|weather|diffusion|\bexp-", re.I)
SENS_SNAP = re.compile(r"\((jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}\)|\b0\d{3}\b|terminus|\b-exp\b|preview\)", re.I)


def sensitivity_events(zip_path: Path) -> list[tuple[str, str, str]]:
    """Mechanical alternative rule kept as a sensitivity check (spec 1.1): Epoch notable plus
    large-scale subsets, name filters only, one event per lab per Epoch date."""
    if sha256_file(zip_path) != PINNED_ZIP_SHA256:
        raise InputMismatch(str(zip_path))
    pool = {}
    with zipfile.ZipFile(zip_path) as z:
        for f in ("notable_ai_models.csv", "large_scale_ai_models.csv"):
            for row in csv.DictReader(io.StringIO(z.read(f).decode("utf-8"))):
                pool[row["Model"]] = row
    ev: dict[tuple[str, str], list[str]] = {}
    for m, row in pool.items():
        lab, d = lab_of(row["Organization"]), row["Publication date"]
        if not lab or not (WINDOW[0] <= d <= WINDOW[1]):
            continue
        if not re.search(r"Language|Multimodal", row["Domain"]) or row["Model accessibility"].startswith("Unreleased"):
            continue
        if SENS_SPEC.search(m) or SENS_LOW.search(m) or (SENS_SNAP.search(m) and not m.startswith("GPT-4 (Mar")):
            continue
        ev.setdefault((lab, d), []).append(m)
    return [(lab, d, " | ".join(sorted(ms))) for (lab, d), ms in sorted(ev.items())]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, default=default_zip_path())
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    b = build(a.zip, ROOT / "releases" / "ladders.yaml")
    probs = check_consistency(b)
    missing = sorted({c.epoch_name for c in b.candidates} - set(b.decisions))
    for p in probs + [f"undecided: {m}" for m in missing]:
        print(p, file=sys.stderr)
    if probs or missing:
        return 1
    text = render_csv(b.events)
    print(f"candidates {len(b.candidates)}  events {len(b.events)}  sha256 {hashlib.sha256(text.encode()).hexdigest()}")
    if a.write:
        (ROOT / "releases" / "frontier.csv").write_text(text, encoding="utf-8")
        (ROOT / "releases" / "decisions.csv").write_text(render_decisions_csv(b), encoding="utf-8")
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["lab", "epoch_date", "models"])
        w.writerows(sensitivity_events(a.zip))
        (ROOT / "releases" / "sensitivity_epoch_subsets.csv").write_text(buf.getvalue(), encoding="utf-8")
        (ROOT / "releases" / "frontier.sha256").write_text(
            hashlib.sha256(text.encode()).hexdigest() + "  frontier.csv\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
