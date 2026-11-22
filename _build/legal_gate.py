#!/usr/bin/env python3
"""Which Driving Test pre-publish legal hold gate.

Adapted from the sister-site gate. Usage:
  python3 _build/legal_gate.py check [--no-queue]
Exit 0 when every page passes. Exit 3 on HOLD_REVIEW.

Flags:
  unsourced claims: a state or sourced guide page with no official .gov/.mil/.us link,
    or a dollar amount on a page that does not link an official source
  legal pages missing: About, Contact, Privacy, Terms, Disclaimer, Copyright,
    Ad disclosure, or Image policy is absent or not linked from the home page
  stray trademarks: DMV.org, a commercial test-prep brand, or a trademark symbol
Plus the sister-site tripwires for accusations, contact details outside legal pages,
remote images, and affiliation claims.
"""
import datetime
import glob
import hashlib
import html
import json
import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import BY_SLUG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "whichdrivingtest.com"
BOT = "Which Driving Test build"
CR = os.environ.get("CONTENT_REVIEW_DIR", "/tmp/whichdrivingtest-content-review")
Q = os.path.join(CR, "queue.jsonl")
DR = os.path.join(CR, "drafts", "whichdrivingtest")
HIGH = {1, 2, 6, 8}
OBJECTIVE = {3, 4}
LEGAL_PAGES = (
    "privacy",
    "terms",
    "contact",
    "disclaimer",
    "copyright",
    "ad-disclosure",
    "about",
    "image-policy",
    "methodology",
)
REQUIRED_LEGAL = (
    "about/index.html",
    "contact/index.html",
    "privacy/index.html",
    "terms/index.html",
    "disclaimer/index.html",
    "copyright/index.html",
    "ad-disclosure/index.html",
    "image-policy/index.html",
)
SOURCED_GUIDES = {
    "guides/real-id/index.html",
    "guides/learner-permit-ages/index.html",
    "guides/teen-licensing/index.html",
    "guides/permit-holding-period/index.html",
    "guides/permit-test-questions-by-state/index.html",
}
KW = {
    1: r"\b(fraud\w*|scam\w*|corrupt(ion|ly)?|embezzl\w*|arrested|indicted|charged with|convicted|lawsuits?|sued|suing|misconduct|abus(e|ed|ive)|dishonest\w*|cover[ -]?up|criminal|bribe\w*|negligen\w*|cheat(s|ed|ing)?|rip[ -]?off)\b",
    5: r"\b(guaranteed returns?|tax advice|legal advice|medical advice|you should (sue|claim compensation)|take \d+ ?mg)\b",
    6: r"\b(election|ballot|polling (place|station)|voter registration|vote by|voting day|certified results?|electoral)\b",
    7: r"\b(official partner|endorsed by|in partnership with|certified by|approved by the|100% (safe|accurate)|guaranteed (best|pass|score))\b",
    8: r"\b(embargo(ed)?|cease and desist|dmca|takedown notice|legal notice|reporting restriction|correction request)\b",
}
STRAY = (
    (r"dmv\.org", "DMV.org is a private brand, not a state agency"),
    (r"®|™", "trademark symbol"),
    (r"\b(Aceable|Zutobi|DriversEd\.com|Driving-Tests\.org)\b", "commercial test-prep brand"),
)


def lines(name):
    out = []
    for path in (os.path.join(CR, name), os.path.join(ROOT, "legal", name)):
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def approved(digest):
    return any(
        row.get("site") == SITE and row.get("sha256") == digest and str(row.get("approved_by", "")).lower().startswith("joshua")
        for row in lines("approvals.jsonl")
    )


def cleared(digest):
    return any(
        row.get("site") == SITE
        and row.get("sha256") == digest
        and str(row.get("chatgpt_verdict", "")).upper().startswith("SAFE")
        for row in lines("moderate-clearances.jsonl")
    )


def visible(raw):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def official_link(raw):
    for url in re.findall(r'href="(https?://[^"]+)"', raw):
        host = (urlparse(url).hostname or "").lower()
        if host.endswith(".gov") or host.endswith(".mil") or host.endswith(".us"):
            return True
    return False


def needs_source(rel):
    top = rel.split("/")[0]
    return top in BY_SLUG or rel in SOURCED_GUIDES


def negated(text, start):
    return re.search(r"\b(not|never|no|nor|isn'?t|aren'?t|without)\b[^.]{0,40}$", text[max(0, start - 55) : start], re.I)


