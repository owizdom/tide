# tide

Release-by-release safety disclosures in frontier AI model cards, January 2023 to October 2026, for Anthropic, OpenAI, Google, Meta, xAI, Mistral and DeepSeek. Free Systems Challenge 4: are labs disclosing more or less with each model release?

By Wisdom Okechukwu.

## Result

Releases whose documents, public at launch, report at least one dangerous-capability test result rose from 20% in the first half of 2023 to 71% in July to October 2026. Outside safety testing moved between 20% and 50% and stood at 41% in the latest half-year. Anthropic (14 of 17) and OpenAI (12 of 15) account for 26 of the 40 releases that reported such a result; Mistral reported none in 11. Of 87 frontier releases, 63 had a card within two days of launch, 10 got one later and 14 never did.

The write-up, with three case studies of disclosure drops, method and limits, is [docs/methods.md](docs/methods.md). The charts are in [analysis/out](analysis/out).

## What is where

| Folder | Contents |
|---|---|
| `releases/` | The frozen list of 87 frontier releases, the rule that picks them, every include or exclude decision with a reason code, and the pinned Epoch AI export it is built from |
| `cards/` | Every candidate launch document found, the launch version of each card (Wayback capture or commit, sha256, word count), and the extra launch documents |
| `coding/` | The codebook, both independent coding passes with a quote for every positive code, adjudications, the figures and tables pass, the verification sample, and the final codes in `coding/codes.csv` |
| `analysis/` | Shares by half-year and by lab, the case-study rule, the charts, and the checker that asserts every number in the write-up against the data |
| `report/` | Builds the .docx version of the write-up |
| `docs/` | The approved spec, the write-up and the project journal |
| `tests/` | The acceptance tests from the spec |

## Reproduce

Python 3.9 or later with matplotlib, numpy, pillow, pyyaml, python-docx and pytest, plus poppler (`pdftotext`, `pdftoppm`) and pandoc.

```
python3 -m pytest -q
python3 -m analysis.verify_claims
python3 -m report.build_docx
```

The coded document texts sit in a local cache (`~/.tide-cache`), not in the repository. `python3 -m cards.fetch` and `python3 -m cards.secondary` fetch them again from the archived URLs recorded in `cards/manifest.csv` and `cards/secondary.csv`, and the sha256 in each row identifies the exact bytes that were coded.

## Sources

Epoch AI, Data on AI models (CC BY 4.0). Model cards, system cards, technical reports and safety reports from the seven labs, as archived by the Wayback Machine, Hugging Face, GitHub and arXiv. Charts are drawn with the Free Systems chart kit, which is not included in this repository; `python3 -m analysis.plot` needs it in `analysis/fs_kit`. The rendered charts are in `analysis/out`.
