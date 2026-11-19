# Which Driving Test (whichdrivingtest.com)

Driving test and license rules for every US state and the District of Columbia, written from official agency pages. Static site, GitHub Pages (branch `main`, folder `/`).

This is not a government site and it is not legal advice. A fee, age, or document is included only when the official page states it.

v1 (16 Nov 2026): 363 HTML pages, 48 state guides. Ohio's learner permit age is 15 years and six months. Massachusetts, Illinois, Colorado, and New York are not yet covered because the official sites could not be quoted (New York research exists, but live DMV fetches returned empty pages during quote verification, so those facts stay out of `states.json` until they can be re-checked on purpose). Arizona's guide cites Arizona Revised Statutes because the MVD site did not open. `NOINDEX` is false for the launch build. The CNAME file is `whichdrivingtest.com`. The exact launch command is in `LAUNCH-NOTES.md`.

## Build

```
python3 _build/verify_quotes.py   # keeps a fact only when its quote is on the official page
python3 _build/build.py
python3 _build/check.py
```

`./deploy.sh` runs those three steps, then the legal gate. It does not commit.

`./deploy.sh --launch` is the launch command. It fails until `GA4_ID` in `_build/config.py` is a `G-` measurement id, and it fails if any page lacks the Cloudflare Web Analytics beacon or the GA4 loader. See `LAUNCH-NOTES.md`.

`NOINDEX` in `_build/config.py` is the single launch flag. It is `False` for this launch build, which drops the noindex meta and writes the Cloudflare beacon. The CNAME file and root-relative paths are written either way. `datePublished` is the `PUBLISHED` constant, not the build clock. Google Analytics 4 loads only after the visitor accepts the consent banner.

IndexNow: `./indexnow.sh` refuses to ping while `NOINDEX` is true.

## Sources

Research notes live in `_research/` (not published; Jekyll skips underscore folders). `_build/verify_quotes.py` re-downloads each official URL and drops any fact whose quote is not on the page, and any fee whose amount is not in that quote. Clean facts are `_build/data/states.json`.

Do not add a figure from a test-prep site, and do not guess a fee.
