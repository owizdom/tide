"""Track B acceptance tests (spec 0001 AT3, AT4, AT5) plus unit tests for capture selection."""
import csv
import hashlib
import re
from pathlib import Path

from cards import fetch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cards" / "manifest.csv"
SEARCH_SOURCES = {"lab", "announcement", "hf", "github", "arxiv", "wayback"}


# ---- unit: pure selection logic -------------------------------------------------

def test_raw_wayback_url_uses_id_mode():
    assert fetch.raw_url("20250822000303", "https://data.x.ai/a.pdf") == (
        "https://web.archive.org/web/20250822000303id_/https://data.x.ai/a.pdf"
    )


def test_earliest_capture_is_the_launch_version_candidate():
    caps = [("20250828005111", "B"), ("20250822000303", "A"), ("20250822005628", "A")]
    assert fetch.earliest(caps) == ("20250822000303", "A")


def test_days_after_launch():
    assert fetch.days_between("2025-07-09", "2025-08-22") == 44
    assert fetch.days_between("2025-07-09", "2025-07-09") == 0


def test_at_launch_rule_uses_documented_date_first():
    # documented date on launch day, first capture 40 days later: card existed at launch,
    # but the archived bytes are not proven to be the launch version.
    s = fetch.launch_status("2025-07-09", card_date="2025-07-09", capture_ts="20250818000000")
    assert s == {"card_at_launch": 1, "launch_version_unverified": 1, "card_days_after_launch": 0}


def test_at_launch_rule_late_card():
    s = fetch.launch_status("2025-07-09", card_date="2025-08-20", capture_ts="20250822000303")
    # captured 2 days after its own publication: these bytes are the first published version
    assert s == {"card_at_launch": 0, "launch_version_unverified": 0, "card_days_after_launch": 42}


def test_at_launch_rule_capture_within_grace():
    s = fetch.launch_status("2024-05-13", card_date="", capture_ts="20240515120000")
    assert s == {"card_at_launch": 1, "launch_version_unverified": 0, "card_days_after_launch": 2}


def test_capture_before_printed_date_wins():
    # a printed revision date cannot make a document younger than its first archived copy
    s = fetch.launch_status("2026-04-08", card_date="2026-05-26", capture_ts="20260414233054")
    assert s == {"card_at_launch": 0, "launch_version_unverified": 0, "card_days_after_launch": 6}


def test_digest_change_dates():
    caps = [("20250822000303", "A"), ("20250822005628", "A"), ("20250828005111", "B"), ("20250901000000", "B")]
    assert fetch.digest_change_dates(caps) == ["2025-08-28"]


def test_pick_primary_takes_latest_card_public_by_launch():
    rows = [
        {"doc_kind": "announcement_only", "card_date": "2026-07-09", "card_url": "a"},
        {"doc_kind": "system_card", "card_date": "2026-06-25", "card_url": "preview"},
        {"doc_kind": "system_card", "card_date": "2026-07-09", "card_url": "launch"},
        {"doc_kind": "system_card", "card_date": "2026-08-19", "card_url": "later"},
    ]
    assert fetch.pick_primary(rows, "2026-07-09")["card_url"] == "launch"


def test_pick_primary_falls_back_to_earliest_later_card():
    rows = [
        {"doc_kind": "announcement_only", "card_date": "2024-05-13", "card_url": "a"},
        {"doc_kind": "system_card", "card_date": "2024-08-08", "card_url": "b"},
        {"doc_kind": "addendum", "card_date": "2024-10-01", "card_url": "c"},
    ]
    assert fetch.pick_primary(rows, "2024-05-13")["card_url"] == "b"
    assert fetch.pick_primary([{"doc_kind": "none", "card_date": "", "card_url": ""}], "2024-05-13") is None


def test_undated_card_uses_first_capture_date():
    rows = [
        {"doc_kind": "github_card", "card_date": "2024-03-14", "card_url": "repo"},
        {"doc_kind": "model_card", "card_date": "", "date_eff": "2023-11-05", "card_url": "x.ai/model-card"},
    ]
    assert fetch.pick_primary(rows, "2023-11-04")["card_url"] == "x.ai/model-card"


