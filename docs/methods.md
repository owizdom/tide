# Are labs disclosing more or less with each model release?

Free Systems Challenge 4. Data, code and every coded card: this repository (`tide`).

## Findings

Far more frontier releases now launch with a card that reports safety test results than in 2023. Releases whose card, public at launch, reports at least one dangerous-capability test result rose from 20% in the first half of 2023 to 71% in July to October 2026.

Outside testing has not kept pace. The share of releases whose card reports any outside safety testing moved between 12% and 50% across the eight half-years and stood at 41% in the latest one.

Disclosure is concentrated. Anthropic reported dangerous-capability results at launch for 14 of 17 frontier releases and OpenAI for 12 of 15. Google did so for 5 of 13, Meta for 4 of 11, xAI for 3 of 11, DeepSeek for 1 of 9 and Mistral for 0 of 11. Across all labs the figure is 39 of 87.

Cards are often late or missing. Of 87 frontier releases, 62 had a card public within two days of launch, 11 got one later (6 to 374 days after launch) and 14 never got one.

## Three drops between successive releases

The case rule was fixed before coding: an item counts as dropped when one release discloses it at launch and the same lab's next frontier release does not. The three largest drops, counted over the 14 items, ties going to the later release:

1. Meta, Muse Spark 1.1 to Muse Spark 1.2 (August 2026). Muse Spark 1.1 shipped with a 112-page evaluation report disclosing 13 of the 14 items, all but government testing. Muse Spark 1.2 shipped with an announcement and no card, so all 13 dropped. Meta's next release, Muse Spark 1.3, got its evaluation report 51 days after launch.
2. OpenAI, GPT-4.5 to GPT-4.1 (April 2025). GPT-4.5 launched with a system card reporting results in all five dangerous-capability domains and a Preparedness Framework determination. GPT-4.1 launched with an announcement only, and no card has appeared since. 10 of the 14 items dropped.
3. OpenAI, GPT-4 to GPT-4 Turbo (November 2023). GPT-4 launched with a technical report and system card covering all five domains and outside red teaming by named organisations. GPT-4 Turbo launched with an announcement and no card. 10 of the 14 items dropped.

## What was measured

Frontier release. Each lab's top-tier general-purpose model at each new version, from Epoch AI's full AI models database (export of 5 November 2026, sha256 pinned in `releases/epoch/SOURCE.txt`). Seven labs: Anthropic, OpenAI, Google, Meta, xAI, Mistral and DeepSeek. The rule and every include or exclude decision (`releases/ladders.yaml`) were frozen before any card was fetched. The list has 87 releases from January 2023 to October 2026. Epoch's own frontier subset (top 5 by training compute) was not used because it has no Mistral or DeepSeek models and almost nothing after mid-2025.

Card at launch. The developer's own document about the model (system card, model card, technical report, or Hugging Face or GitHub model card), captured as it stood at launch: the earliest Wayback Machine capture, or the commit at launch for Hugging Face and GitHub cards. A card public no later than two days after launch counts as at launch. Announcement posts and product documentation pages do not count as cards.

Items. Results in five dangerous-capability domains (bio, chemical or nuclear; cyber; autonomy or AI R&D; persuasion; deception or scheming), a framework threshold stated for the model, outside testing (any, named organisation, government, pre-release timing stated), and four kinds of safeguard (safety training, runtime, access restrictions, weight security). The codebook is `coding/codebook.md`. An item counts as disclosed at launch only when the card public at launch reports it. A release with a late card or no card discloses nothing at launch.

Card length is reported separately in `cards/manifest.csv` and never enters a share.

## How the cards were coded

Two coders coded every one of the 73 cards independently: pass A on Claude Opus 5.5, pass B on Claude Sonnet 5.5. Every code above zero carries a verbatim quote that a test finds in the archived card text. Agreement across 1,022 codes was high, with Cohen's kappa between 0.83 and 1.00 for every item. The 18 disagreements were settled by a third Claude instance that coded nothing, citing the codebook.

The coding was not clean the first time, and the record says so. Pass B copied pass A's files for two releases through a shared scratch folder. Both copies were quarantined and recoded by isolated coders, and a test now fails if any release pair shares four or more identical notes. Pass B skimmed some long cards, and those were recoded with one coder per card. Three rules were added during coding at Wisdom Okechukwu's direction: addendum cards count only what they report for the new model; capability-benchmark vendors are not outside safety testing; consumer age gates are not access restrictions.

All coding was done by Claude models. A fourth Claude instance, which coded and adjudicated nothing, checked a seeded sample of 80 final codes against the cards (50 positives, 30 zeros, all 14 items): 78 correct, 0 wrong, 2 unsure. There was no human audit: the spec's 15-release hand audit was replaced, at Wisdom Okechukwu's direction, by this check.

## Limits

Coders read the card text, not its figures. A result shown only in a chart image is missed.

Labs publish safety material outside model cards (framework reports, blog posts, risk reports). This study counts only the model's own card, so a lab that discloses elsewhere scores lower here.

Half-years hold 5 to 17 releases, so a single release moves a share by 6 to 20 points.

The latest half-year runs only to 31 October 2026.

Two verification codes stayed unsure. Muse Spark 1.1 counts as restricting access because its card ties a controlled deployment to Meta's Advanced AI Scaling Framework. Llama 3.1 405B gets no outside testing because the card ties its partnered red teaming to Llama 3. Either could reasonably go the other way, and neither changes a headline figure by more than one release.

## Sources

Model and system cards from the seven labs as archived at launch (Wayback Machine, Hugging Face, GitHub). Epoch AI, Data on AI models, CC BY 4.0. Stanford CRFM Foundation Model Transparency Index (December 2025) for indicator alignment.
