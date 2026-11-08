# Are labs disclosing more or less with each model release?

Free Systems Challenge 4. Data, code, and the source URL, archive capture and sha256 of every coded document: this repository (`tide`). `cards/fetch.py` and `cards/secondary.py` re-fetch the exact bytes.

## Findings

Far more frontier releases now launch with documents that report safety test results than in 2023. Releases whose documents, public at launch, report at least one dangerous-capability test result rose from 20% in the first half of 2023 to 71% in July to October 2026.

Outside testing has not kept pace. The share of releases whose launch documents report any outside safety testing moved between 20% and 50% across the eight half-years and stood at 41% in the latest one.

Disclosure is concentrated. Anthropic reported dangerous-capability results at launch for 14 of 17 frontier releases and OpenAI for 12 of 15. Google did so for 5 of 13, Meta for 5 of 11, xAI for 3 of 11, DeepSeek for 1 of 9 and Mistral for 0 of 11. Across all labs the figure is 40 of 87.

Cards are often late or missing. Of 87 frontier releases, 63 had a card public within two days of launch, 10 got one later (6 to 374 days after launch) and 14 never got one.

## Three drops between successive releases

The case rule was fixed before coding: an item counts as dropped when one release discloses it at launch and the same lab's next frontier release does not. The three largest drops, counted over the 14 items, ties going to the later release:

1. Meta, Muse Spark 1.1 to Muse Spark 1.2 (August 2026). Muse Spark 1.1 shipped with a 112-page evaluation report disclosing 13 of the 14 items, all but government testing. Muse Spark 1.2 shipped with an announcement and a note on how its capability benchmarks were run, and no card, so all 13 dropped. Meta's next release, Muse Spark 1.3, got its evaluation report 51 days after launch.
2. OpenAI, GPT-4.5 to GPT-4.1 (April 2025). GPT-4.5 launched with a system card reporting results in all five dangerous-capability domains and a Preparedness Framework determination. GPT-4.1 launched with an announcement only, and no card has appeared since. 10 of the 14 items dropped.
3. OpenAI, GPT-4 to GPT-4 Turbo (November 2023). GPT-4 launched with a technical report and system card covering all five domains and outside red teaming by experts and by a named organisation, the Alignment Research Center. GPT-4 Turbo launched with an announcement and no card. 10 of the 14 items dropped.

## What was measured

Frontier release. Each lab's top-tier general-purpose model at each new version, from Epoch AI's full AI models database (export of 5 November 2026, sha256 pinned in `releases/epoch/SOURCE.txt`). Seven labs: Anthropic, OpenAI, Google, Meta, xAI, Mistral and DeepSeek. The rule and every include or exclude decision (`releases/ladders.yaml`) were frozen before any document was fetched. The list has 87 releases from January 2023 to October 2026. Epoch's own frontier subset (top 5 by training compute) was not used because it has no Mistral or DeepSeek models and almost nothing after mid-2025.