def test_pick_prefers_richest_kind_within_launch_window():
    # every document public by launch + 2 counts as at launch; code the richest one
    rows = [
        {"doc_kind": "hf_card", "card_date": "2025-01-20", "card_url": "readme"},
        {"doc_kind": "tech_report", "card_date": "2025-01-22", "card_url": "paper"},
        {"doc_kind": "tech_report", "card_date": "2025-01-20", "card_url": "launch-pdf"},
    ]
    assert fetch.pick_primary(rows, "2025-01-20")["card_url"] == "launch-pdf"


def test_pick_tie_prefers_earliest_archived_copy():
    rows = [
        {"doc_kind": "system_card", "card_date": "2025-02-24", "wayback_first_200": "20260126195603", "card_url": "late-copy"},
        {"doc_kind": "system_card", "card_date": "2025-02-24", "wayback_first_200": "20250224184553", "card_url": "launch-copy"},
    ]
    assert fetch.pick_primary(rows, "2025-02-24")["card_url"] == "launch-copy"


def test_pick_tie_on_date_prefers_richer_kind():
    rows = [
        {"doc_kind": "github_card", "card_date": "2023-07-18", "card_url": "gh"},
        {"doc_kind": "tech_report", "card_date": "2023-07-18", "card_url": "paper"},
    ]
    assert fetch.pick_primary(rows, "2023-07-18")["card_url"] == "paper"


def test_pick_pre_launch_card_when_none_in_window():
    rows = [
        {"doc_kind": "tech_report", "card_date": "2023-12-06", "card_url": "report"},
        {"doc_kind": "model_card", "card_date": "2024-06-01", "card_url": "late"},
    ]
    assert fetch.pick_primary(rows, "2024-02-08")["card_url"] == "report"


def test_ranked_candidates_give_fallbacks_in_order():
    rows = [
        {"doc_kind": "hf_card", "card_date": "2026-04-24", "card_url": "readme"},
        {"doc_kind": "tech_report", "card_date": "2026-04-24", "card_url": "dead-pdf"},
        {"doc_kind": "tech_report", "card_date": "2026-04-26", "card_url": "arxiv"},
    ]
    assert [r["card_url"] for r in fetch.ranked_candidates(rows, "2026-04-24")] == ["dead-pdf", "arxiv", "readme"]


def test_launch_status_falls_back_to_effective_date():
    s = fetch.launch_status("2025-09-29", card_date="", capture_ts="", date_eff="2025-09-29")
    assert s["card_at_launch"] == 1 and s["launch_version_unverified"] == 1


def test_redirect_target_from_wayback_location():
    loc = "https://web.archive.org/web/20250929172200id_/https://assets.anthropic.com/m/12f2/original/Card.pdf"
    assert fetch.original_from_location(loc) == "https://assets.anthropic.com/m/12f2/original/Card.pdf"
    assert fetch.original_from_location("https://assets.anthropic.com/x.pdf") == "https://assets.anthropic.com/x.pdf"
    rel = "/web/20260901180542id_/https://www.anthropic.com/document/card.pdf"
    assert fetch.original_from_location(rel) == "https://www.anthropic.com/document/card.pdf"


def test_cdx_query_encodes_ampersand():
    q = fetch.cdx_query("https://www-cdn.anthropic.com/x/Claude%20Fable%205.1%20&%20Mythos.pdf")
    assert "Fable%205.1%20%26%20Mythos.pdf&output=json" in q


def test_decompress_zstd_and_gzip():
    import gzip, subprocess
    raw = b"%PDF-1.7 hello"
    z = subprocess.run(["zstd", "-c", "-q"], input=raw, capture_output=True).stdout
    assert fetch.decompress(z) == raw
    assert fetch.decompress(gzip.compress(raw)) == raw
    assert fetch.decompress(raw) == raw


def test_printed_date_from_card_text():
    assert fetch.printed_date("Muse Spark Safety Report\nDate: April 14, 2026\n") == "2026-04-14"
    assert fetch.printed_date("Grok 4 Model Card xAI Last updated: August 20, 2025") == "2025-08-20"
    assert fetch.printed_date("System Card: Claude Sonnet 4.5 September 2025") == ""


def test_normalise_date():
    from cards import merge
    assert merge.norm_date("2024-03-08 (arXiv v1 of the same report)") == "2024-03-08"
    assert merge.norm_date("undated (launch-day upper bound)") == ""
    assert merge.norm_date("not printed (upper bound 2023-11-05)") == ""


