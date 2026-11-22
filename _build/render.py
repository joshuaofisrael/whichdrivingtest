"""HTML shell, schema, and small components. Paths are root-relative."""

import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ADSENSE_PUB, CF_BEACON_TOKEN, CHECKED_LABEL, DOMAIN, GA4_ID, NOINDEX, PUBLISHED, SITE
from geo import REGIONS, region_groups

BANNER = (
    '<p class="banner"><strong>Not a government site.</strong> '
    "Not affiliated with any DMV. "
    "This is general information, not legal advice. Rules and fees change. "
    'Check your state licensing agency before you apply. <a href="/disclaimer/">Read the disclaimer</a>.</p>'
)

FOOTER_BLURB = (
    f"<strong>{SITE}</strong> explains driving test and license rules from official state agency pages. "
    "We are not a government site and we are not affiliated with any DMV. "
    "This is general information, not legal advice. "
    "The state agency page controls, and rules and fees change."
)

LEGAL_LINE = (
    '<p class="legal-line">© 2026 Joshua Israel Ventures LLC. All rights reserved. '
    f"{SITE} is a trade name of Joshua Israel Ventures LLC, a Florida limited liability company.</p>"
)

NAV = [
    ("home", "/", "Home"),
    ("states", "/states/", "States"),
    ("how", "/guides/how-to-use/", "How to use"),
    ("realid", "/guides/real-id/", "REAL ID"),
]

FOOTER_LINKS = [
    ("/about/", "About"),
    ("/methodology/", "Sources and methods"),
    ("/image-policy/", "Image policy"),
    ("/terms/", "Terms of use"),
    ("/privacy/", "Privacy"),
    ("/disclaimer/", "Disclaimer"),
    ("/ad-disclosure/", "Advertising disclosure"),
    ("/copyright/", "Copyright and DMCA"),
    ("/contact/", "Contact"),
]

LOGO = (
    '<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
    '<rect width="64" height="64" rx="14" fill="#0b3954"/>'
    '<rect x="8" y="34" width="48" height="16" rx="3" fill="#e7f5ee"/>'
    '<rect x="14" y="40" width="8" height="4" rx="1" fill="#f0b429"/>'
    '<rect x="28" y="40" width="8" height="4" rx="1" fill="#f0b429"/>'
    '<rect x="42" y="40" width="8" height="4" rx="1" fill="#f0b429"/>'
    '<circle cx="32" cy="20" r="8" fill="none" stroke="#f0b429" stroke-width="4"/>'
    "</svg>"
)


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def jsonld(obj):
    raw = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{raw}</script>'


def canonical(path):
    if path in ("", "/"):
        return DOMAIN + "/"
    if path.startswith("http"):
        return path
    return DOMAIN + "/" + path.lstrip("/")


def ext(url, label, official=True, nofollow=False):
    rel = "nofollow noopener" if nofollow else "noopener"
    suffix = ' <span class="ext">(official site)</span>' if official else ""
    return f'<a href="{esc(url)}" rel="{rel}" target="_blank">{esc(label)}{suffix}</a>'


def btn(url, label):
    return f'<a class="btn alt" href="{esc(url)}" rel="noopener" target="_blank">{esc(label)}</a>'


def internal(href, label):
    return f'<a href="{esc(href)}">{esc(label)}</a>'


def crumbs_html(items):
    parts = []
    last = len(items) - 1
    for i, (name, href) in enumerate(items):
        if i == last:
            parts.append(f'<li aria-current="page">{esc(name)}</li>')
        else:
            parts.append(f'<li><a href="{esc(href)}">{esc(name)}</a></li>')
    return '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(parts) + "</ol></nav>"


def breadcrumb_schema(items):
    elements = []
    for i, (name, href) in enumerate(items, 1):
        elements.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": canonical(href),
            }
        )
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": elements}


def article_schema(headline, path, about=None, published=None):
    stamp = published or PUBLISHED
    obj = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "datePublished": stamp,
        "dateModified": stamp,
        "author": {"@type": "Organization", "name": SITE, "url": DOMAIN + "/"},
        "publisher": {
            "@type": "Organization",
            "name": SITE,
            "url": DOMAIN + "/",
            "logo": {"@type": "ImageObject", "url": DOMAIN + "/logo.png"},
        },
        "image": DOMAIN + "/og.png",
        "mainEntityOfPage": canonical(path),
    }
    if about:
        obj["about"] = {"@type": "Thing", "name": about}
    return obj


def faq_schema(faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }


