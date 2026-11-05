# Spec 0001: release-by-release safety disclosure series

- **Status:** APPROVED 2026-11-05 (rule A version-flagship, two quote-gated Claude passes plus a 15-release hand audit, Free Systems house chart style)
- **Owner:** architect (Opus 5.5)
- **Brief:** Free Systems Challenge 4, "Are labs disclosing more or less with each model release?"
- **Builds on:** the Model Cards post (freesystems.substack.com/p/model-cardscollect-em-all, 2026-09-10) and owizdom/ai-research-model-cards

## 1. Objective

Answer one question with a release-level dataset: across frontier releases from 2023 to October 2026, did model and system cards disclose more or less about risks, dangerous-capability evaluations and safeguards, and is that disclosure concentrating in a few labs?

Done means all of the following exist and pass section 5:

1. `releases/frontier.csv`: the frozen list of frontier releases, produced by a script from the pinned Epoch export and the rule in section 1.1. It is frozen and hashed before any card is fetched.
2. `cards/manifest.csv`: for every release, the card as it stood at launch (archive URL, capture timestamp, sha256 of the bytes), or a logged search that found no card.
3. `coding/codes.csv`: one row per release with the variables in section 1.2, every positive code backed by a verbatim quote that appears in the archived text.
4. `analysis/out/share_by_half.png`: the share of frontier releases disclosing each item, by half-year, covering at least 5 labs. A lab-by-half heatmap answers the concentration part.
5. Stretch: 2 or 3 case studies of a drop in disclosure between successive releases of one lab, picked by the rule in section 1.3.

### 1.1 Frontier release (decided before collection, never changed after)

Epoch's own "frontier" subset is defined as the top 5 by training compute at release (epoch.ai/data/ai-models-documentation, fetched 2026-11-05). It cannot carry this study alone. From 2023 it holds 30 models, 0 from Mistral or DeepSeek, and nothing after Grok 4 except GPT-6 Astra, because recent flagships have no compute estimate.

Proposed rule (option A in the approval question):

- Universe: Epoch `all_ai_models.csv`, export of 2026-11-05 (zip sha256 `a31aafbf…3d6ee4`).
- Labs: Anthropic, OpenAI, Google and Google DeepMind, Meta, xAI, Mistral, DeepSeek.
- Window: publicly available between 2023-01-01 and 2026-10-31.
- Model: general-purpose language or multimodal model, publicly usable at launch (API, consumer product or open weights). Epoch "Unreleased" is out.
- Flagship: the release is the top tier of a new version from that lab, using a per-lab tier ladder written into `releases/ladders.yaml` before the list is generated. A lower tier of a version already counted is out (Sonnet 4.6 after Opus 4.6). A higher tier of a counted version is in (Opus 4.5 after Sonnet 4.5).
- Out by rule: dated re-snapshots of a counted name (GPT-4o Aug 2024); inference-time modes of a counted model (Pro, Deep Think, Thinking); domain variants (Codex, Cyber, Math, Coder, image, voice); secondary small open lines while the lab has a larger flagship line (Gemma); third-party fine-tunes.
- Previews: a preview or experimental release and the later general release of the same model count once, at the first public release (Wisdom, 2026-11-05). Vision variants of a counted text model are out as domain variants.
- Unit: one launch event per lab per day. A card covering several models on one day counts once.
- Date of record: the date the model became publicly usable. Epoch's publication date can be an announcement date. Where the two differ, both are kept and the difference is logged with its source.

Expected size: about 80 to 100 launch events. A mechanical filter over Epoch's notable and large-scale subsets gave 93 events across all 7 labs and all 8 half-years (2023H1 to 2026H2). It was rejected as the main rule because Epoch's 2026 notability tags lag: GPT-5.6, Grok 4.6, Gemini 3.6 and 3.7 Flash and Claude Sonnet 5 sit in the full database but in neither subset. It is kept as a sensitivity check.

Wisdom approves the generated list, release by release, before any card is fetched. After that the list only changes for a factual error (a wrong date or lab), logged in the JOURNAL with the evidence.

### 1.2 Variables per release

Each is coded from the card as available at launch. "Card" means a document from the developer about this model or its family: a system card, model card, technical report, or Hugging Face or GitHub model card. An announcement blog post alone is coded as `announcement_only`, not as a card. A product documentation page (for example a docs.mistral.ai model spec page) is not a card either (Wisdom, 2026-11-05).

