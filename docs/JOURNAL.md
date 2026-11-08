# JOURNAL

## Snapshot (rewritten each wave)

- Stage: DONE 2026-11-08; final review findings fixed. All four tracks complete; methods, charts, codes final.
- Final codes: coding/codes.csv = max(text pass codes_v11.csv, agreed supplement). Supplement: 54 extra launch docs over 33 releases, 1,402 rendered pages, 592 codes, 2 disagreements adjudicated, kappa 0.966, 9 codes raised.
- Headline: any dangerous-capability result at launch 20% (H1 23) to 71% (H2 26); outside testing 20-50%, 41% latest; 63 of 87 cards at launch, 10 late, 14 never; labs any-DC Anthropic 14/17, OpenAI 12/15, Google 5/13, Meta 5/11, xAI 3/11, DeepSeek 1/9, Mistral 0/11.
- Tests: 69 passed; analysis.verify_claims 30 of 30; prose-check PASS on docs/methods.md.
- Repo: local only, branch owizdom/tide-tracks-a-b, no remote.

## Evidence (append only)

### 2026-11-05 reading pass

- Epoch export `~/Desktop/ai_models.zip`, sha256 `a31aafbf290549655ca57ef4d6f207cdc9bc036dfbde183c14ba5114323d6ee4`, holds `all_ai_models.csv` (3,708 rows), `notable_ai_models.csv` (1,092), `large_scale_ai_models.csv` (534), `frontier_ai_models.csv` (138). Row counts from csv.DictReader.
- Epoch documentation (epoch.ai/data/ai-models-documentation, fetched 2026-11-05): "Frontier models are models that were in the top 5 of training compute as of the time of their release." Large-scale is at least 1e23 FLOP.
- Epoch frontier subset from 2023: 30 models, 0 Mistral, 0 DeepSeek, last entries Grok 4 (2025-07-09) and GPT-6 Astra (2026-09-03).
- Mechanical filter over notable plus large-scale (script in session scratchpad, rule_M): 93 launch events, all 7 labs, all 8 half-years. Missing from both subsets but present in the full database: GPT-5.6 Sol/Terra/Luna, Grok 4.5, Grok 4.6, Gemini 3.6 and 3.7 Flash, Claude Sonnet 5.
- FMTI repo cloned at `f4500c5f4763966fddf71c468a148533a1236290` (2025-12-09). Dec 2025 edition: 100 indicators, 13 companies, mean score 41. Indicators 47 to 58 cover risks, mitigations and risk thresholds; FMTI scores one flagship per company, not releases.
- Free Systems post "Model Cards: collect 'em all", post_date 2026-09-10: 22 cards, about 476,000 words, average about 30,700 words per system card; explorer at modelcards.freesystems.net. It proposes a common model card with questions on external evaluators, safeguards and unreported areas.
- Wayback CDX works from this machine. `data.x.ai/2025-08-20-grok-4-model-card.pdf`: first capture 2025-08-21 (status "-"), first 200 capture 2025-08-22 (digest PMZ5…), digest AJF4… by 2025-08-28.
- Hugging Face commits API for `meta-llama/Llama-3.1-405B-Instruct` returns "Access to model ... is restricted" without login.
- ai-research-model-cards `data/dataset/documents.csv` at `3b02160`: 90 documents, 6 labs, no DeepSeek. URLs are current versions, not launch versions.

### 2026-11-05 Track A draft

