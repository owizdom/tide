# Coder brief (main pass, codebook v1)

You are one of two independent coders (A or B) in a content-analysis study of AI model cards. Never read anything under coding/passes/ except your own folder. Never read coding/pilot/.

1. Read /Users/macbook/Desktop/code/tide/coding/codebook.md in full and apply it literally. It is v1; its boundary rules and timing rule override your own judgement.
2. Your releases are listed in the group file you were given. For each, the card text is the file in the `text_path` column of /Users/macbook/Desktop/code/tide/cards/manifest.csv. Code ONLY from that text: no outside knowledge of the model, the lab, or other documents.
3. Read every card in full, in chunks (Read with offset and limit) until the end of the file. Keyword search is allowed only to find better quotes after a full read, never instead of one. A zero is a claim that the card does not disclose something; you must have read the whole card to make it.
4. For each release write coding/passes/<A or B>/<release_id>.json:
   {"release_id": "<id>", "coder": "<A|B>", "codebook": "v1", "codes": {"<variable>": {"value": <int>, "quote": "<verbatim span>", "locator": "<page or section>", "note": "<short reason>"}}}
   All 14 variables: dc_eval_cbrn, dc_eval_cyber, dc_eval_autonomy, dc_eval_persuasion, dc_eval_scheming, framework_threshold (0, 1 or 2); ext_test_any, ext_test_named_org, ext_test_government, ext_test_timing_stated, safeguards_training, safeguards_runtime, safeguards_access, safeguards_weights (0 or 1).
5. Any value above 0 needs one contiguous span copied exactly from the text, 10 to 300 characters, that by itself supports the value. Every 0 needs a short note.
6. Before finishing, from /Users/macbook/Desktop/code/tide run (replace X with your letter):
   python3 -c "import json,csv,glob; from coding.check import quote_found, validate; m={r['release_id']:r for r in csv.DictReader(open('cards/manifest.csv'))}; [print(p, v) for p in glob.glob('coding/passes/X/*.json') for rec in [json.load(open(p))] for v,c in rec['codes'].items() if c['value']>0 and not quote_found(c['quote'], open(m[rec['release_id']]['text_path'],errors='replace').read())]; [print(x) for p in glob.glob('coding/passes/X/*.json') for x in validate(json.load(open(p)))]"
   and fix whatever it prints for your own files (fix the quote; change a value only if the evidence is not in the text).
7. Write nothing outside your own coding/passes/<letter>/ folder.

Report: the release_ids you wrote, any card you could not read in full and why, any codebook rule you found ambiguous with the passage that made it so, and the model you ran as. Keep the report under 300 words.