| Variable | Coding | Aligned with |
|---|---|---|
| `card_at_launch` | card public no later than launch day + 2 | FMTI 44, 48 ("concurrent with release") |
| `card_ever`, `card_days_after_launch` | first card by 2026-10-31, and its lag in days | brief |
| `dc_eval_{cbrn,cyber,autonomy,persuasion,scheming}` | 0 not mentioned, 1 domain named without a result, 2 result reported on this model | FMTI 47, 48 |
| `ext_test_any`, `ext_test_named_org`, `ext_test_government` | testing by outsiders, a named organisation, a government body (US CAISI or AISI, UK AISI, other), counted unless the card says it came after release | FMTI 50, 51 |
| `ext_test_timing_stated` | the card states some outside testing happened before release | brief ("pre-deployment") |
| `framework_threshold` | 0 none, 1 framework named, 2 the model's position against a named threshold stated (ASL-3, "High", a CCL) | FMTI 58 |
| `safeguards_{training,runtime,access,weights}` | safety training, runtime classifiers or monitoring, access restrictions, weight security | FMTI 52, 56, 88 to 90 |
| `card_words`, `card_pages` | length of the launch version | brief; reported apart, never scored |
| `card_updated_after_launch`, `update_dates` | content digest changed after launch | brief |

The chart counts an item as disclosed when the code is 2 for three-level items and 1 for binary ones. "Card length is not quality" holds in the data model: length never enters a disclosure share or index.

Launch version: the earliest retrievable bytes captured no later than launch + 2 days. Sources in order are the Wayback Machine raw capture (`id_` mode, which avoids live-subresource leakage), the Hugging Face or GitHub commit at launch, arXiv v1, and the lab's own dated PDF. A card whose first capture is later than launch + 2 is coded `card_at_launch = 0`. Its content is still coded from the earliest version, flagged `launch_version_unverified`. A first Wayback capture is only an upper bound on the publication date. A date printed in the card or in the announcement that links it takes precedence when one exists.

### 1.3 Case-study rule (stretch)

A drop is any item that goes from disclosed to not disclosed between two successive frontier releases of the same lab. Case studies are the 2 or 3 drops covering the most items, ties broken by the later date. They are picked from the coded data, never by reputation.

## 2. Non-goals

- Capability benchmarks and scores. The explorer covers those.
- Judging whether an evaluation was adequate. This study records what was disclosed, not whether it was good.
- A composite disclosure score or ranking. Shares per item only.
- Re-scoring FMTI, or company-level documents (frameworks, usage policies) as disclosures. They count only when a card references them.
- Labs beyond the 7, and non-language models.
- Any write to the ai-research-model-cards database. Its `.env` points at Railway production, so only its exported CSVs are read.
- A website. The deliverable is data, a chart and a methods note.

## 3. Stack

New private repository `~/Desktop/code/tide`, flat domain folders. Card bytes live in a gitignored cache, `~/.tide-cache/`. Only manifests and hashes are committed.

```
releases/   rule.py, ladders.yaml, frontier.csv, sensitivity_epoch_subsets.csv
cards/      discover.py, fetch.py (Wayback CDX, HF, GitHub, arXiv), extract.py (pdftotext), manifest.csv
coding/     codebook.md, code.py (two independent passes), quotes.py, audit.csv, codes.csv
analysis/   shares.py, plot.py, cases.py, verify_claims.py, out/
docs/       specs/, TASKS.md, JOURNAL.md, methods.md
tests/
```

Inputs pinned: Epoch export zip sha256 `a31aafbf290549655ca57ef4d6f207cdc9bc036dfbde183c14ba5114323d6ee4`; FMTI repo at `f4500c5`; card URLs seeded from ai-research-model-cards `data/dataset/documents.csv` (90 rows, read at `3b02160`).

## 4. Seam contract

```
releases/frontier.csv   release_id, lab, model, epoch_name, epoch_date, available_date, tier, rule_reason
cards/manifest.csv      release_id, card_url, source, archive_url, capture_ts, sha256, bytes, text_path, launch_version_unverified, search_log
coding/codes.csv        release_id, <section 1.2 variables>, coder, pass
coding/quotes.csv       release_id, variable, value, quote, locator, sha256
```

`release_id` is `<lab>-<available_date>-<slug>` and never changes once the list is frozen.

## 5. Acceptance tests

T = automated. L = live run with a recorded artifact.