- Approval answers: frontier rule "Version-flagship", coding "2 Claude passes + audit", chart "Free Systems house".
- Tier evidence from Epoch abstracts (all_ai_models.csv): Claude Fable 5 "a Mythos-class model ... capabilities exceed those of any model we've ever made generally available"; Claude Opus 5 "comes close to the frontier intelligence of Claude Fable 5 at half the price"; Claude Mythos Preview accessibility note "Not available to the general public"; GPT-6 Sol/Luna "the most demanding and important projects still call for Astra's full depth"; GPT-6.1 Sol "an upgrade to GPT-6 Sol that nearly matches GPT-6 Astra's intelligence"; Gemini 4 Argon "Limited access"; Gemini 4 Carbon "Unreleased as of October 28 2026"; Muse Glimmer "a 30-billion-parameter model optimized for always-on local agent workflows".
- Unverified tier assumptions marked "review" in ladders.yaml: GPT-5.6 Sol over Terra over Luna, GPT-6.1 Terra below Sol, Muse Wonder Full above Wonder, GPT-4V and Llama 3.2/3.3 and Mistral 7B and Pixtral Large treatment.
- Epoch data issue: "Operator" dated 2023-01-23 (excluded as AGENT_PRODUCT either way).
- Tests: red first (ImportError, no rule module), then 14 passed after rule.py and ladders.yaml.

### 2026-11-05 Track A review and freeze

- Fresh reviewer (Opus 5.5, claude-opus-5-5): 9 in-scope findings, all checked against Epoch rows before fixing. Fixed: o3 dated 2025-04-16 (its abstract is the o3/o4-mini release text); Gemini 1.0 Ultra 2024-02-08 and Gemini 2.0 Pro 2025-02-05 from blog.google datePublished, so 1.0 Pro and 2.0 Flash lead their launch days; GPT-4V and Llama 3.2 90B out as vision variants (same as Pixtral Large, Grok-1.5V); Mistral Large 2.1 out as a snapshot of Large 2; Magistral Medium 1.1 and 1.2 in as reasoning models (same as DeepSeek-R1); Facebook AI Research rows added to the Meta pattern (4 new candidates, none included); AT1 now reads the hash from this JOURNAL; AT2 test added; sensitivity file `releases/sensitivity_epoch_subsets.csv` written (98 events).
- Wisdom's decision: previews count once, at the preview. o1 and DeepSeek-V3.2 become snapshots.
- Out-of-scope follow-ups, not fixed: the checker does not verify non-relative exclusions or LOWER_TIER across versions; V4 Flash 0731 refs V4-Pro; PaLM-2 Unicorn coded LOWER_TIER at equal tier; GPT-6.1 Terra tier order assumed; SAME_EVENT-only day would crash build_events; extra event_models column; duplicate YAML keys within a lab are not detected.
- FREEZE frontier.csv sha256 51dce3f1e6b098d9d1c43b9ad8ef77fb0e0258295d3d328c49435dbf2172c59f at 2026-11-05T12:51:00Z

### 2026-11-05 Track B

- Scouts (4, model claude-haiku-5-5 as each reported): raw CSVs in `cards/discovery/raw/` (anthropic_mistral 32 rows, google_meta 34, openai_deepseek 37, xai 17). Wayback answered the parallel scouts with HTTP 429 and refused connections; several launch-day captures stayed unread by the scouts.
- My correction: I had added search-source tokens to four xAI search logs that the scout never wrote; removed before merging. Search tokens now come only from scout text (`cards/merge.py`). The 11 releases missing a required search were searched by me (arXiv API, GitHub org listings, HF model search, lab pages), logged in `raw/zz_gapfill.csv`. Found: arXiv "Muse Spark Safety & Preparedness Report" (2026-05-14).
- Rule changes in fetch.py, each with a test: primary card = latest card dated by launch + 2, else earliest later card (GPT-5.6 has a 2026-06-25 preview card); publication date = earlier of printed date and first capture (Muse Spark report archived 2026-04-14, prints 2026-05-26); AT5 test aligned to the spec wording "capture_ts or a source date".
- Fetch run: 87 rows; sources wayback 56, live 9, commit 8, none 14; 19 cards flagged launch_version_unverified. Gemini 1.0 report failed once (connection refused) and succeeded on `--only` retry.
- Preliminary, unreviewed: card_at_launch by half 2/5, 5/8, 7/10, 6/8, 7/12, 11/14, 10/13, 14/17 (2023H1 to 2026H2).

### 2026-11-05 Track B reviews

