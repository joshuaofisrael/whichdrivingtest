#!/usr/bin/env python3
"""Build the static site from _build/data/states.json.

Root-relative paths and the CNAME file are always written.
NOINDEX in config.py is the single switch for the noindex meta tag.
"""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ADSENSE_ADS_TXT, CHECKED_LABEL, DOMAIN, INDEXNOW_KEY, NOINDEX, PUBLISHED, SITE
from content import all_pages, uncovered_phrase
from geo import STATES
from render import page, picker_html, _is_thin

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("WDT_ROOT") or os.path.dirname(HERE)
DATA = os.path.join(HERE, "data", "states.json")

STATIC_DIRS = [
    "guides",
    "states",
    "about",
    "methodology",
    "image-policy",
    "contact",
    "terms",
    "privacy",
    "disclaimer",
    "ad-disclosure",
    "copyright",
]
STATIC_FILES = ["index.html", "404.html", "sitemap.xml", "robots.txt", "llms.txt", "CNAME"]


def scrub(obj):
    if isinstance(obj, str):
        return (
            obj.replace("\u2014", "-")
            .replace("\u2013", "-")
            .replace("\u2019", "'")
            .replace("\u2018", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
        )
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    return obj


def load_states():
    if not os.path.isfile(DATA):
        raise SystemExit(f"Missing {DATA}. Run _build/verify_quotes.py after research is saved.")
    with open(DATA, encoding="utf-8") as fh:
        states = scrub(json.load(fh))
    for st in states:
        if not st.get("teen_url"):
            st["teen_url"] = st.get("supervised_url") or st.get("curfew_url") or st.get("holding_url") or st.get("passengers_url")
        if not st.get("real_id_url"):
            for doc in st.get("documents") or []:
                if doc.get("url"):
                    st["real_id_url"] = doc["url"]
                    break
        st["name"] = st.get("name") or st["slug"]
    return states


def clean_output():
    for slug, _name, _region in STATES:
        path = os.path.join(ROOT, slug)
        if os.path.isdir(path):
            shutil.rmtree(path)
    for name in STATIC_DIRS:
        path = os.path.join(ROOT, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
    for name in STATIC_FILES:
        path = os.path.join(ROOT, name)
        if os.path.isfile(path):
            os.remove(path)


def write_text(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def html_path(url_path):
    rel = url_path.strip("/")
    if not rel:
        return os.path.join(ROOT, "index.html")
    if rel == "404.html":
        return os.path.join(ROOT, "404.html")
    return os.path.join(ROOT, rel, "index.html")


def public_url(url_path):
    rel = url_path.strip("/")
    if not rel:
        return DOMAIN + "/"
    if rel == "404.html":
        return DOMAIN + "/404.html"
    return DOMAIN + "/" + rel + "/"


def write_robots():
    body = """User-agent: *
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Mediapartners-Google
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: DuckAssistBot
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: CCBot
Allow: /

User-agent: Bytespider
Allow: /

Sitemap: https://whichdrivingtest.com/sitemap.xml
"""
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(body)


def write_sitemap(pages):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for item in pages:
        if item["path"] == "404.html" or _is_thin(item["path"]):
            continue
        lines.append("  <url>")
        lines.append(f"    <loc>{public_url(item['path'])}</loc>")
        lines.append(f"    <lastmod>{item.get('lastmod') or PUBLISHED}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_llms(pages, states):
    by_slug = {st["slug"]: st for st in states}
    lines = [
        f"# {SITE}",
        "",
        f"> {SITE} ({DOMAIN.replace('https://', '')}) explains driving test and license rules for every US state and the District of Columbia. Facts come from official state licensing pages. Checked {CHECKED_LABEL}. Not a government site. Not legal advice.",
        "",
        "## Guides",
    ]
    for item in pages:
        path = item["path"].strip("/")
        if path.startswith("guides/"):
            lines.append(f"- [{item['title']}]({public_url(item['path'])})")
    lines.append("")
    lines.append("## States")
    for slug, name, _region in sorted(STATES, key=lambda s: s[1]):
        st = by_slug.get(slug)
        if not st:
            if name in {"Massachusetts", "Illinois", "Colorado", "New York"}:
                lines.append(f"- {name}: not yet covered because the official site could not be quoted.")
            else:
                lines.append(f"- {name}: guide not published. Official figures were not confirmed.")
            continue
        age = f" Learner permit age published: {st['permit_age']}." if st.get("permit_age") else ""
        lines.append(f"- [{name}]({DOMAIN}/{slug}/).{age}")
        for key, label in (
            ("permit", "Learner permit"),
            ("written-test", "Written test"),
            ("road-test", "Road test"),
            ("real-id", "REAL ID"),
            ("fees", "Fees"),
            ("transfer", "License transfer"),
            ("teen", "Teen licensing"),
        ):
            if st.get("_topics", {}).get(key):
                lines.append(f"  - [{label}]({DOMAIN}/{slug}/{key}/)")
    lines.append("")
    lines.append("## Other pages")
    for item in pages:
        path = item["path"].strip("/")
        if path in ("", "404.html") or path.startswith("guides") or path in by_slug:
            continue
        if "/" in path and path.split("/")[0] in by_slug:
            continue
        lines.append(f"- [{item['title']}]({public_url(item['path'])})")
    lines.append("")
    with open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_indexnow():
    path = os.path.join(ROOT, INDEXNOW_KEY + ".txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(INDEXNOW_KEY)


def write_ads_txt():
    path = os.path.join(ROOT, "ads.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(ADSENSE_ADS_TXT.strip() + "\n")


def main():
    states = load_states()
    pages, report, published = all_pages(states)
    clean_output()
    picker = picker_html(published)
    note = uncovered_phrase(report["missing_states"])
    for item in pages:
        html = page(
            item["title"],
            item["description"],
            item["path"],
            item["body"],
            item["schemas"],
            nav=item.get("nav"),
            picker=picker,
            uncovered=note,
        )
        dest = html_path(item["path"])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(html)
    write_sitemap(pages)
    write_robots()
    write_llms(pages, [st for st in states if st["slug"] in published])
    write_indexnow()
    write_ads_txt()
    with open(os.path.join(ROOT, "CNAME"), "w", encoding="utf-8") as fh:
        fh.write("whichdrivingtest.com\n")
    report_path = os.path.join(HERE, "data", "build-report.json")
    summary = {
        "pages": len(pages),
        "html_without_404": len(pages) - 1,
        "states": len(report["published"]),
        "missing_states": report["missing_states"],
        "topics": {key: len(slugs) for key, slugs in report["topics"].items()},
        "skipped": report["skipped"],
        "noindex": NOINDEX,
        "checked": CHECKED_LABEL,
    }
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
