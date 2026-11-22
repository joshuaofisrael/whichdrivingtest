#!/usr/bin/env python3
"""QA for the built site. Exit 1 on any issue."""

import glob
import html
import json
import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ADSENSE_ADS_TXT, ADSENSE_PUB, CF_BEACON_TOKEN, DOMAIN, GA4_ID, INDEXNOW_KEY, LASTMOD_OVERRIDES, NOINDEX, PUBLISHED
from geo import BY_SLUG

# Paths in _build/thin-noindex.txt are intentionally noindex (AdSense low-value-content fix, 20 Nov 2026).
import os as _os
_THIN = set()
try:
    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "thin-noindex.txt"), encoding="utf-8") as _fh:
        _THIN = {l.strip().strip("/") for l in _fh if l.strip() and not l.startswith("#")}
except FileNotFoundError:
    pass


def _thin_rel(rel):
    r = str(rel).replace("\\", "/")
    if r.endswith("index.html"):
        r = r[: -len("index.html")]
    return r.strip("/") in _THIN



ROOT = os.environ.get("WDT_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGAL = {"terms", "privacy", "disclaimer", "copyright", "ad-disclosure"}
LEGAL_HOSTS = {"adssettings.google.com", "policies.google.com", "google.com", "www.google.com", "aboutads.info", "www.aboutads.info"}
ANALYTICS_HOSTS = {
    "static.cloudflareinsights.com",
    "www.googletagmanager.com",
    "www.google-analytics.com",
    "region1.google-analytics.com",
    "pagead2.googlesyndication.com",
}
BEACON_SRC = "https://static.cloudflareinsights.com/beacon.min.js"
GA4_LOADER = "https://www.googletagmanager.com/gtag/js"
UNCOVERED = "Massachusetts, Illinois, Colorado, and New York are not yet covered because the official sites could not be quoted."
# Order matches content.UNCOVERED_STATES so footer text stays stable across builds.
FOOTER_HREFS = (
    "/about/",
    "/contact/",
    "/privacy/",
    "/terms/",
    "/disclaimer/",
    "/copyright/",
    "/ad-disclosure/",
    "/image-policy/",
)
BAD = 0


def issue(msg):
    global BAD
    BAD += 1
    print(msg)


def money(text):
    return set(re.findall(r"\$\d[\d,]*(?:\.\d{2})?", text or ""))


def load_amounts():
    path = os.path.join(os.path.dirname(__file__), "data", "states.json")
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for st in json.load(fh):
            allowed = set()
            for fee in st.get("fees") or []:
                allowed |= money(fee.get("amount"))
            out[st["slug"]] = allowed
    return out


def main():
    launch = "--launch" in sys.argv
    amounts = load_amounts()
    if launch and NOINDEX:
        issue("launch-noindex")
    if launch and not re.fullmatch(r"G-[A-Z0-9]+", GA4_ID or ""):
        issue("ga4-id-empty: set GA4_ID in _build/config.py to a G- measurement id")
    files = [f for f in glob.glob(ROOT + "/**/*.html", recursive=True) if "/_build/" not in f and "/_research/" not in f]
    titles = {}
    for f in files:
        text = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, ROOT)
        top = rel.split("/")[0]
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
            try:
                json.loads(raw)
            except Exception as exc:
                issue(f"JSONLD {rel} {exc}")
        visible = re.sub(r"<script.*?</script>", "", text, flags=re.S)
        visible_name = re.sub(r"Joshua(?:'|’|&#x27;|&#39;)s Law", "", visible)
        if top not in LEGAL and re.search(r"Joshua|Israel Ventures|©", visible_name):
            issue(f"LLC/© {rel}")
        if top in LEGAL and "is a trade name of Joshua Israel Ventures LLC" not in text:
            issue(f"nolegalline {rel}")
        if not re.search(r'<link rel="canonical" href="https://whichdrivingtest\.com/', text):
            issue(f"canonical {rel}")
        if "github.io" in text:
            issue(f"github.io {rel}")
        if text.count("<h1") != 1:
            issue(f"h1count {rel} {text.count('<h1')}")
        if "—" in text or "–" in text:
            issue(f"dash {rel}")
        if "not legal advice" not in text.lower() or "not a government site" not in text.lower():
            issue(f"disclaimer {rel}")
        desc = re.search(r'<meta name="description" content="(.*?)">', text)
        if not desc:
            issue(f"nodesc {rel}")
        else:
            dlen = len(html.unescape(desc.group(1)))
            if dlen > 155:
                issue(f"longdesc {dlen} {rel}")
            if dlen < 40:
                issue(f"shortdesc {dlen} {rel}")
        title = re.search(r"<title>(.*?)</title>", text)
        if not title:
            issue(f"notitle {rel}")
        else:
            t = html.unescape(title.group(1))
            titles.setdefault(t, []).append(rel)
            if len(t) >= 60:
                issue(f"longtitle {len(t)} {t}")
        if NOINDEX or rel == "404.html":
            if 'content="noindex, follow"' not in text:
                issue(f"missing-noindex {rel}")
        else:
            if "noindex" in text and not _thin_rel(rel):
                issue(f"stray-noindex {rel}")
        details = len(re.findall(r"<details\b", text))
        faq_qs = 0
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if data.get("@type") == "FAQPage":
                faq_qs += len(data.get("mainEntity") or [])
        if details != faq_qs:
            issue(f"faq-mismatch {rel} details={details} schema={faq_qs}")
        if rel != "404.html" and "application/ld+json" not in text:
            issue(f"no-jsonld {rel}")
        if rel == "index.html" and '"@type": "WebSite"' not in text:
            issue("no-website-schema")
        if rel not in ("index.html", "404.html") and '"@type": "BreadcrumbList"' not in text:
            issue(f"no-breadcrumb {rel}")
        if (
            top in BY_SLUG
            or rel.startswith("guides/")
            or rel in ("about/index.html", "methodology/index.html", "image-policy/index.html", "contact/index.html")
            or top in LEGAL
        ) and '"@type": "Article"' not in text:
            issue(f"no-article {rel}")
        key_faq = rel in (
            "index.html",
            "states/index.html",
            "guides/index.html",
            "guides/how-to-use/index.html",
            "guides/real-id/index.html",
            "guides/learner-permit-ages/index.html",
            "guides/teen-licensing/index.html",
            "guides/permit-holding-period/index.html",
            "guides/permit-test-questions-by-state/index.html",
            "guides/road-test-automatic-fails/index.html",
        ) or (top in BY_SLUG and rel.endswith("/index.html") and rel.count("/") == 1)
        if key_faq and '"@type": "FAQPage"' not in text:
            issue(f"no-faq-schema {rel}")
        if 'property="og:title"' not in text or 'property="og:description"' not in text or 'property="og:url"' not in text:
            issue(f"og {rel}")
        for href in FOOTER_HREFS:
            if f'href="{href}"' not in text:
                issue(f"footer-missing {rel} {href}")
        if "not affiliated with any dmv" not in text.lower():
            issue(f"affiliation {rel}")
        if UNCOVERED not in text:
            issue(f"uncovered {rel}")
        for img in re.finditer(r"<img\b[^>]*>", text, flags=re.I):
            window = text[max(0, img.start() - 400) : img.end()]
            if 'href="/image-policy/' not in window:
                issue(f"img-policy {rel}")
        if not NOINDEX:
            if BEACON_SRC not in text or "data-cf-beacon" not in text:
                issue(f"no-beacon {rel}")
            if CF_BEACON_TOKEN and f'"token": "{CF_BEACON_TOKEN}"' not in text:
                issue(f"beacon-token {rel}")
            if GA4_LOADER not in text or 'src="/assets/consent.js"' not in text:
                issue(f"no-ga4-loader {rel}")
            if "analytics_storage" not in text or "'denied'" not in text:
                issue(f"no-consent-default {rel}")
            if "Cookie settings" not in text:
                issue(f"no-cookie-settings {rel}")
        found = money(html.unescape(re.sub(r"<[^>]+>", " ", text)))
        allowed = amounts.get(top, set()) if top in BY_SLUG else set()
        for amt in found:
            if amt not in allowed:
                issue(f"unlisted-fee {rel} {amt}")
        for link in re.findall(r'(?:href|src)="([^"]*)', text):
            if not link or link.startswith("#") or link.startswith("mailto:"):
                continue
            bare = link.split("#", 1)[0].split("?", 1)[0]
            if not bare:
                continue
            if bare.startswith("http://") or bare.startswith("https://"):
                host = (urlparse(bare).hostname or "").lower()
                if host in {"whichdrivingtest.com", "www.whichdrivingtest.com"}:
                    continue
                if host in ANALYTICS_HOSTS:
                    continue
                official = host.endswith(".gov") or host.endswith(".mil") or host.endswith(".us")
                if top in BY_SLUG or top in {"guides", "states", "about", "methodology", "image-policy"}:
                    if not official:
                        issue(f"unofficial-link {rel} {bare}")
                elif top in LEGAL and not official and host not in LEGAL_HOSTS:
                    issue(f"unexpected-link {rel} {bare}")
                continue
            if not bare.startswith("/"):
                issue(f"not-root-relative {rel} {bare}")
                continue
            if bare.startswith("//") or bare.startswith("/whichdrivingtest"):
                issue(f"bad-prefix {rel} {bare}")
                continue
            target = os.path.join(ROOT, bare.lstrip("/"))
            if not (os.path.isfile(target) or os.path.isfile(os.path.join(target, "index.html"))):
                issue(f"broken {rel} {bare}")
    for title, paths in titles.items():
        if len(paths) > 1:
            issue(f"duptitle {title} {paths}")
    cname = os.path.join(ROOT, "CNAME")
    if not os.path.isfile(cname) or open(cname, encoding="utf-8").read().strip() != "whichdrivingtest.com":
        issue("CNAME")
    robots = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read() if os.path.isfile(os.path.join(ROOT, "robots.txt")) else ""
    for token in (
        "Googlebot",
        "Bingbot",
        "GPTBot",
        "ClaudeBot",
        "PerplexityBot",
        "OAI-SearchBot",
        "CCBot",
        "Google-Extended",
        "Applebot-Extended",
        "Bytespider",
        "Sitemap: https://whichdrivingtest.com/sitemap.xml",
    ):
        if token not in robots:
            issue(f"robots-missing {token}")
    sm_path = os.path.join(ROOT, "sitemap.xml")
    if not os.path.isfile(sm_path):
        issue("no-sitemap")
    else:
        sm = open(sm_path, encoding="utf-8").read()
        if "404.html" in sm:
            issue("404-in-sitemap")
        blocks = re.findall(r"<url>(.*?)</url>", sm, flags=re.S)
        for block in blocks:
            loc_m = re.search(r"<loc>(.*?)</loc>", block)
            lm_m = re.search(r"<lastmod>(.*?)</lastmod>", block)
            if not lm_m:
                issue("sitemap-no-lastmod")
                continue
            rel_loc = loc_m.group(1)[len(DOMAIN) :].lstrip("/") if loc_m else ""
            expected = LASTMOD_OVERRIDES.get(rel_loc, PUBLISHED)
            if lm_m.group(1) != expected:
                issue(f"sitemap-lastmod {rel_loc or '(home)'}")
        locs = re.findall(r"<loc>(.*?)</loc>", sm)
        llms = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read() if os.path.isfile(os.path.join(ROOT, "llms.txt")) else ""
        for loc in locs:
            if not loc.startswith(DOMAIN):
                issue(f"sitemap-host {loc}")
                continue
            rel = loc[len(DOMAIN) :].lstrip("/")
            target = os.path.join(ROOT, "index.html") if not rel else os.path.join(ROOT, rel, "index.html")
            if not os.path.isfile(target):
                issue(f"sitemap-missing {loc}")
            if rel.startswith(tuple(BY_SLUG)) or rel.split("/")[0] in BY_SLUG or (rel == "" ):
                pass
            slug = rel.split("/")[0]
            if slug in BY_SLUG and f"{DOMAIN}/{slug}/" not in llms:
                issue(f"llms-missing {slug}")
    key_path = os.path.join(ROOT, INDEXNOW_KEY + ".txt")
    if not os.path.isfile(key_path) or open(key_path, encoding="utf-8").read().strip() != INDEXNOW_KEY:
        issue("indexnow-key")
    ads_path = os.path.join(ROOT, "ads.txt")
    # AdSense detached 21 Nov 2026 until the account is approved (see seo-central/site-seo-rules.md). Do not re-add.
    if os.path.isfile(ads_path) and "pub-5681559774142917" in open(ads_path, encoding="utf-8").read():
        issue("ads-txt-still-has-adsense")
    sample = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if "google-adsense-account" in sample or "adsbygoogle.js" in sample:
        issue("adsense-tag-present")
    print("files", len(files), "issues", BAD)
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()