- Review 1 (Opus 5.5): 19 of 87 rows on the wrong document or version, tests green. Earlier preliminary card-at-launch numbers RETRACTED to the user. Fixes: arXiv abs -> v1 PDF; HF blob -> resolve; launch-window pick; undated cards dated by first capture; redirect following; CDX errors raise instead of live fallback; zstd/gzip decompress; printed date from coded bytes; search tokens ignore "not run"; card-signal test. Wisdom: docs spec pages are not cards.
- Review 2 (Opus 5.5): 9 of 11 fixed; new N1-N6 (relative redirect Location, missed launch-day Anthropic copies, DeepSeek R1 and V4-Pro launch PDFs at commits, Mistral Large 4 placeholder capture, April Gemini 2.5 Pro card). All fixed with per-release regression tests; also CDX query encoding of '&' (Fable 5.1). No third review round: regressions are asserted per release; the final review covers Track B again.
- Pinned Epoch zip left ~/Desktop (copies in ~/Downloads and Trash, both sha256 a31aafbf...); vendored at releases/epoch/ai_models.zip.

### 2026-11-05 Track C pilot and main pass start

- Pilot: pass A Opus 5.5 and pass B Sonnet 5.5 on 10 releases (coding/pilot_ids.txt). AT6 and AT7 clean. 130 codes, 7 disagreements; kappa ext_test_any 0.60, ext_test_named_org 0.60, safeguards_weights 0.62, ext_test_government 0.74, safeguards_runtime 0.78, dc_eval_autonomy 0.82, the rest 1.00. Both pilot coders keyword-scanned parts of the three longest cards; the main brief forbids that.
- Wisdom: outside testing counts unless the card says it came after release; new flag ext_test_timing_stated carries the strict reading. Codebook v1 frozen with boundary rules from the pilot. Pilot passes archived in coding/pilot/passes_v0.
- Main pass: 73 cards, 1,235,825 words, 12 groups of about 103k words (coding/groups/), wave 1 = groups 1-3 for A (Opus) and B (Sonnet). Wisdom approved the token cost.

### 2026-11-05 usage limit

- Wave 1 (6 agents) took the 5-hour session from 89% to the cap at about 17:30; groups 2 and 3 were stopped at 94% to give group 1 room, and group 1 hit the limit before writing. On disk at 19:21: pass A 7 valid files (g02 3, g03 4), pass B 2 (g03). Resumed at 19:21: g01 and g02, both passes, via the same agents (context kept). Concurrency 4. Remaining: g03 rest, g04-g12.
- Independence note: coder A (g02) reported that a coder B helper script overwrote its helper w.py in the shared scratchpad; A says it read no B output and moved to its own folder. Brief amended: per-coder scratch folders. Disclose in methods.
- CONTAMINATION found 2026-11-05 ~19:45: pass B files for claude-2-1 (14/14 notes identical to A) and o3 (13/14) were produced from A's files (A written 17:29, B 19:24; shared scratchpad helper scripts the likely route). Both B files plus B opus-4-8 (coder admitted keyword-scanning most of 8,277 lines) moved to coding/quarantine/B/ and recoded by a fresh isolated B coder (coding/groups/r01_recode_B.txt). New test test_passes_are_independent fails if a release pair shares 4+ identical notes.
- Also quarantined pass A claude-2-1 and o3 (coder A reported its claude-2-1 file was rewritten on disk by another process); recoded by a fresh isolated A coder (coding/groups/r01_recode_A.txt).
- v1.1 clarifications (addenda: Wisdom; outside testing = safety testing). Pass B shortcut long cards three times (Sonnet with ~100k-word groups); remaining B work split so any card over 25k words gets its own agent (coding/groups_B/). Recodes: r02 (both passes: gpt-5-1, gpt-5-2, grok-4-5, grok-4-7; B also claude-2-1, gemini-1-0-pro, opus-4-7). norm() now strips zero-width characters.
- B g10S filtered Claude 3.7 Sonnet lines 960+ to prose >=60 chars; added to B recode r02.
- Wisdom 2026-11-07: age gates are not safeguards_access (codebook clarification 3, applied at adjudication).

