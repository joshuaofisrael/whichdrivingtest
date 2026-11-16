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
GA4_ID = ""

# First verification day for v1. Do not bump on a rebuild that does not change facts.
PUBLISHED = "2026-11-16"
CHECKED_LABEL = "16 Nov 2026"

INDEXNOW_KEY = "c4e1a9b27d6f48e0a3c5b81d09e7f246"
