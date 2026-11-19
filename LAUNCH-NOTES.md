# Launch notes

`NOINDEX` in `_build/config.py` is `False`. The launch build writes root-relative paths, keeps `CNAME` as `whichdrivingtest.com`, and rewrites `sitemap.xml` (with `lastmod`), `robots.txt`, `llms.txt`, and the IndexNow key file.

Massachusetts, Illinois, Colorado, and New York are not yet covered because the official sites could not be quoted. That sentence is in the footer of every page. No ages or fees are shown for those states. Do not re-run `verify_quotes.py` as a side effect of deploy unless you mean to; the 18 Nov verify pass emptied New York in `states.json` when DMV URLs returned no text.

## Commands

QA, which passes while `GA4_ID` is still an empty string:

```
python3 _build/build.py
python3 _build/check.py
python3 _build/legal_gate.py check --no-queue
```

The same three steps, plus quote verification when `_research/b*.json` is present:

```
./deploy.sh
```

Exact launch command, after you set `GA4_ID` in `_build/config.py` to your measurement id (`G-XXXXXXXXXX`):

```
./deploy.sh --launch
```

`./deploy.sh --launch` requires `NOINDEX = False`. It re-checks quotes when `_research/b*.json` is present, builds the site, runs the launch check, and runs the legal gate. It does not commit and it does not ping IndexNow.

The launch check fails if `GA4_ID` is empty, if any page is missing the Cloudflare Web Analytics beacon, or if any page is missing the GA4 loader.

When whichdrivingtest.com answers on the apex, ping IndexNow:

```
./indexnow.sh
```

## Analytics

Cloudflare Web Analytics uses the public beacon token in `CF_BEACON_TOKEN`. The script is `https://static.cloudflareinsights.com/beacon.min.js` with `data-cf-beacon='{"token": "..."}'`. It is written on every page only when `NOINDEX` is false.

Google Analytics 4 loads only after Accept on the consent banner. Consent Mode v2 defaults are denied. Cookie settings in the footer reopens the banner. The privacy page names Google Analytics 4 and Cloudflare Web Analytics.
