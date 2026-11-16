#!/usr/bin/env python3
"""Keep a fact only when a short quote from it is on the official page.

Reads _research/b*.json. Writes _build/data/states.json.
Dollar amounts survive only as fee rows whose amount is printed in the quote.
"""

import glob
import hashlib
import html
import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from shutil import which
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESEARCH = os.path.join(ROOT, "_research")
CACHE = os.path.join(RESEARCH, "cache")
OUT = os.path.join(HERE, "data", "states.json")
REPORT = os.path.join(HERE, "data", "verify-report.json")

PAIRS = [
    ("permit_age", "permit_age_quote", "permit_age_url"),
    ("license_age", "license_age_quote", "license_age_url"),
    ("full_license_age", "full_license_age_quote", "full_license_age_url"),
    ("written_required", "written_quote", "written_url"),
    ("written_detail", "written_detail_quote", "written_url"),
    ("road_required", "road_quote", "road_url"),
    ("road_detail", "road_detail_quote", "road_url"),
    ("supervised_hours", "supervised_quote", "supervised_url"),
    ("holding_period", "holding_quote", "holding_url"),
    ("real_id_summary", "real_id_quote", "real_id_url"),
    ("transfer_summary", "transfer_quote", "transfer_url"),
    ("teen_summary", "teen_quote", "teen_url"),
    ("out_of_state_permit", "out_of_state_permit_quote", "out_of_state_permit_url"),
    ("curfew", "curfew_quote", "curfew_url"),
    ("passengers", "passengers_quote", "passengers_url"),
]
FALLBACK_QUOTE = {
    "written_detail": "written_quote",
    "road_detail": "road_quote",
    "teen_summary": "teen_quote",
}
AGE_KEYS = {"permit_age", "license_age", "full_license_age"}
AGE_PATTERNS = [
    re.compile(r"\d+\s+years?\s+and\s+\d+\s+months?", re.I),
    re.compile(r"\d+\s*(?:1/2|½)\s+years?(?:\s+of\s+age)?", re.I),
    re.compile(r"\d+\s+and\s+a\s+half(?:\s+years?)?(?:\s+of\s+age)?", re.I),
    re.compile(r"at least\s+\d+\s+years?\s+old", re.I),
    re.compile(r"\d+(?:st|nd|rd|th)\s+birthday", re.I),
    re.compile(r"\d+\s+years?\s+of\s+age(?:\s+or\s+older)?", re.I),
    re.compile(r"\d+\s+years?\s+old", re.I),
    re.compile(r"aged?\s+\d{1,2}(?:\s+and\s+older)?", re.I),
    re.compile(r"age\s+\d{1,2}\s+1/2", re.I),
]
URL_EXTRAS = ("agency_home", "scheduled_url", "handbook_url", "fee_page_url")


def clean_display(text):
    text = html.unescape(str(text or ""))
    text = re.sub(r"(\d)\s*\u00bd", r"\1 1/2", text)
    text = text.replace("\u00bd", " 1/2")
    text = (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\xa0", " ")
    )
    text = re.sub(r"(\d)1/2", r"\1 1/2", text)
    return re.sub(r"\s+", " ", text).strip()


def norm(text):
    return clean_display(text).lower()


def digits(text):
    return set(re.findall(r"\d+", clean_display(text)))


def official(url):
    host = (urlparse(url or "").hostname or "").lower()
    return bool(host) and (host.endswith(".gov") or host.endswith(".mil") or host.endswith(".us"))


def html_to_text(raw):
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    return norm(text)


def pdf_text(raw):
    if which("pdftotext") is None:
        return ""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(raw)
        name = tmp.name
    try:
        proc = subprocess.run(["pdftotext", "-q", name, "-"], check=False, capture_output=True)
        return norm(proc.stdout.decode("utf-8", "replace"))
    finally:
        os.remove(name)