Launch documents. Every developer document about the model that was public no later than two days after launch: system and model cards, card addenda, technical reports, Hugging Face and GitHub model cards (including the same model's base, instruct and quantized repositories), and model-specific safety reports whose main subject is the model's safety testing or safeguards. Announcement posts, product documentation pages, company-wide frameworks and documents about other models do not count. Each document was captured as it stood at launch: the earliest Wayback Machine capture, or the commit at launch for Hugging Face and GitHub. Two independent searches of every release found 177 candidate documents; every exclusion is logged with its reason in `cards/discovery/disc2_excluded.csv`.

Card at launch. A card (system card, model card, technical report or repository model card) public no later than two days after launch. Model-specific safety reports and evaluation notes count toward the items below but do not count as a card.

Items. Results in five dangerous-capability domains (bio, chemical or nuclear; cyber; autonomy or AI R&D; persuasion; deception or scheming), a framework threshold stated for the model, outside testing (any, named organisation, government, pre-release timing stated), and four kinds of safeguard (safety training, runtime, access restrictions, weight security). The codebook is `coding/codebook.md`. An item counts as disclosed at launch when any launch document reports it, in its text, tables or figures. A release with a late card or no card discloses nothing at launch. The four launch documents of such releases (three Meta notes on how capability benchmarks were run, and xAI's training-data summary for Grok 4.5) were read. None reports a test result, outside testing or a runtime or access safeguard; the Grok 4.5 summary, dated launch day but first archived on 11 July 2026, three days after launch, says its training data was "curated and filtered for quality and safety". None can change a figure, because these releases had no card at launch. They are listed in `cards/no_card_launch_docs.csv`.

Card length is reported separately in `cards/manifest.csv` and never enters a share.

## How the documents were coded

Text. Two coders coded every one of the 73 cards independently: pass A on Claude Opus 5.5, pass B on Claude Sonnet 5.5. Every code above zero carries a verbatim quote that a test finds in the archived document. Agreement across 1,022 codes was high, with Cohen's kappa between 0.83 and 1.00 for every item. The 18 disagreements were settled by a separate Claude instance that coded nothing, citing the codebook.

Figures, tables and extra documents. For every item below its top level, both passes then read 54 extra launch documents across 33 releases and looked at 1,402 rendered pages: every page that holds a figure and every page whose text mentions an open item. A figure or table result counts when cited by page, with its caption or label text from the document and a description. Across 592 item codes the two passes disagreed twice (kappa 0.966); a separate instance adjudicated both. Nine codes rose, all on evidence both passes found or the adjudicator confirmed: Claude Opus 4's persuasion result (a figure) and access restrictions (its launch-day ASL-3 report); Gemini 3 Pro's outside testing, pre-release timing and weight security (its launch-day Frontier Safety Framework report); Llama 3.1 405B's bio and cyber results and outside testing (its paper); and Llama 3 70B's stated pre-release timing (its card places an outside expert test inside the process that runs "before we make our release decision"; the adjudicator ruled on that sentence). The codebook asks whether a document states that outside testing happened before release. Gemini 3 Pro's launch-day safety report, read only in this pass, ties its outside testing to the deployment decision, and both coders coded it 1. GPT-4.5's card says "We conducted extensive safety evaluations prior to deployment" but ties no timing to METR or Apollo Research, saying only that METR "evaluated an earlier checkpoint"; the text passes split on it, the adjudicator ruled 0, and both coders here also coded 0.

Corrections the checks forced. PaLM 2's launch-day report is Google's own copy from 10 May 2023; the arXiv copy a week later adds a sentence on production monitoring, so PaLM 2 was recoded on the launch text. Pass B copied pass A's files for two releases through a shared scratch folder; both copies were quarantined and recoded by isolated coders, and a test now fails if any release pair shares four or more identical notes. Long cards were recoded one coder per card where a coder had skimmed. Rules added during coding at Wisdom Okechukwu's direction (addenda, benchmark vendors, age gates, every launch document, figures) are written into the codebook as numbered clarifications.

Verification. A further Claude instance, which coded and adjudicated nothing, checked a seeded sample of 80 text-pass codes against the documents (50 positives, 30 zeros, all 14 items): 78 correct, 0 wrong, 2 unsure, and both unsure cases were then settled by written codebook rules. There was no human audit: the spec's 15-release hand audit was replaced, at Wisdom Okechukwu's direction, by this check.

## Limits

These are gaps in the public record that further work cannot close.

- Two launch-day papers were never archived. Meta posted the LLaMA paper (February 2023) and "The Llama 3 Herd of Models" (July 2024) on its own site at launch. Every archived copy of the LLaMA PDF is an error page and the Llama 3.1 PDF was never captured. The arXiv v1 of each paper, posted 3 and 8 days later, is coded in its place, on the reading that it is the paper Meta published at launch. That choice matters for Llama 3.1 only: without its paper, Meta's count falls from 5 of 11 to 4 of 11, all labs from 40 of 87 to 39 of 87, and the second half of 2024 from 25% to 12% for dangerous-capability results and from 25% to 12% for outside testing. No LLaMA code comes from its paper.
- Three late cards were first archived after the date printed on them (Muse Spark 1.3, Grok 4.20, Grok 4.5), so their first public version cannot be proven. None of them was public at launch, so no at-launch figure depends on them.
- Two images in web cards could not be retrieved: a Hugging Face avatar on a dead image host and one Meta image behind an expired signed link.
- Half-years hold 5 to 17 releases, the number of frontier releases the labs made, so a single release moves a share by 6 to 20 points.
- The latest half-year runs only to 31 October 2026.

## Sources

Model and system cards, technical reports and model-specific safety reports from the seven labs as archived at launch (Wayback Machine, Hugging Face, GitHub, arXiv). Epoch AI, Data on AI models, CC BY 4.0. Stanford CRFM Foundation Model Transparency Index (December 2025) for indicator alignment.
