# Which Driving Test (whichdrivingtest.com)

Driving test and license rules for every US state and the District of Columbia, written from official agency pages. Static site, GitHub Pages (branch `main`, folder `/`).

This is not a government site and it is not legal advice. A fee, age, or document is included only when the official page states it.

v1 (16 Nov 2026): 343 HTML pages, 46 state guides. Five states have no guide yet because the official site blocked or timed out before a quote could be checked: Massachusetts, Illinois, Michigan, Arizona, and Colorado. `NOINDEX` is still true. The CNAME file is `whichdrivingtest.com`.

## Build

```
python3 _build/verify_quotes.py   # keeps a fact only when its quote is on the official page
python3 _build/build.py
python3 _build/check.py
```

`./deploy.sh` runs those three steps. It does not commit.

`NOINDEX` in `_build/config.py` is the single launch flag. Leave it `True` until whichdrivingtest.com is live. Set it to `False` and rebuild to drop the noindex meta. The CNAME file and root-relative paths are written either way. `datePublished` is the `PUBLISHED` constant, not the build clock.

IndexNow: `./indexnow.sh` refuses to ping while `NOINDEX` is true.

## Sources

Research notes live in `_research/` (not published; Jekyll skips underscore folders). `_build/verify_quotes.py` re-downloads each official URL and drops any fact whose quote is not on the page, and any fee whose amount is not in that quote. Clean facts are `_build/data/states.json`.

Do not add a figure from a test-prep site, and do not guess a fee.