def fetch_one(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    path = os.path.join(CACHE, key + ".txt")
    meta = os.path.join(CACHE, key + ".meta")
    if os.path.isfile(path) and os.path.isfile(meta):
        final = open(meta, encoding="utf-8").read().strip()
        if official(final):
            return url, open(path, encoding="utf-8").read()
        return url, ""
    if not official(url):
        return url, ""
    bin_path = path + ".bin"
    try:
        proc = subprocess.run(
            [
                "curl",
                "-fsSL",
                "-L",
                "--max-time",
                "45",
                "-A",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "-o",
                bin_path,
                "-w",
                "%{url_effective}\n%{content_type}",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return url, ""
    if proc.returncode != 0 or not os.path.isfile(bin_path):
        return url, ""
    final = proc.stdout.splitlines()[0].strip() if proc.stdout else ""
    ctype = proc.stdout.splitlines()[1] if len(proc.stdout.splitlines()) > 1 else ""
    if not official(final):
        os.remove(bin_path)
        return url, ""
    raw = open(bin_path, "rb").read()
    os.remove(bin_path)
    if "pdf" in ctype.lower() or final.lower().endswith(".pdf") or url.lower().endswith(".pdf"):
        text = pdf_text(raw)
    else:
        text = html_to_text(raw)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(final)
    return url, text


def quote_on_page(page, quote):
    q = norm(quote)
    words = q.split()
    if len(words) < 4 or not page:
        return False
    if len(words) < 6 and not digits(q):
        return False
    return q in page


def short_age(quote):
    shown = clean_display(quote)
    for pat in AGE_PATTERNS:
        match = pat.search(shown)
        if match:
            return clean_display(match.group(0))
    return None


def prose_ok(value, quote):
    if not isinstance(value, str):
        return None
    text = clean_display(value)
    if not re.search(r"[A-Za-z]", text) or "$" in text:
        return None
    if digits(text) - digits(quote):
        return None
    if len(text) > 460:
        text = text[:460].rsplit(" ", 1)[0]
    return text


def choose_text(key, value, quote):
    shown = clean_display(quote)
    count = len(shown.split())
    # Keep the official sentence. A short age clip can hide a condition.
    if key in AGE_KEYS and 4 <= count <= 42 and "$" not in shown:
        low = shown.lower()
        # Drop a statute fragment that is an exception, not the permit rule.
        if "unless" in low and "under" in low and not any(w in low for w in ("permit", "learner", "instruction", "license")):
            return None
        return shown
    prose = prose_ok(value, quote)
    if prose:
        return prose
    if 4 <= count <= 42 and "$" not in shown:
        return shown
    return None


def fee_ok(fee, page):
    amount = clean_display(fee.get("amount"))
    quote = fee.get("quote") or ""
    if not quote_on_page(page, quote):
        return False
    q = norm(quote)
    amt = norm(amount)
    if amt not in q:
        return False
    if "$" not in amount and "dollar" not in amt and not digits(amount):
        return False
    words = [w for w in re.findall(r"[a-z]{5,}", norm(fee.get("item") or ""))]
    if words and not any(w in q for w in words):
        return False
    return True


def score_state(st):
    score = 0
    for key, _quote, _url in PAIRS:
        if st.get(key):
            score += 2
    score += len(st.get("fees") or [])
    score += len(st.get("documents") or [])
    return score


def collect_urls(raw):
    found = set()
    for _key, _qk, url_key in PAIRS:
        url = raw.get(url_key)
        if url:
            found.add(url)
    for key in URL_EXTRAS:
        if raw.get(key):
            found.add(raw[key])
    for group in ("fees", "documents", "teen_points", "sources"):
        for item in raw.get(group) or []:
            if isinstance(item, dict) and item.get("url"):
                found.add(item["url"])
    return [u for u in found if official(u)]


def clean_state(raw, pages):
    st = {
        "slug": raw.get("slug"),
        "name": raw.get("name"),
        "agency": clean_display(raw.get("agency") or ""),
        "agency_short": clean_display(raw.get("agency_short") or ""),
        "sources": [],
    }
    for key in URL_EXTRAS:
        url = raw.get(key)
        st[key] = url if url and pages.get(url) else None
    for key, quote_key, url_key in PAIRS:
        quote = raw.get(quote_key) or raw.get(FALLBACK_QUOTE.get(key, ""), "")
        url = raw.get(url_key)
        page = pages.get(url) or ""
        if not quote_on_page(page, quote):
            st[key] = None
            st[url_key] = url if page else None
            continue
        st[key] = choose_text(key, raw.get(key), quote)
        st[url_key] = url
        if st[key] is None:
            st[url_key] = url if page else None
    fees = []
    for fee in raw.get("fees") or []:
        if not isinstance(fee, dict):
            continue
        url = fee.get("url")
        page = pages.get(url) or ""
        if fee_ok(fee, page):
            fees.append({"item": clean_display(fee.get("item") or "Fee")[:120], "amount": clean_display(fee.get("amount"))[:40], "url": url})
    st["fees"] = fees
    docs = []
    for doc in raw.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = doc.get("url")
        page = pages.get(url) or ""
        quote = doc.get("quote") or ""
        if not quote_on_page(page, quote):
            continue
        summary = prose_ok(doc.get("summary"), quote) or choose_text("document", doc.get("summary"), quote)
        if not summary:
            continue
        docs.append({"item": clean_display(doc.get("item") or "Document")[:80], "summary": summary, "url": url})
    st["documents"] = docs
    points = []
    for point in raw.get("teen_points") or []:
        if not isinstance(point, dict):
            continue
        url = point.get("url")
        page = pages.get(url) or ""
        quote = point.get("quote") or ""
        if not quote_on_page(page, quote):
            continue
        text = prose_ok(point.get("text"), quote) or choose_text("teen", point.get("text"), quote)
        if text:
            points.append({"text": text, "url": url})
    st["teen_points"] = points
    for src in raw.get("sources") or []:
        if isinstance(src, dict) and src.get("url") and pages.get(src["url"]):
            st["sources"].append(
                {
                    "title": clean_display(src.get("title") or st["agency"] or "Official page")[:140],
                    "url": src["url"],
                    "publisher": clean_display(src.get("publisher") or st["agency"] or "")[:140],
                }
            )
    if not st["agency"]:
        st["agency"] = None
    if not st["agency_short"]:
        st["agency_short"] = None
    return st


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    paths = (
        sorted(glob.glob(os.path.join(RESEARCH, "b*.json")))
        + sorted(glob.glob(os.path.join(RESEARCH, "c*.json")))
        + sorted(glob.glob(os.path.join(RESEARCH, "e*.json")))
    )
    if not paths:
        raise SystemExit("No _research/b*.json files")
    raw_states = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("states") or [data]
        raw_states.extend(data)
    urls = []
    seen_urls = set()
    for raw in raw_states:
        if isinstance(raw, dict):
            for url in collect_urls(raw):
                if url not in seen_urls:
                    seen_urls.add(url)
                    urls.append(url)
    pages = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_one, url) for url in urls]
        for fut in as_completed(futures):
            url, text = fut.result()
            pages[url] = text
    cleaned = []
    by_slug = {}
    for raw in raw_states:
        if not isinstance(raw, dict) or not raw.get("slug"):
            continue
        state = clean_state(raw, pages)
        slug = state["slug"]
        old = by_slug.get(slug)
        if old is None or score_state(state) > score_state(old):
            by_slug[slug] = state
    cleaned = list(by_slug.values())
    # Keep a previously verified state when this run has no fresh file for it.
    if os.path.isfile(OUT):
        with open(OUT, encoding="utf-8") as fh:
            previous = json.load(fh)
        have = {st.get("slug") for st in cleaned}
        for old in previous:
            if old.get("slug") and old.get("slug") not in have:
                cleaned.append(old)
    cleaned.sort(key=lambda s: s.get("name") or s["slug"])
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(cleaned, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    report = {
        "states": len(cleaned),
        "urls": len(urls),
        "pages_with_text": sum(1 for v in pages.values() if v),
        "empty_pages": [u for u, v in pages.items() if not v][:30],
    }
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: report[k] for k in ("states", "urls", "pages_with_text")}, indent=2))


if __name__ == "__main__":
    main()
