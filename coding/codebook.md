# Codebook v1.1 (v1 frozen 2026-11-05 after the pilot; v1.1 adds two clarifications the same day, listed at the end)

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

Boundary rules (v1, from the pilot):
- Level 2 includes a stated threshold determination that covers this model, even without a score ("Neither ARC nor we believe that our current Claude models possess ... 'autonomous replication' abilities" is autonomy = 2).
- Autonomous or agentic cyberattack evaluations are cyber, not autonomy. Autonomy needs replication, AI R&D, self-improvement, or long-horizon autonomy evaluated as its own risk.
- Social engineering or spear-phishing uplift studied as part of cyber is cyber, not persuasion. Manipulation listed as a behaviour the lab looked for, with no result, is persuasion = 1.
- Situational awareness, stealth, honesty and deception evaluations framed as misalignment or loss-of-control risk are scheming. Reward hacking mentioned only as a training problem is not.

Not dangerous-capability evaluations: general benchmarks (MMLU, SWE-bench), bias, toxicity, jailbreak refusal rates, hallucination. These belong to safeguards or to nothing.

## External pre-deployment testing

- `ext_test_any` (0/1): people outside the lab tested this model before release (red teamers, testers, partners), named or not.
- `ext_test_named_org` (0/1): the card names at least one outside organisation that tested this model before release (for example METR, Apollo Research, a contracted red-team firm).
- `ext_test_government` (0/1): the card says a government body tested this model before release (US CAISI or AISI, UK AISI, another state institute).
- `ext_test_timing_stated` (0/1): the card states that some outside testing of this model happened before its release (for example "pre-deployment", "prior to release", "before launch").

Timing rule (Wisdom, 2026-11-05): outside testing reported in the card counts for the first three items unless the card says it happened after this model's release. GPT-4o's "Following the text output only deployment of GPT-4o, we worked with ... METR and Apollo Research" is after release, so it does not count. Grok 4's AISI testing with no stated timing counts. `ext_test_timing_stated` lets the strict pre-deployment reading be charted too.

"Outside the lab" means another organisation or independent individuals. Teams inside the lab that sit outside the model team ("specialist teams who sit outside of the model development team") are not outside. Partners or experts the card does not tie to this model's testing do not count.

Post-release bug bounties and generic statements about working with governments or policymakers do not count. A benchmark named after a government body (for example "UK AISI's Theory of Mind") is not government testing.

## Framework threshold

`framework_threshold`
- 0: no safety or scaling framework is referenced.
- 1: the card names a framework (Responsible Scaling Policy, Preparedness Framework, Frontier Safety Framework, Frontier AI Framework, Risk Management Framework, or similar) without placing this model against a threshold.
- 2: the card states where this model sits against a named threshold or level (ASL-3 required or not, "High" or "Critical" in a category, a Critical Capability Level reached or not).

## Safeguards described

Each 0/1, for safeguards applied to this model's deployment:
- `safeguards_training`: safety training or fine-tuning for refusals, harmlessness, or policy compliance (RLHF for safety, constitutional training, safety data).
- `safeguards_runtime`: a named runtime mechanism, such as classifiers, filters, moderation, or monitoring, applied at inference or in production. Safeguard models the lab ships as defaults for deployers (Llama Guard in the reference implementation) count. A general statement that a policy is enforced, with no mechanism named, does not.
- `safeguards_access`: access restrictions the card ties to risk or safety (trusted access programmes, KYC, usage tiers, limited availability for safety reasons). A staged or alpha rollout with no stated safety reason does not count. A licence or contact-details gate does not count.
- `safeguards_weights`: a stated protection of this model's weights against theft or exfiltration, including self-exfiltration by the model. A description of a stricter standard not applied to this model does not count.

## Keyword screen for zeros (AT7)

A 0 on an item whose keywords occur in the text gets a reviewer note explaining why it stays 0.

- cbrn: biolog, bioweapon, chemical weapon, CBRN, radiolog, nuclear, virolog, pathogen
- cyber: cyber, CTF, capture the flag, exploit, vulnerabilit, offensive security
- autonomy: autonom, self-replicat, AI R&D, research and development, self-improv, ARA
- persuasion: persuas, manipulat, influence operation
- scheming: decept, sabotage, sandbag, scheming, alignment faking, evaluation awareness, exfiltrat, reward hack
- external: external, third-party, third party, red team, METR, Apollo, AISI, CAISI, Safety Institute, pre-deployment, prior to release
- framework: Responsible Scaling, Preparedness Framework, Frontier Safety Framework, Frontier AI Framework, Risk Management Framework, ASL-, Critical Capability Level, CCL
- safeguards: classifier, filter, moderation, monitor, refus, safety training, RLHF, trusted access, weight security, security of model weights

## Pilot (done)

Pass A Opus 5.5, pass B Sonnet 5.5, 10 releases, 130 codes, 7 disagreements: ext_test_any and ext_test_named_org kappa 0.60, safeguards_weights 0.62, ext_test_government 0.74, safeguards_runtime 0.78, autonomy 0.82, the rest 1.00. Every disagreement traced to a definition fixed above. The main pass recodes all 87 releases, the pilot ten included, under v1.

## Pilot plan (v0)

10 releases, stratified: one per lab plus three more from the labs with the longest cards. Two independent passes. Disagreements and any definition that produced them are logged in `docs/JOURNAL.md`; definitions may change only here, before the main pass, and the version number goes up.

## v1.1 clarifications (2026-11-05, during the main pass)

1. Addendum cards (Wisdom). When the coded document is an addendum, appendix or update to an earlier model's card (for example the Claude 2 card with a Claude 2.1 appendix), an item counts only if the document reports it for this model or states that the result carries over to this model. Evaluations and outside testing reported for the earlier model do not count for this release. Safety training described for the model family counts when the document says this model was built the same way.
2. Outside testing means safety or risk testing: red teaming, dangerous-capability, alignment, or misuse evaluations. A third party that only ran or reported capability benchmark scores (for example "Results are taken from tests conducted by Mercor") is not outside testing.

3. Age gates (Wisdom, 2026-11-07). An age requirement for a consumer product (for example "Claude.ai ... is only available to users aged 18 or above") is a general usage term, not safeguards_access, even inside a child-safety section. Applied at adjudication.

Releases coded under v1 that clarifications 1 and 2 can change are recoded on both passes (coding/groups/r02_recode.txt).