### 2026-11-07 coding complete
- Both passes cover 73 cards. tests/test_coding.py 9 passed (AT6 quotes, independence). Agreement over 1,022 codes: 18 disagreements; kappa cbrn 0.976, cyber 0.973, autonomy 0.973, persuasion 0.944, scheming 0.972, framework 1.000, ext_any 0.945, ext_named 1.000, ext_gov 1.000, ext_timing 0.940, sg_training 0.966, sg_runtime 0.972, sg_access 0.833, sg_weights 0.920. Session usage 30%, week 19% at this point (premium plan).
- PaLM 2 primary moved to Google's launch-day copy (2023-05-10); it lacks the arXiv v1 runtime-monitoring sentence, so PaLM 2 is recoded on the launch text (old passes in coding/quarantine/palm2_v1).

### 2026-11-08 final merge and write-up

- Supplement merge: raised 9 (Opus 4 persuasion 1->2, access 0->1; Gemini 3 Pro ext_any, timing, weights 0->1; Llama 3.1 cbrn 1->2, cyber 1->2, ext_any 0->1; Llama 3 70B timing 0->1 adjudicated); DeepSeek V3 safeguards_training adjudicated 0.
- Four launch documents of no-card releases were never coded (secondary.py skips releases without a primary card): Muse Spark, 1.2 and 1.3 eval-method notes and the Grok 4.5 training-data summary. Captured and read 2026-11-08: none reports any item (capability benchmark method and data provenance only). Recorded in methods.
- Methods rewritten to the final numbers; charts reworded from "card" to "launch documents"; verify_claims extended to supplement statistics (30 of 30).

### 2026-11-08 final review (Opus 5.5, claude-opus-5-5)

- Recompute matched every headline number; 69 passed; verify_claims 30 of 30.
- Fixed in scope: (1) Llama 3.1 arXiv v1 stand-in (+8 days) now stated as a method choice with its sensitivity (Meta 4 of 11, all 39 of 87, H2 2024 25% to 12% on both lines); (2) candidate documents 177 with a URL, not 208 rows; (3) supplement files committed, the four no-card launch documents recorded in cards/no_card_launch_docs.csv, methods states documents are pinned by URL, capture and sha256 with bytes re-fetchable; (4) Llama 3 70B timing described as an adjudicated card sentence, with the release-decision tie that separates it and Gemini 3 Pro from GPT-4.5; (5) chart footers scope the 80-code check to text-pass codes. Also GPT-4 case study: ARC is the one named organisation.
- AT8 hand audit: replaced by the independent 80-code Claude check at Wisdom's instruction on 2026-11-07 ("those 80 questions please answer them yourselves and finish this task up fast").
- Out of scope, not changed: Opus 4 persuasion 2 rests on a behavioural-audit manipulation score; DeepSeek V4.1 Flash cyber 2 rests on CyberGym/ExploitGym results without risk framing.

### 2026-11-08 review round 2 (Opus 5.5, claude-opus-5-5)

- Independent recompute matched every number, including the Llama 3.1 sensitivity. 69 passed; 30 of 30.
- Fixed: methods no longer states a timing rule absent from the codebook; it reports what each pass coded under codebook line 35. The Grok 4.5 training-data summary's "filtered for quality and safety" and its post-window first capture are now stated in methods and cards/no_card_launch_docs.csv (no figure changes: no card at launch).
- Out of scope: stand-in capture_ts in secondary.csv shows launch day; round-half-even shows 1/8 as 12%; verify_claims does not assert the sensitivity numbers; two secondary docs first captured after launch + 2 add no positive code.

### 2026-11-08 review round 3 (Opus 5.5, claude-opus-5-5)

- Fixed: GPT-4.5 timing sentence now quotes the card's "prior to deployment" sentence and states the text-pass split and adjudication; Gemini 3 Pro's 1 is attributed to the figure and extra-document pass. Methods now gives the Grok 4.5 summary's first capture (11 July 2026), which the round 2 entry claimed it did.
