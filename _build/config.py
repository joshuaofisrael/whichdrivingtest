# Which Driving Test site config.
# NOINDEX is the single launch flag. Leave it True until whichdrivingtest.com
# resolves and is ready to be indexed. Set it False and rebuild to drop the
# noindex meta. datePublished is this constant, never the build clock.

SITE = "Which Driving Test"
DOMAIN = "https://whichdrivingtest.com"
CONTACT = "joshuaofisrael@gmail.com"

# Launch build. False drops the noindex meta. True keeps every page out of search.
NOINDEX = False

# Public Cloudflare Web Analytics beacon token. Written into pages only when NOINDEX is False.
CF_BEACON_TOKEN = "eac63f2b5dbc4539a2d95249baab6472"

# Owner fills a GA4 measurement id (G-XXXXXXXXXX) before ./deploy.sh --launch can pass.
# Leave this empty until then. Do not invent an id.
GA4_ID = "G-CZDQRN3V8F"

# First verification day for v1. Do not bump on a rebuild that does not change facts.
PUBLISHED = "2026-11-16"
CHECKED_LABEL = "16 Nov 2026"

INDEXNOW_KEY = "c4e1a9b27d6f48e0a3c5b81d09e7f246"

# Google AdSense publisher id. Head script + meta only; no ad units until approved.
ADSENSE_PUB = "ca-pub-5681559774142917"
ADSENSE_ADS_TXT = "google.com, pub-5681559774142917, DIRECT, f08c47fec0942fa0"

# Per-page lastmod/datePublished overrides for a page published or materially
# changed after PUBLISHED. Keys are the page's root-relative path exactly as
# returned by content.py (trailing slash kept). Every other page keeps PUBLISHED.
# Do not backdate or manufacture freshness here; add an entry only the day a
# page is actually new or actually changed.
LASTMOD_OVERRIDES = {
    "guides/permit-holding-period/": "2026-11-18",
    "wyoming/transfer/": "2026-11-19",
    "privacy/": "2026-11-19",
    "ad-disclosure/": "2026-11-19",
    # Alabama permit refresh and road-test upgrade, 20 Nov 2026.
    "alabama/": "2026-11-20",
    "alabama/permit/": "2026-11-20",
    "alabama/road-test/": "2026-11-20",
    "alabama/teen/": "2026-11-20",
    "alabama/written-test/": "2026-11-20",
    "alabama/fees/": "2026-11-20",
    "alabama/real-id/": "2026-11-20",
    "guides/learner-permit-ages/": "2026-11-20",
    "guides/teen-licensing/": "2026-11-20",
    "guides/road-test-automatic-fails/": "2026-11-20",
    "": "2026-11-20",
    "states/": "2026-11-20",
    "guides/permit-test-questions-by-state/": "2026-11-19",
}