def scan(raw, rel):
    text = visible(raw)
    top = rel.split("/")[0]
    legal = top in LEGAL_PAGES or rel == "404.html"
    found = []
    for number, pattern in KW.items():
        for match in re.finditer(pattern, text, re.I):
            if number == 8 and match.group(0).lower() == "dmca" and (
                top == "copyright" or text[max(0, match.start() - 14) : match.end()] == "Copyright and DMCA"
            ):
                continue
            if number in (5, 7) and negated(text, match.start()):
                continue
            if number == 7 and re.match(
                r"\s+(the\s+)?(superintendent|department|state|division|board|commission|agency|secretary|director)\b",
                text[match.end() : match.end() + 60],
                re.I,
            ):
                # Statute quote: a course approved or certified by a public office, not this site.
                continue
            found.append((number, match.group(0), "keyword tripwire; review"))
            break
    for pattern, why in STRAY:
        match = re.search(pattern, text, re.I)
        if match:
            found.append(("trademark", match.group(0), "stray trademark: " + why))
            break
    if not legal:
        email = re.search(r"[\w.+-]+@[\w-]+\.[a-z][\w.]+", text)
        if email:
            found.append((2, email.group(0), "email address"))
        phone = re.search(r"(?<![\w/.:,-])(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w-])", text)
        if phone:
            found.append((2, phone.group(0).strip(), "possible phone number"))
        street = re.search(
            r"\b\d{1,5}\s+[A-Z][a-z]+(\s[A-Z][a-z]+)*\s(Street|St|Road|Rd|Drive|Dr|Avenue|Ave|Lane|Ln|Court|Ct|Boulevard|Blvd)\b",
            text,
        )
        if street:
            found.append((2, street.group(0), "possible street address"))
    remote = re.search(r"""<(?:img|source|video)[^>]+src=["'](https?://[^"']+)""", raw, re.I)
    if remote:
        found.append((3, remote.group(1), "remote image or video"))
    if needs_source(rel) and not official_link(raw):
        found.append((4, "(no official source URL)", "unsourced claim: page cites no .gov, .mil, or .us source"))
    if re.search(r"\$\d", text) and not official_link(raw) and not legal:
        found.append(("unsourced", "$", "unsourced claim: dollar amount without an official source link"))
    return text, found


def severity(found):
    nums = [item[0] for item in found if isinstance(item[0], int)]
    if any(n in HIGH for n in nums):
        return "HIGH"
    return "MODERATE" if found else None


def verdict(found, digest):
    if not found:
        return "PASS"
    if approved(digest):
        return "PASS (Joshua approved hash)"
    if severity(found) == "MODERATE" and not any(n in OBJECTIVE for n, _, _ in found if isinstance(n, int)) and cleared(digest):
        return "PASS (MODERATE, cleared hash)"
    return "HOLD_REVIEW"


def main(argv):
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    no_queue = "--no-queue" in argv
    bad = 0
    count = 0
    for rel in REQUIRED_LEGAL:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            bad += 1
            print("HOLD_REVIEW HIGH", rel, "legal page missing")
    home = os.path.join(ROOT, "index.html")
    if os.path.isfile(home):
        home_html = open(home, encoding="utf-8").read()
        for rel in REQUIRED_LEGAL:
            href = "/" + rel[: -len("index.html")]
            if f'href="{href}"' not in home_html:
                bad += 1
                print("HOLD_REVIEW HIGH", "index.html", "legal page not linked", href)
    for path in sorted(glob.glob(os.path.join(ROOT, "**/*.html"), recursive=True)):
        if "/_build/" in path or "/_research/" in path:
            continue
        rel = os.path.relpath(path, ROOT)
        raw = open(path, encoding="utf-8").read()
        text, found = scan(raw, rel)
        digest = hashlib.sha256(text.encode()).hexdigest()
        result = verdict(found, digest)
        count += 1
        if result == "HOLD_REVIEW":
            bad += 1
            print("HOLD_REVIEW", severity(found), rel, "sha256", digest[:12])
            for rule, excerpt, why in found:
                print(f"  rule {rule}: {excerpt!r} {why}")
            if not no_queue and os.path.isdir(os.path.dirname(Q)):
                os.makedirs(DR, exist_ok=True)
                draft = os.path.join(DR, rel.replace("/", "__") + ".HOLD_REVIEW.html")
                open(draft, "w", encoding="utf-8").write(raw)
                title = (re.search(r"<title>(.*?)</title>", raw) or [None, rel])[1]
                open(Q, "a", encoding="utf-8").write(
                    json.dumps(
                        {
                            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                            "site": SITE,
                            "bot": BOT,
                            "title": html.unescape(title),
                            "flagged": "; ".join(f"[{rule}] {excerpt}" for rule, excerpt, _why in found),
                            "severity": severity(found),
                            "draft_path": draft,
                            "sha256": digest,
                            "status": "HOLD_REVIEW",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        elif found:
            print(result, rel)
    print(f"legal gate: {count} pages checked, {bad} HOLD_REVIEW")
    return 3 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
