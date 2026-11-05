# Codebook v0 (pilot draft, freezes after the 10-release pilot)

Unit: one release, coded from the text of its primary card as captured in `cards/manifest.csv`. Later addenda in `other_docs` are not read for at-launch codes. Every value above 0 needs a verbatim quote from the card text and a locator (page or section heading). A quote must be copied exactly; the test in AT6 searches for it.

The question for every item is "does this card disclose it about this model", not "did the lab do it". A lab-level framework document, a blog post or a news report does not count unless the card itself states it.

## Dangerous-capability evaluations, by domain

`dc_eval_cbrn`, `dc_eval_cyber`, `dc_eval_autonomy`, `dc_eval_persuasion`, `dc_eval_scheming`

- 0: the domain is not mentioned as a risk evaluated for this model.
- 1: the card names the domain as a risk area, or says it was evaluated, without any result for this model.
- 2: the card reports at least one result for this model in the domain: a score, a pass or fail against a task set, a threshold determination, or a described qualitative finding from a named test.

Domains:
- cbrn: biological, chemical, radiological or nuclear weapons uplift, including virology and wet-lab protocol tasks.
- cyber: offensive cyber capability (CTFs, vulnerability discovery and exploitation, cyber ranges). Prompt-injection robustness alone is not cyber capability.
- autonomy: autonomous replication, AI research and development automation, self-improvement, long-horizon autonomous tasks evaluated as a risk.
- persuasion: persuasion, manipulation, influence operations.
- scheming: deception, sabotage, sandbagging, evaluation awareness, alignment faking, self-exfiltration, reward hacking evaluated as a misalignment risk.

Not dangerous-capability evaluations: general benchmarks (MMLU, SWE-bench), bias, toxicity, jailbreak refusal rates, hallucination. These belong to safeguards or to nothing.

## External pre-deployment testing

- `ext_test_any` (0/1): people outside the lab tested this model before release (red teamers, testers, partners), named or not.
- `ext_test_named_org` (0/1): the card names at least one outside organisation that tested this model before release (for example METR, Apollo Research, a contracted red-team firm).
- `ext_test_government` (0/1): the card says a government body tested this model before release (US CAISI or AISI, UK AISI, another state institute).

Post-release bug bounties and generic statements about working with governments do not count.

## Framework threshold

`framework_threshold`
- 0: no safety or scaling framework is referenced.
- 1: the card names a framework (Responsible Scaling Policy, Preparedness Framework, Frontier Safety Framework, Frontier AI Framework, Risk Management Framework, or similar) without placing this model against a threshold.
- 2: the card states where this model sits against a named threshold or level (ASL-3 required or not, "High" or "Critical" in a category, a Critical Capability Level reached or not).

## Safeguards described

Each 0/1, for safeguards applied to this model's deployment:
- `safeguards_training`: safety training or fine-tuning for refusals, harmlessness, or policy compliance (RLHF for safety, constitutional training, safety data).
- `safeguards_runtime`: classifiers, filters, moderation, or monitoring applied at inference or in production.
- `safeguards_access`: access restrictions tied to risk (trusted access programmes, KYC, staged rollout, usage tiers, limited availability for safety reasons).
- `safeguards_weights`: security measures protecting the model weights.

## Keyword screen for zeros (AT7)

A 0 on an item whose keywords occur in the text gets a reviewer note explaining why it stays 0.

- cbrn: biolog, bioweapon, chemical weapon, CBRN, radiolog, nuclear, virolog, pathogen
- cyber: cyber, CTF, capture the flag, exploit, vulnerabilit, offensive security
- autonomy: autonom, self-replicat, AI R&D, research and development, self-improv, ARA
- persuasion: persuas, manipulat, influence operation
- scheming: decept, sabotage, sandbag, scheming, alignment faking, evaluation awareness, exfiltrat, reward hack
- external: external, third-party, third party, red team, METR, Apollo, AISI, CAISI, Safety Institute
- framework: Responsible Scaling, Preparedness Framework, Frontier Safety Framework, Frontier AI Framework, Risk Management Framework, ASL-, Critical Capability Level, CCL
- safeguards: classifier, filter, moderation, monitor, refus, safety training, RLHF, trusted access, weight security, security of model weights

## Pilot

10 releases, stratified: one per lab plus three more from the labs with the longest cards. Two independent passes. Disagreements and any definition that produced them are logged in `docs/JOURNAL.md`; definitions may change only here, before the main pass, and the version number goes up.