def test_arxiv_abs_maps_to_pinned_v1_pdf():
    from cards import merge
    assert merge.canonical_url("https://arxiv.org/abs/2303.08774") == "https://arxiv.org/pdf/2303.08774v1"
    assert merge.canonical_url("https://arxiv.org/abs/2303.08774v3") == "https://arxiv.org/pdf/2303.08774v1"
    assert merge.canonical_url("https://huggingface.co/a/b/blob/main/r.pdf") == "https://huggingface.co/a/b/resolve/main/r.pdf"


def test_search_tokens_ignore_sources_marked_not_run():
    from cards import merge
    got = merge.search_tokens("Live guesses 404; Epoch product page checked; Wayback not run for these URLs", "")
    assert "wayback" not in got
    got = merge.search_tokens("Epoch Reference 'Introducing Magistral' (not fetched); arXiv none; Wayback CDX on sibling", "")
    assert "announcement" not in got and "wayback" not in got and "arxiv" in got


def test_search_tokens_from_free_text():
    from cards import merge
    got = merge.search_tokens("announcement bytes; HF/GitHub/arXiv not linked; Wayback CDX on announcement", "https://x.ai/blog/a")
    assert got == {"lab", "announcement", "hf", "github", "arxiv", "wayback"}


def test_pinned_any_url_with_commit_sha():
    from cards import merge
    r = merge.pin({"card_url": "https://huggingface.co/deepseek-ai/DeepSeek-V2-Chat/raw/896a24c2ddb90143bc8eeba56eb55bc4334d234f/README.md",
                   "card_date_src": "HF commits API: commit 896a24c2 dated 2024-05-06T09:00:00Z", "card_date": "2024-05-06"})
    assert r[0].endswith("/README.md") and r[1] == "2024-05-06"


def test_pinned_hf_resolve_at_commit():
    from cards import merge
    r = merge.pin({"card_url": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/5c449c2f36b66f448ebf8e68add19d8b555d5c9b/DeepSeek_V4.pdf",
                   "card_date_src": "commit 5c449c2f36b66f448ebf8e68add19d8b555d5c9b committed 2026-04-24T02:50:24Z", "card_date": "2026-04-24"})
    assert r == ("https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/5c449c2f36b66f448ebf8e68add19d8b555d5c9b/DeepSeek_V4.pdf", "2026-04-24")


def test_pinned_hf_and_github_commits():
    from cards import merge
    hf = merge.pin({"card_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3", "card_date_src":
                    'HF commit dd31960ee457249502f7c6a652a30ff78e9fc792 "Release DeepSeek-V3", 2024-12-26', "card_date": "2024-12-26"})
    assert hf == ("https://huggingface.co/deepseek-ai/DeepSeek-V3/raw/dd31960ee457249502f7c6a652a30ff78e9fc792/README.md", "2024-12-26")
    gh = merge.pin({"card_url": "https://raw.githubusercontent.com/meta-llama/llama3/bb55334adcedfa9f5da66d2e1ed64e6f3dbd82ed/MODEL_CARD.md",
                    "card_date_src": "commit bb55334adcedfa9f5da66d2e1ed64e6f3dbd82ed committed 2024-04-19T13:51:06Z", "card_date": "2024-04-18"})
    assert gh == ("https://raw.githubusercontent.com/meta-llama/llama3/bb55334adcedfa9f5da66d2e1ed64e6f3dbd82ed/MODEL_CARD.md", "2024-04-19")


# ---- acceptance: the real manifest ---------------------------------------------

def _manifest():
    assert MANIFEST.exists(), "cards/manifest.csv not built yet"
    return list(csv.DictReader(MANIFEST.open(encoding="utf-8")))


def _releases():
    return {r["release_id"]: r for r in csv.DictReader((ROOT / "releases" / "frontier.csv").open(encoding="utf-8"))}


def test_at3_every_release_accounted_for():
    rows = {r["release_id"]: r for r in _manifest()}
    rel = _releases()
    assert set(rows) == set(rel), (sorted(set(rel) - set(rows))[:10], sorted(set(rows) - set(rel))[:10])
    for rid, r in rows.items():
        if not r["sha256"]:
            got = {s.strip() for s in r["search_log"].split(";") if s.strip()}
            assert SEARCH_SOURCES <= got, (rid, sorted(SEARCH_SOURCES - got))


