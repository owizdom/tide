# Supplement brief (codebook v1.2): figures, tables and extra launch documents

You are one of two independent coders (A or B). Never open coding/passes/, coding/supplement/<other letter>/, coding/quarantine/, coding/pilot/ or another coder's scratch folder.

1. Read /Users/macbook/Desktop/code/tide/coding/codebook.md in full, including clarifications 1-7 at the end. Clarifications 4 and 5 are why this pass exists.
2. Your work file lists releases. For each release it gives:
   - the open items: items whose current code is below the top level, with the current value;
   - extra launch documents (text files) that nobody has coded yet;
   - page images (PNG) from every launch document: every page that holds a figure, and every page whose text mentions an open item.
3. For each release:
   - Read every extra document's text in full, to the last line.
   - Look at every listed page image with the Read tool. Do not skip any.
   - For each open item, decide the highest level the codebook supports from the extra documents and the page images. Values never go below the current value.
4. Write coding/supplement/<letter>/<release_id>.json:
   {"release_id": "...", "coder": "<A|B>", "codebook": "v1.2", "items": {"<open item>": {"value": <int>, "source": "none|text|figure", "doc_sha": "<sha256 of the document the evidence is in>", "quote": "<verbatim span from that document's text layer>", "page": "<page number or imgN>", "description": "<what the figure shows, for figure evidence>", "note": "<short reason>"}}}
   - source "none": the value stays at the current value; give a note.
   - source "text": quote is required, 10 to 300 characters, copied exactly from the extra document's text file.
   - source "figure": page and description are required. The quote is the figure's caption, title or axis label as it appears in the document's text layer (required for PDF pages, optional for web images whose labels are only in the image).
   Every open item listed must appear in your file.
5. Before finishing, from /Users/macbook/Desktop/code/tide run: python3 -m coding.supplement --check <letter>
   and fix whatever it prints for your files.
6. Write nothing outside coding/supplement/<letter>/ except helper files in /private/tmp/claude-501/-Users-macbook/a64e47e7-93f9-4b32-9ffc-8c10d5410b76/scratchpad/coder<letter>_supp<group>/.

Report: releases done, every item you raised (release, item, old -> new, source), any page you could not read, the model you ran as. Under 300 words.