def faq_block(faqs):
    chunks = ['<h2 id="faq-h">Frequently asked questions</h2>', '<div class="faq">']
    for q, a in faqs:
        chunks.append(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>")
    chunks.append("</div>")
    return "".join(chunks)


def sources_block(sources, checked=None):
    seen = []
    for src in sources:
        url = (src or {}).get("url")
        if not url or any(s["url"] == url for s in seen):
            continue
        seen.append(
            {
                "title": src.get("title") or "Official page",
                "url": url,
                "publisher": src.get("publisher") or "",
            }
        )
    if not seen:
        return ""
    items = []
    for src in seen:
        label = src["title"]
        if src["publisher"] and src["publisher"] not in label:
            label = f'{src["title"]} ({src["publisher"]})'
        items.append(f"<li>{ext(src['url'], label)}</li>")
    return (
        f'<section class="sources"><h2>Sources</h2>'
        f"<p>Checked {esc(checked or CHECKED_LABEL)}. These are the official pages used for the figures on this page.</p>"
        f"<ul>{''.join(items)}</ul></section>"
    )


def related_block(links):
    if not links:
        return ""
    items = "".join(f"<li>{internal(href, label)}</li>" for href, label in links)
    return f'<aside class="related"><h2>Related guides</h2><ul>{items}</ul></aside>'


def facts_table(rows):
    body = "".join(f'<tr><th scope="row">{esc(label)}</th><td>{value}</td></tr>' for label, value in rows)
    return f'<div class="tablewrap"><table class="facts">{body}</table></div>'


def missing():
    return "Not clearly published on the pages we checked."


def picker_html(published):
    """published: dict slug -> name, only states that have a page."""
    groups = region_groups()
    options = ['<option value="">Choose a state</option>']
    for region in REGIONS:
        opts = []
        for slug, name in groups[region]:
            if slug not in published:
                continue
            opts.append(f'<option value="/{esc(slug)}/">{esc(name)}</option>')
        if opts:
            options.append(f'<optgroup label="{esc(region)}">' + "".join(opts) + "</optgroup>")
    return (
        '<div class="jump">'
        '<label for="state-jump">State</label>'
        f'<select id="state-jump">{"".join(options)}</select>'
        "</div>"
    )


def byline(checked=None):
    return f'<p class="byline">By {esc(SITE)}. Last checked {esc(checked or CHECKED_LABEL)}.</p>'


def adsense_html():
    """AdSense account verification only. No ad units are placed on the page."""
    return ""  # AdSense detached 21 Nov 2026 until the account is approved (see seo-central/site-seo-rules.md). Do not re-add.
    if NOINDEX or not ADSENSE_PUB:
        return ""
    pub = esc(ADSENSE_PUB)
    return (
        f'<meta name="google-adsense-account" content="{pub}">\n'
        f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={pub}" '
        'crossorigin="anonymous"></script>'
    )


def analytics_html():
    """Launch-only analytics. GA4 is consent-gated. The Cloudflare beacon is not."""
    if NOINDEX:
        return "<!-- analytics: omitted while NOINDEX is true -->"
    beacon = "<!-- cf-beacon: token missing -->"
    if CF_BEACON_TOKEN:
        beacon = (
            '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f"data-cf-beacon='{{\"token\": \"{CF_BEACON_TOKEN}\"}}'></script>"
        )
    ga_id = esc(GA4_ID or "")
    consent = f"""<script>
window.dataLayer=window.dataLayer||[];
function gtag(){{dataLayer.push(arguments);}}
gtag('consent','default',{{
  ad_storage:'denied',
  ad_user_data:'denied',
  ad_personalization:'denied',
  analytics_storage:'denied',
  functionality_storage:'denied',
  personalization_storage:'denied',
  security_storage:'granted',
  wait_for_update:500
}});
gtag('set','ads_data_redaction',true);
gtag('set','url_passthrough',true);
</script>
<script src="/assets/consent.js" defer data-ga4-id="{ga_id}" data-ga4-loader="https://www.googletagmanager.com/gtag/js"></script>"""
    return consent + beacon


def consent_banner():
    if NOINDEX:
        return ""
    return (
        '<div id="consent-banner" class="consent" role="region" aria-label="Cookie settings" hidden>'
        '<p id="consent-title"><strong>Cookie settings</strong></p>'
        "<p>Cloudflare Web Analytics loads without cookies. Google Analytics 4 stays off unless you accept. "
        '<a href="/privacy/#cookies">Privacy</a></p>'
        '<p class="consent-actions"><button type="button" id="consent-accept">Accept</button> '
        '<button type="button" id="consent-reject">Reject</button></p>'
        "</div>"
    )


# AdSense low-value-content fix (20 Nov 2026): paths listed in _build/thin-noindex.txt
# get noindex,follow and stay out of the sitemap until they have real unique substance.
_THIN_NOINDEX = set()
try:
    import os as _os
    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "thin-noindex.txt"), encoding="utf-8") as _fh:
        _THIN_NOINDEX = {l.strip().strip("/") for l in _fh if l.strip() and not l.startswith("#")}
except FileNotFoundError:
    pass


def _is_thin(path):
    return str(path).strip("/") in _THIN_NOINDEX


def page(title, description, path, body, schemas, nav=None, picker="", uncovered=""):
    canon = canonical(path)
    robots = "noindex, follow" if (NOINDEX or path == "404.html" or _is_thin(path)) else "index, follow"
    og_type = "website" if path in ("", "/", "404.html", "contact/") else "article"
    nav_html = []
    for key, href, label in NAV:
        current = ' aria-current="page"' if key == nav else ""
        nav_html.append(f'<a href="{esc(href)}"{current}>{esc(label)}</a>')
    footer_bits = [internal(href, label) for href, label in FOOTER_LINKS]
    if not NOINDEX:
        footer_bits.append('<a href="/privacy/#cookies" id="cookie-settings">Cookie settings</a>')
    footer_links = " | ".join(footer_bits)
    schema_html = "".join(jsonld(s) for s in schemas)
    uncovered_html = f'<p class="uncovered">{esc(uncovered)}</p>' if uncovered else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{esc(canon)}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#0b3954">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{esc(SITE)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canon)}"><meta property="og:image" content="{DOMAIN}/og.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css?v=2">{schema_html}
{adsense_html()}
{analytics_html()}
</head><body><a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="/">{LOGO}<span>{esc(SITE)}</span></a><nav class="main" aria-label="Main">{''.join(nav_html)}</nav>{picker}</div></header>
<main id="main" class="wrap">{body}</main>
<footer class="site"><div class="wrap"><p class="fbrand">{FOOTER_BLURB}</p>
{uncovered_html}
<p class="flinks">{footer_links}</p>
</div></footer>
{consent_banner()}
<script src="/assets/site.js?v=2" defer></script>
</body></html>
"""