def test_at4_cached_bytes_match_manifest():
    for r in _manifest():
        if r["sha256"]:
            p = fetch.cache_path(r["sha256"], r["card_url"])
            assert p.exists(), (r["release_id"], str(p))
            assert hashlib.sha256(p.read_bytes()).hexdigest() == r["sha256"], r["release_id"]


def test_at5_launch_version_claims_are_backed():
    rel = _releases()
    for r in _manifest():
        if r["card_at_launch"] == "1" and r["launch_version_unverified"] == "0":
            launch = rel[r["release_id"]]["available_date"]
            # spec AT5: "capture_ts or a source date no later than launch + 2"
            dates = [d for d in (r["card_date"], fetch.ts_date(r["capture_ts"]) if r["capture_ts"] else "") if d]
            assert dates, r["release_id"]
            assert fetch.days_between(launch, min(dates)) <= fetch.GRACE_DAYS, (r["release_id"], launch, dates)


def test_extracted_text_is_not_garbled():
    for r in _manifest():
        if r["sha256"]:
            assert int(r["words"]) > 0, r["release_id"]
            if r["pages"] and int(r["pages"]) > 0:
                assert int(r["words"]) / int(r["pages"]) >= 40 or r["text_flag"], r["release_id"]


ARXIV_CHROME = re.compile(r"\[\d{4}\.\d{4,5}(v\d+)?\]")


def _text(r):
    return Path(r["text_path"]).read_text(encoding="utf-8", errors="replace") if r["text_path"] else ""


def test_card_signal_not_landing_or_binary():
    for r in _manifest():
        if not r["sha256"]:
            continue
        t = _text(r)
        head = t[:1500]
        assert not (ARXIV_CHROME.search(head) and "Skip to main content" in head), (r["release_id"], "arXiv abstract page")
        assert "/blob/" not in r["card_url"], (r["release_id"], "HF file viewer")
        sample = t[:20000]
        bad = sum(1 for ch in sample if ch == "\ufffd" or (ord(ch) < 32 and ch not in "\n\r\t\f"))
        assert bad <= 0.01 * max(1, len(sample)), (r["release_id"], "binary text", bad)
        if r["doc_kind"] in {"system_card", "tech_report"}:
            assert int(r["words"]) >= 1500, (r["release_id"], r["words"])


def test_regressions_from_track_b_review():
    m = {r["release_id"]: r for r in _manifest()}
    assert m["xai-2023-11-04-grok-1"]["card_at_launch"] == "1"
    assert m["deepseek-2026-04-24-deepseek-v4-pro"]["launch_version_unverified"] == "0"
    assert m["deepseek-2026-04-24-deepseek-v4-pro"]["card_url"].endswith("DeepSeek_V4.pdf")
    assert m["deepseek-2025-01-20-deepseek-r1"]["card_url"].endswith("DeepSeek_R1.pdf")
    for rid in ["anthropic-2026-09-01-claude-fable-5-1", "anthropic-2026-09-22-claude-opus-5-5",
                "anthropic-2023-11-21-claude-2-1", "anthropic-2025-02-24-claude-3-7-sonnet", "anthropic-2025-08-05-claude-opus-4-1"]:
        assert m[rid]["source"] == "wayback" and m[rid]["launch_version_unverified"] == "0", rid
        assert m[rid]["card_url"].startswith("http"), rid
    assert int(m["mistral-2026-10-06-mistral-large-4"]["card_days_after_launch"]) >= 20
    assert m["google-2025-03-25-gemini-2-5-pro-mar-2025"]["card_days_after_launch"] == "22"
    assert m["anthropic-2025-09-29-claude-sonnet-4-5"]["source"] == "wayback"
    assert "o1-system-card" in m["openai-2024-09-12-o1-preview"]["card_url"]
    assert m["openai-2024-09-12-o1-preview"]["card_url"].endswith(".pdf")
    assert m["openai-2025-08-07-gpt-5"]["card_url"].endswith(".pdf")
    assert m["meta-2026-04-08-muse-spark"]["card_date"] == "2026-04-14"