| # | Test | Type | Passes when |
|---|---|---|---|
| AT1 | Frontier list is reproducible | T | `rule.py` on the pinned zip and `ladders.yaml` reproduces `frontier.csv` byte for byte, and its sha256 matches the one logged at freeze |
| AT2 | Freeze precedes collection | T | the JOURNAL freeze entry and the list hash predate every `capture_ts` fetch time in the manifest |
| AT3 | Every release is accounted for | T | each `release_id` has a manifest row with a card, or a search log covering lab site, announcement, Hugging Face, GitHub, arXiv and Wayback CDX |
| AT4 | Bytes match | T | re-hashing every cached file reproduces `sha256` in the manifest |
| AT5 | Launch version | T | every `card_at_launch = 1` has `capture_ts` or a source date no later than launch + 2, otherwise it carries the flag |
| AT6 | No invented evidence | T | every positive code has a quote found verbatim (whitespace-normalised) in the extracted text of the cited snapshot |
| AT7 | Zeros are checked | T | any 0 whose domain keywords occur in the text carries a reviewer note |
| AT8 | Coding agreement | L | two independent passes agree per variable at Cohen's kappa of at least 0.7, and Wisdom's hand audit of 15 stratified releases agrees with the final codes at the same bar. A variable below the bar is reported as unreliable, not silently kept |
| AT9 | Coverage | T | at least 5 labs, each with at least one release in at least 6 of the 8 half-years, or the gap is stated on the chart |
| AT10 | Chart from data | T | one command rebuilds the PNG from `codes.csv`, and each cell shows its n |
| AT11 | Claims match data | T | `verify_claims.py` asserts every number in `methods.md` and any write-up against `codes.csv` |
| AT12 | Tripwire | T | the suite fails on 0 tests run or any skip |

## 6. Tracks

| Track | Owns | Depends on | AT |
|---|---|---|---|
| A frontier list | `releases/` | Wisdom's rule choice | AT1, AT2 |
| B cards | `cards/` | A frozen | AT3, AT4, AT5 |
| C codebook and coding | `coding/` | B for text; codebook pilot on 10 releases first | AT6, AT7, AT8 |
| D analysis | `analysis/`, `docs/methods.md` | C | AT9, AT10, AT11 |

A runs alone and ends at the freeze gate. B and the codebook pilot in C then run in parallel. The codebook freezes after the pilot, before the main coding pass.

## 7. Pre-mortem: "it shipped and nobody trusted it; why?"

| # | Failure | Mitigation in this spec |
|---|---|---|
| 1 | The frontier list looks chosen to produce the finding | Rule and ladders written first, list frozen and hashed before any card is read (AT1, AT2), Epoch-subset sensitivity run published beside it |
| 2 | Recent half-years look thin because Epoch tags lag | Universe is the full database, not the notable subset |
| 3 | "At launch" codes actually read a later, edited card | Raw captures with timestamps and hashes, launch + 2 cutoff, unverified versions flagged (AT5). Wayback's first 200 capture of the Grok 4 card is 2025-08-22, 44 days after Epoch's 2025-07-09 date, and its digest changes by 2025-08-28 |
| 4 | Wayback replays pull live 2026 content into old captures (seen in plank) | `id_` raw mode only, hashes on raw bytes |
| 5 | The LLM coder invents a quote, or Claude checks Claude | Verbatim quote test (AT6), two independent passes, Wisdom's hand audit with kappa (AT8) |
| 6 | "Did not disclose" is wrong because the text layer of a 60,000-word PDF is garbled (the explorer hit this on Fable 5) | pdftotext with a page and character check, keyword screen on zeros (AT7) |
| 7 | 8 to 20 releases per half-year make shares noisy | n in every cell, Wilson intervals in the methods note, yearly pooling as a sensitivity check |
| 8 | Readers take long cards as better cards | Length is plotted apart and never feeds a share |
| 9 | Family cards (Claude 4 covers Opus 4 and Sonnet 4) double count | One launch event per lab per day |
| 10 | Gated Hugging Face repos block launch versions (Llama 3.1 405B returns "restricted") | GitHub history of meta-llama repos and Wayback as fallbacks |

## 8. Rollout, rollback, removal

- **Rollout:** local private repo, small commits per track after Wisdom's go. No push or publication without his explicit OK.
- **Rollback:** every output is regenerated from pinned inputs; deleting `analysis/out/` and `coding/codes.csv` returns to the frozen list.
- **Removal:** the Epoch-subset sensitivity file is removed only if the published methods note drops it.

## Approval questions

1. Frontier rule: A (version-flagship over Epoch's full database, list approved by Wisdom), B (mechanical Epoch notable and large-scale filter, 93 events), or C (Epoch's top-5 compute set only).
2. Coding: two quote-gated Claude passes plus a 15-release hand audit, or hand coding of everything.
3. Chart style: Free Systems house style or plain white.
