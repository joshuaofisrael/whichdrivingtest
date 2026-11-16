"""Page bodies. Every age, hour, and fee is interpolated from verified state data."""

import json
import os
import re

from geo import BORDERS, BY_SLUG, EDL_SLUGS, REGIONS, RELATED, STATES, in_place, name_of, region_groups
from render import (
    BANNER,
    CHECKED_LABEL,
    DOMAIN,
    LEGAL_LINE,
    SITE,
    article_schema,
    breadcrumb_schema,
    btn,
    byline,
    crumbs_html,
    esc,
    ext,
    facts_table,
    faq_block,
    faq_schema,
    internal,
    missing,
    related_block,
    sources_block,
)

FED_PATH = os.path.join(os.path.dirname(__file__), "data", "federal.json")

TOPIC_META = [
    ("permit", "Learner permit"),
    ("written-test", "Written test"),
    ("road-test", "Road test"),
    ("real-id", "REAL ID and documents"),
    ("fees", "Fees"),
    ("transfer", "License from another state"),
    ("teen", "Teen licensing"),
]

URL_KEYS = [
    "agency_home",
    "permit_age_url",
    "license_age_url",
    "full_license_age_url",
    "written_url",
    "road_url",
    "scheduled_url",
    "handbook_url",
    "supervised_url",
    "holding_url",
    "fee_page_url",
    "real_id_url",
    "transfer_url",
    "teen_url",
    "out_of_state_permit_url",
    "curfew_url",
    "passengers_url",
]


def clean_desc(text):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 155:
        raise SystemExit(f"description {len(text)} > 155: {text}")
    return text


def clean_title(text):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 70:
        raise SystemExit(f"title {len(text)} > 70: {text}")
    return text


def agency_of(st):
    return st.get("agency") or "The state licensing agency"


def short_of(st):
    return st.get("agency_short") or agency_of(st)


def shown(text):
    text = (text or "").strip()
    if text and text[-1] not in ".!?":
        text += "."
    return esc(text)


def sentence(text, url=None, label="Source"):
    if not text:
        return ""
    link = f" {ext(url, label)}" if url else ""
    return f"<p>{esc(text)}{link}</p>"


def load_federal():
    with open(FED_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def sources_for(st):
    items = []
    for src in st.get("sources") or []:
        if src.get("url"):
            items.append(src)
    publisher = agency_of(st)
    for key in URL_KEYS:
        url = st.get(key)
        if url:
            items.append({"title": publisher, "url": url, "publisher": publisher})
    for fee in st.get("fees") or []:
        if fee.get("url"):
            items.append({"title": fee.get("item") or "Fee", "url": fee["url"], "publisher": publisher})
    for doc in st.get("documents") or []:
        if doc.get("url"):
            items.append({"title": doc.get("item") or "Documents", "url": doc["url"], "publisher": publisher})
    for point in st.get("teen_points") or []:
        if point.get("url"):
            items.append({"title": "Teen licensing", "url": point["url"], "publisher": publisher})
    return items


def ready_topics(st):
    docs = st.get("documents") or []
    fees = st.get("fees") or []
    teen_bits = [
        st.get("teen_summary"),
        st.get("supervised_hours"),
        st.get("curfew"),
        st.get("passengers"),
        st.get("holding_period"),
    ]
    teen_url = st.get("teen_url") or st.get("supervised_url") or st.get("curfew_url") or st.get("holding_url")
    return {
        "permit": bool(st.get("permit_age") and st.get("permit_age_url")),
        "written-test": bool(st.get("written_required") and st.get("written_url") and (st.get("written_detail") or st.get("handbook_url"))),
        "road-test": bool(st.get("road_required") and st.get("road_url") and (st.get("road_detail") or st.get("scheduled_url") or st.get("handbook_url"))),
        "real-id": bool((st.get("real_id_url") or any(d.get("url") for d in docs)) and (docs or st.get("real_id_summary"))),
        "fees": bool(fees),
        "transfer": bool(st.get("transfer_summary") and st.get("transfer_url") and len(st.get("transfer_summary") or "") >= 40),
        "teen": bool(teen_url and any(teen_bits)),
    }


def publishable(st):
    if st.get("slug") not in BY_SLUG:
        return False
    if not any(st.get(k) for k in URL_KEYS):
        return False
    keys = (
        "permit_age",
        "license_age",
        "full_license_age",
        "written_required",
        "road_required",
        "supervised_hours",
        "documents",
        "fees",
        "transfer_summary",
        "real_id_summary",
        "teen_summary",
    )
    return any(st.get(k) for k in keys)


def nearby(slug, published):
    borders = [s for s in BORDERS.get(slug, []) if s in published]
    if borders:
        return "Nearby states", borders[:4]
    related = [s for s in RELATED.get(slug, []) if s in published]
    return "Also see", related[:3]


def related_for(st, topics, published, skip=None):
    links = []
    if skip is not None:
        links.append((f"/{st['slug']}/", f"{st['name']} overview"))
    for key, label in TOPIC_META:
        if key == skip or not topics.get(key):
            continue
        links.append((f"/{st['slug']}/{key}/", f"{st['name']} {label.lower()}"))
    links.append(("/guides/how-to-use/", "How to use these guides"))
    if skip == "real-id":
        links.append(("/guides/real-id/", "Federal REAL ID rule"))
    if skip in (None, "permit"):
        links.append(("/guides/learner-permit-ages/", "Permit ages by state"))
    if skip in (None, "teen"):
        links.append(("/guides/teen-licensing/", "Teen licensing by state"))
    _heading, slugs = nearby(st["slug"], published)
    for slug in slugs[:3]:
        links.append((f"/{slug}/", name_of(slug)))
    deduped = []
    seen = set()
    for href, label in links:
        if href in seen:
            continue
        seen.add(href)
        deduped.append((href, label))
    return deduped


def doc_list(st):
    docs = st.get("documents") or []
    if not docs:
        return f"<p>{esc(missing())} Use the agency page for the list to bring.</p>"
    items = []
    for doc in docs:
        label = esc(doc.get("item") or "Document")
        summary = esc(doc.get("summary") or "")
        link = f" {ext(doc['url'], 'Source')}" if doc.get("url") else ""
        items.append(f"<li><strong>{label}.</strong> {summary}{link}</li>")
    return (
        "<ul>"
        + "".join(items)
        + "</ul><p>This is a short reading of the official list, not the filing packet itself. Bring what the agency page names.</p>"
    )


def fee_table(st):
    rows = []
    for fee in st.get("fees") or []:
        link = ext(fee["url"], "Source") if fee.get("url") else ""
        rows.append(f"<tr><td>{esc(fee.get('item') or 'Fee')}</td><td>{esc(fee.get('amount') or '')}</td><td>{link}</td></tr>")
    return (
        '<div class="tablewrap"><table class="list"><thead><tr><th>Item</th><th>Amount published</th><th>Source</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        "<p>If a fee you need is not in this table, it was not confirmed. This guide does not guess a price. Pay the agency, not a third party site that offers to file for you.</p>"
    )


def buttons(st):
    links = []
    if st.get("agency_home"):
        links.append(btn(st["agency_home"], f"{short_of(st)} home"))
    if st.get("scheduled_url"):
        links.append(btn(st["scheduled_url"], "Scheduling page"))
    if st.get("handbook_url"):
        links.append(btn(st["handbook_url"], "Handbook"))
    if not links:
        return ""
    return '<p class="btnrow">' + "".join(links) + "</p>"


def frame(h1, crumbs, inner, faqs, sources, links, legal=False):
    parts = [crumbs_html(crumbs), '<article class="prose wide">', f"<h1>{esc(h1)}</h1>"]
    if not legal:
        parts.append(byline())
    parts.append(BANNER)
    parts.append(inner)
    if faqs:
        parts.append(faq_block(faqs))
    if sources:
        parts.append(sources_block(sources))
    if links:
        parts.append(related_block(links))
    if legal:
        parts.append(LEGAL_LINE)
    parts.append("</article>")
    return "".join(parts)


def pack(path, title, description, nav, body, schemas):
    return {
        "path": path,
        "title": clean_title(title),
        "description": clean_desc(description),
        "nav": nav,
        "body": body,
        "schemas": schemas,
    }


def content_schemas(h1, path, crumbs, faqs, about=None):
    schemas = [breadcrumb_schema(crumbs), article_schema(h1, path, about)]
    if faqs:
        schemas.append(faq_schema(faqs))
    return schemas


def state_faqs(st):
    name = st["name"]
    place = in_place(name)
    agency = short_of(st)
    faqs = []
    docs = st.get("documents") or []
    if docs:
        items = ", ".join(d.get("item") or "a listed document" for d in docs[:5])
        faqs.append(
            (
                f"What should I bring for a {name} driver license or permit?",
                f"{agency} publishes a document list that includes {items}. Bring the originals they name. This page only shortens that list.",
            )
        )
    else:
        faqs.append(
            (
                f"What should I bring for a {name} driver license or permit?",
                f"A full document list was not confirmed on the pages checked {CHECKED_LABEL}. Start with the {agency} site linked here.",
            )
        )
    if st.get("out_of_state_permit"):
        faqs.append((f"Can I use a learner permit from another state in {place}?", st["out_of_state_permit"]))
    else:
        faqs.append(
            (
                f"Can I use a learner permit from another state in {place}?",
                f"The {agency} pages checked on {CHECKED_LABEL} do not clearly say that a learner permit from another state is accepted. Confirm with {agency} before you drive or apply.",
            )
        )
    if st.get("scheduled_url"):
        faqs.append(
            (
                f"How do I book the {name} road test?",
                f"Use the official scheduling link on this page. Book through {agency}, not a third party site that charges to file for you.",
            )
        )
    else:
        faqs.append(
            (
                f"How do I book the {name} road test?",
                f"A public scheduling link was not confirmed on the pages we checked. Start at the {agency} site linked here and follow their appointment steps.",
            )
        )
    fees = st.get("fees") or []
    if fees:
        bits = "; ".join(f"{f.get('item')} {f.get('amount')}" for f in fees[:4])
        faqs.append(
            (
                f"Where are {name} license and permit fees listed?",
                f"{agency} publishes these amounts: {bits}. Fees change. Read the official fee page before you pay.",
            )
        )
    elif st.get("fee_page_url"):
        faqs.append(
            (
                f"Where are {name} license and permit fees listed?",
                f"A dollar amount was not confirmed for this guide, so none is shown. The official fee page is linked here. Pay {agency} directly.",
            )
        )
    else:
        faqs.append(
            (
                f"Where are {name} license and permit fees listed?",
                f"A current fee table was not confirmed on the pages we checked, so this guide does not guess a price. Use the {agency} site before you pay.",
            )
        )
    return faqs


def state_page(st, topics, published):
    name = st["name"]
    place = in_place(name)
    agency = agency_of(st)
    path = f"{st['slug']}/"
    h1 = f"{name} driving test requirements and DMV guide"
    title = h1
    description = f"{name}: permit and license ages, written and road tests, REAL ID, and official DMV links."
    crumbs = [("Home", "/"), (name, "/" + path)]
    quick = []
    if st.get("permit_age"):
        quick.append(f"<li><strong>Learner permit:</strong> {shown(st['permit_age'])}</li>")
    else:
        quick.append(f"<li><strong>Learner permit:</strong> {esc(missing())}</li>")
    if st.get("license_age"):
        quick.append(f"<li><strong>First license:</strong> {shown(st['license_age'])}</li>")
    else:
        quick.append(f"<li><strong>First license:</strong> {esc(missing())}</li>")
    if st.get("written_required"):
        quick.append(f"<li><strong>Written test:</strong> {esc(st['written_required'])}</li>")
    else:
        quick.append(f"<li><strong>Written test:</strong> {esc(missing())}</li>")
    if st.get("road_required"):
        quick.append(f"<li><strong>Road test:</strong> {esc(st['road_required'])}</li>")
    else:
        quick.append(f"<li><strong>Road test:</strong> {esc(missing())}</li>")
    rows = []
    rows.append(("Learner permit", esc(st["permit_age"]) if st.get("permit_age") else esc(missing())))
    rows.append(("Written test", esc(st["written_required"]) if st.get("written_required") else esc(missing())))
    rows.append(("Supervised driving", esc(st["supervised_hours"]) if st.get("supervised_hours") else esc(missing())))
    rows.append(("Road test", esc(st["road_required"]) if st.get("road_required") else esc(missing())))
    rows.append(("First license", esc(st["license_age"]) if st.get("license_age") else esc(missing())))
    rows.append(("Full license", esc(st["full_license_age"]) if st.get("full_license_age") else esc(missing())))
    if st.get("real_id_summary"):
        real_cell = esc(st["real_id_summary"])
    elif st.get("real_id_url"):
        real_cell = ext(st["real_id_url"], "Official REAL ID page")
    else:
        real_cell = esc(missing())
    if topics.get("real-id"):
        real_cell += f' <a href="/{st["slug"]}/real-id/">Document guide</a>'
    rows.append(("REAL ID", real_cell))
    if st.get("fees"):
        fee_cell = "; ".join(f"{esc(f.get('item'))}: {esc(f.get('amount'))}" for f in st["fees"][:6])
        if topics.get("fees"):
            fee_cell += f' <a href="/{st["slug"]}/fees/">Fee details</a>'
    elif st.get("fee_page_url"):
        fee_cell = ext(st["fee_page_url"], "Official fee page") + ". No dollar amount was confirmed, so none is shown."
    else:
        fee_cell = esc(missing()) + " No dollar amount is shown."
    rows.append(("Fees", fee_cell))
    inner = [
        f"<p>This is a short guide to the driving test and license rules in {esc(place)}. It is written from {esc(agency)} pages opened on {esc(CHECKED_LABEL)}.</p>",
        '<div class="answer"><p><strong>Quick answer</strong></p><ul>' + "".join(quick) + "</ul></div>",
        buttons(st),
        "<h2>At a glance</h2>",
        facts_table(rows),
        "<p>A line that says the point was not clearly published is not a zero and not a waiver. The agency page controls.</p>",
        "<h2>Documents</h2>",
        doc_list(st),
    ]
    if topics.get("transfer") or st.get("transfer_summary"):
        inner.append("<h2>License from another state</h2>")
        inner.append(sentence(st.get("transfer_summary"), st.get("transfer_url"), "Transfer rules"))
        if topics.get("transfer"):
            inner.append(f'<p>More detail is on the <a href="/{st["slug"]}/transfer/">transfer guide</a>.</p>')
    if topics.get("teen") or st.get("teen_summary") or st.get("supervised_hours"):
        inner.append("<h2>Teen drivers</h2>")
        if st.get("teen_summary"):
            inner.append(sentence(st["teen_summary"], st.get("teen_url") or st.get("supervised_url"), "Teen rules"))
        elif st.get("supervised_hours"):
            inner.append(sentence(st["supervised_hours"], st.get("supervised_url"), "Practice hours"))
        if topics.get("teen"):
            inner.append(f'<p>Hours, night rules, and passenger limits are on the <a href="/{st["slug"]}/teen/">teen licensing guide</a>.</p>')
    topic_bits = []
    for key, label in TOPIC_META:
        if topics.get(key):
            topic_bits.append(f'<li><a href="/{st["slug"]}/{key}/">{esc(label)}</a></li>')
    if topic_bits:
        inner.append("<h2>Guides for this state</h2><ul>" + "".join(topic_bits) + "</ul>")
    faqs = state_faqs(st)
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published))
    return pack(path, title, description, None, body, content_schemas(h1, path, crumbs, faqs, name))


def permit_page(st, topics, published):
    name = st["name"]
    place = in_place(name)
    path = f"{st['slug']}/permit/"
    h1 = f"{name} learner permit requirements"
    description = f"{name} learner permit age, practice hours, and the official application page."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("Learner permit", "/" + path)]
    inner = [
        sentence(
            f"In {place}, {agency_of(st)} publishes {st['permit_age']} as the minimum age for a learner permit.",
            st.get("permit_age_url"),
            "Permit age",
        ),
        '<div class="answer"><p><strong>Quick answer</strong></p><ul>'
        + f"<li><strong>Minimum age:</strong> {shown(st['permit_age'])}</li>"
        + (f"<li><strong>Holding period:</strong> {shown(st['holding_period'])}</li>" if st.get("holding_period") else f"<li><strong>Holding period:</strong> {esc(missing())}</li>")
        + (f"<li><strong>Practice hours:</strong> {shown(st['supervised_hours'])}</li>" if st.get("supervised_hours") else f"<li><strong>Practice hours:</strong> {esc(missing())}</li>")
        + "</ul></div>",
        buttons(st),
        "<h2>Age and holding period</h2>",
        sentence(st.get("holding_period"), st.get("holding_url") or st.get("permit_age_url"), "Holding period")
        or f"<p>A minimum time to hold the permit was {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Practice driving</h2>",
        sentence(st.get("supervised_hours"), st.get("supervised_url"), "Practice hours")
        or f"<p>Supervised driving hours were {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Knowledge test</h2>",
        sentence(st.get("written_required"), st.get("written_url"), "Written test")
        or f"<p>Whether a written test is required before the permit was {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>What to check next</h2>",
        "<ol><li>Open the official permit page linked on this guide.</li>"
        "<li>Confirm the age and any practice hours still match.</li>"
        "<li>Book only on an official scheduling page, if one is linked.</li></ol>",
    ]
    faqs = [
        (
            f"How old must I be for a learner permit in {place}?",
            f"{short_of(st)} publishes {st['permit_age']} as the minimum age for a learner permit.",
        ),
        (
            f"How long do I hold a {name} learner permit?",
            st["holding_period"]
            if st.get("holding_period")
            else f"A holding period was not clearly published on the pages checked {CHECKED_LABEL}.",
        ),
        (
            f"How many supervised hours does {name} publish?",
            st["supervised_hours"]
            if st.get("supervised_hours")
            else "Supervised driving hours were not clearly published on the pages we checked.",
        ),
    ]
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published, "permit"))
    return pack(path, h1, description, None, body, content_schemas(h1, path, crumbs, faqs, f"{name} learner permit"))


def written_page(st, topics, published):
    name = st["name"]
    path = f"{st['slug']}/written-test/"
    h1 = f"{name} written driving test"
    description = f"{name} knowledge test: what the agency requires, and the official handbook."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("Written test", "/" + path)]
    inner = [
        sentence(st.get("written_required"), st.get("written_url"), "Written test"),
        '<div class="answer"><p><strong>Quick answer</strong></p><p>'
        + esc(st.get("written_detail") or st.get("written_required") or missing())
        + "</p></div>",
        buttons(st),
        "<h2>Format</h2>",
        sentence(st.get("written_detail"), st.get("written_url"), "Test format")
        or f"<p>Question count, languages, and passing score were {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Handbook</h2>",
        (
            f"<p>Study from the official handbook. {ext(st['handbook_url'], 'Official handbook')}</p>"
            if st.get("handbook_url")
            else f"<p>An official handbook link was {esc(missing()[0].lower() + missing()[1:])}</p>"
        ),
    ]
    faqs = [
        (
            f"Does {name} require a written driving test?",
            st.get("written_required") or "That point was not clearly published on the pages we checked.",
        ),
        (
            f"What is the {name} written test format?",
            st.get("written_detail") or "Question count and passing score were not clearly published on the pages we checked.",
        ),
        (
            f"Where is the official {name} driver handbook?",
            "The handbook link is on this page."
            if st.get("handbook_url")
            else "A handbook link was not confirmed on the pages we checked. Start at the agency home page.",
        ),
    ]
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published, "written-test"))
    return pack(path, h1, description, None, body, content_schemas(h1, path, crumbs, faqs, f"{name} written test"))


def road_page(st, topics, published):
    name = st["name"]
    place = in_place(name)
    path = f"{st['slug']}/road-test/"
    h1 = f"{name} road test requirements"
    description = f"{name} road test: what the agency requires, what to bring, and how to schedule."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("Road test", "/" + path)]
    inner = [
        sentence(st.get("road_required"), st.get("road_url"), "Road test"),
        '<div class="answer"><p><strong>Quick answer</strong></p><p>'
        + esc(st.get("road_detail") or st.get("road_required") or missing())
        + "</p></div>",
        buttons(st),
        "<h2>What the agency says to expect</h2>",
        sentence(st.get("road_detail"), st.get("road_url"), "Road test details")
        or f"<p>Vehicle rules and what to bring were {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Scheduling</h2>",
        (
            f"<p>Book on the official page only. {ext(st['scheduled_url'], 'Official scheduling page')}</p>"
            if st.get("scheduled_url")
            else f"<p>A public scheduling link for {esc(place)} was {esc(missing()[0].lower() + missing()[1:])}</p>"
        ),
    ]
    faqs = [
        (
            f"Is a road test required in {place}?",
            st.get("road_required") or "That point was not clearly published on the pages we checked.",
        ),
        (
            f"What should I bring to the {name} road test?",
            st.get("road_detail") or "What to bring was not clearly published on the pages we checked. Use the official road test page.",
        ),
        (
            f"How do I schedule the {name} road test?",
            "Use the official scheduling link on this page."
            if st.get("scheduled_url")
            else f"A scheduling link was not confirmed. Start at the {short_of(st)} site.",
        ),
    ]
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published, "road-test"))
    return pack(path, h1, description, None, body, content_schemas(h1, path, crumbs, faqs, f"{name} road test"))


def realid_page(st, topics, published):
    name = st["name"]
    place = in_place(name)
    path = f"{st['slug']}/real-id/"
    h1 = f"{name} REAL ID documents"
    description = f"{name} REAL ID and the identity documents the licensing agency publishes."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("REAL ID", "/" + path)]
    inner = [
        "<p>REAL ID is a federal card standard. TSA says enforcement began on May 7, 2025, for boarding a federally regulated commercial aircraft, certain federal facilities, and nuclear power plants. A state may still issue a license that is not REAL ID compliant. Driving rules come from the state. "
        '<a href="/guides/real-id/">Federal REAL ID guide</a>.</p>',
        sentence(st.get("real_id_summary"), st.get("real_id_url"), "State REAL ID page"),
        '<div class="answer"><p><strong>Quick answer</strong></p><p>Use the state list below for documents. Use TSA only for the federal purpose of the card.</p></div>',
        buttons(st),
        "<h2>Documents the state page lists</h2>",
        doc_list(st),
    ]
    if st["slug"] in EDL_SLUGS:
        inner.append(
            f"<p>TSA lists {esc(name)} among five states that issue an Enhanced Driver License accepted for REAL ID purposes. Confirm the card type with {esc(short_of(st))}.</p>"
        )
    faqs = [
        (
            f"Is a REAL ID required to drive in {place}?",
            "TSA describes REAL ID for federal purposes such as commercial flights and certain federal facilities. Driving privileges come from the state license. This guide does not treat REAL ID as the rule for whether you may drive.",
        ),
        (
            f"What documents does {name} list for a REAL ID?",
            "The short list on this page is drawn from the state agency. The official page is the list to bring.",
        ),
        (
            f"Does {name} issue an Enhanced Driver License?",
            f"TSA lists {name} as one of five Enhanced Driver License states."
            if st["slug"] in EDL_SLUGS
            else "The federal guide names the five Enhanced Driver License states. Confirm any card mark with the state agency.",
        ),
    ]
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published, "real-id"))
    return pack(path, h1, description, "realid", body, content_schemas(h1, path, crumbs, faqs, f"{name} REAL ID"))


def fees_page(st, topics, published):
    name = st["name"]
    path = f"{st['slug']}/fees/"
    h1 = f"{name} DMV license fees"
    description = f"Published {name} driver license and permit fees, taken only from the official fee page."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("Fees", "/" + path)]
    inner = [
        f"<p>These are dollar amounts printed by {esc(agency_of(st))}. Amounts that were not confirmed are left out on purpose.</p>",
        fee_table(st),
        buttons(st),
    ]
    shown = "; ".join(f"{f.get('item')} {f.get('amount')}" for f in st.get("fees") or [])
    faqs = [
        (f"Which {name} fees are published here?", shown or "No confirmed dollar amount is listed."),
        (
            f"What if the {name} fee I need is missing?",
            "It was not confirmed on the official page we checked, so it is not guessed. Use the agency fee page before you pay.",
        ),
        (
            "Should I pay a website that offers to file my license paperwork?",
            f"Pay {short_of(st)} on the official site. This guide does not sell filing help.",
        ),
    ]
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published, "fees"))
    return pack(path, h1, description, None, body, content_schemas(h1, path, crumbs, faqs, f"{name} license fees"))


def transfer_page(st, topics, published):
    name = st["name"]
    place = in_place(name)
    path = f"{st['slug']}/transfer/"
    h1 = f"{name} license transfer rules"
    description = f"Moving a driver license to {place}, from the official agency page."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("Transfer", "/" + path)]
    inner = [
        sentence(st.get("transfer_summary"), st.get("transfer_url"), "Transfer rules"),
        "<p>If this summary does not say whether a knowledge test or a road test is waived, the pages we checked did not make that clear. Read the official page before you skip a test.</p>",
        buttons(st),
    ]
    if st.get("out_of_state_permit"):
        inner.append("<h2>Learner permit from another state</h2>")
        inner.append(sentence(st["out_of_state_permit"], st.get("out_of_state_permit_url"), "Permit from another state"))
    faqs = [
        (
            f"How do I transfer a license to {place}?",
            st.get("transfer_summary") or "The official transfer page linked here is the rule to follow.",
        ),
        (
            f"Does {name} waive the tests for a new resident?",
            "Only if the summary on this page says so. If it does not, the pages we checked did not make a waiver clear.",
        ),
        (
            f"Can I drive in {place} on a learner permit from another state?",
            st.get("out_of_state_permit")
            or f"That point was not clearly published on the {short_of(st)} pages checked {CHECKED_LABEL}.",
        ),
    ]
    body = frame(h1, crumbs, "".join(inner), faqs, sources_for(st), related_for(st, topics, published, "transfer"))
    return pack(path, h1, description, None, body, content_schemas(h1, path, crumbs, faqs, f"{name} license transfer"))


def teen_page(st, topics, published):
    name = st["name"]
    place = in_place(name)
    path = f"{st['slug']}/teen/"
    h1 = f"{name} teen driver license rules"
    description = f"{name} graduated teen licensing: hours, night rules, and passenger limits when published."
    crumbs = [("Home", "/"), (name, f"/{st['slug']}/"), ("Teen licensing", "/" + path)]
    bits = []
    if st.get("permit_age"):
        bits.append(f"<li><strong>Learner permit:</strong> {shown(st['permit_age'])}</li>")
    if st.get("license_age"):
        bits.append(f"<li><strong>First license:</strong> {shown(st['license_age'])}</li>")
    if st.get("full_license_age"):
        bits.append(f"<li><strong>Full license:</strong> {shown(st['full_license_age'])}</li>")
    if st.get("supervised_hours"):
        bits.append(f"<li><strong>Practice hours:</strong> {shown(st['supervised_hours'])}</li>")
    if st.get("curfew"):
        bits.append(f"<li><strong>Night rule:</strong> {shown(st['curfew'])}</li>")
    if st.get("passengers"):
        bits.append(f"<li><strong>Passengers:</strong> {shown(st['passengers'])}</li>")
    inner = [
        f"<p>Teen licensing in {esc(place)} is the graduated path published by {esc(agency_of(st))}. Adult applicants can have different rules.</p>",
        sentence(st.get("teen_summary"), st.get("teen_url") or st.get("supervised_url"), "Teen rules"),
        '<div class="answer"><p><strong>Quick answer</strong></p><ul>' + "".join(bits) + "</ul></div>" if bits else "",
        buttons(st),
        "<h2>Practice hours</h2>",
        sentence(st.get("supervised_hours"), st.get("supervised_url"), "Practice hours")
        or f"<p>Supervised hours were {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Night driving</h2>",
        sentence(st.get("curfew"), st.get("curfew_url"), "Night rule")
        or f"<p>A night restriction was {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Passengers</h2>",
        sentence(st.get("passengers"), st.get("passengers_url"), "Passenger rule")
        or f"<p>A passenger limit was {esc(missing()[0].lower() + missing()[1:])}</p>",
        "<h2>Holding period and full license</h2>",
        sentence(st.get("holding_period"), st.get("holding_url"), "Holding period") or "",
        sentence(st.get("full_license_age"), st.get("full_license_age_url"), "Full license age") or "",
    ]
    for point in st.get("teen_points") or []:
        inner.append(sentence(point.get("text"), point.get("url"), "Teen rules"))
    faqs = [
        (
            f"How many practice hours does {name} require for teens?",
            st.get("supervised_hours") or "Practice hours were not clearly published on the pages we checked.",
        ),
        (
            f"Is there a night driving rule for teens in {place}?",
            st.get("curfew") or "A night restriction was not clearly published on the pages we checked.",
        ),
        (
            f"Are teen passengers limited in {place}?",
            st.get("passengers") or "A passenger limit was not clearly published on the pages we checked.",
        ),
    ]
    body = frame(h1, crumbs, "".join(x for x in inner if x), faqs, sources_for(st), related_for(st, topics, published, "teen"))
    return pack(path, h1, description, None, body, content_schemas(h1, path, crumbs, faqs, f"{name} teen licensing"))


TOPIC_BUILDERS = {
    "permit": permit_page,
    "written-test": written_page,
    "road-test": road_page,
    "real-id": realid_page,
    "fees": fees_page,
    "transfer": transfer_page,
    "teen": teen_page,
}


def home_page(states):
    complete = len(states) == 51
    h1 = "Driving test requirements for every state" if complete else "Driving test requirements by state"
    title = "Which Driving Test: driving test rules by state"
    description = (
        "Driving test, learner permit, REAL ID, and DMV fee guides for every state and D.C., from official pages."
        if complete
        else "Driving test, learner permit, REAL ID, and DMV fee guides from official state agency pages."
    )
    groups = region_groups()
    by_slug = {st["slug"]: st for st in states}
    cards = []
    for region in REGIONS:
        items = []
        for slug, name in groups[region]:
            st = by_slug.get(slug)
            if not st:
                items.append(f'<li class="card" data-state="{esc(name)}"><h3>{esc(name)}</h3><p>Guide not published yet. The official rules were not confirmed.</p></li>')
                continue
            age = f"Permit: {esc(st['permit_age'])}" if st.get("permit_age") else "Official guide"
            items.append(
                f'<li class="card" data-state="{esc(name)}"><h3><a href="/{esc(slug)}/">{esc(name)}</a></h3><p>{age}</p></li>'
            )
        cards.append(f'<h2 id="{region.lower()}">{esc(region)}</h2><ul class="cards">{"".join(items)}</ul>')
    faqs = [
        (
            "Is Which Driving Test a government site?",
            "No. It is an independent guide. The state licensing agency page controls, and this site is not legal advice.",
        ),
        (
            "Do you list every DMV fee?",
            "No. A dollar amount appears only when the official agency page prints it. Missing fees are left blank on purpose.",
        ),
        (
            "Which state guide should I read?",
            "Read the state where you will apply. For a move, that is your new state. Then open the official link and confirm the figure.",
        ),
    ]
    inner = f"""
<section class="hero"><h1>{esc(h1)}</h1>
{byline()}
{BANNER}
<div class="answer"><p><strong>How to use this guide</strong></p>
<p>Pick the state where you will apply. Each published guide covers the learner permit, the written test, the road test, REAL ID documents, published fees, a license from another state, and teen graduated licensing. Then confirm the figure on the official agency page. Checked {esc(CHECKED_LABEL)}.</p></div>
<p class="btnrow"><a class="btn" href="/states/">Browse all states</a> <a class="btn alt" href="/guides/how-to-use/">How to use this guide</a></p>
</section>
<label for="state-filter">Filter states</label>
<input id="state-filter" class="filter" type="search" placeholder="Type a state name" autocomplete="off">
{''.join(cards)}
<h2>Guides</h2>
<ul class="cols">
<li><a href="/guides/how-to-use/">How to use these guides</a></li>
<li><a href="/guides/real-id/">REAL ID, the federal rule</a></li>
<li><a href="/guides/learner-permit-ages/">Learner permit ages by state</a></li>
<li><a href="/guides/teen-licensing/">Teen licensing by state</a></li>
</ul>
{faq_block(faqs)}
"""
    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": SITE,
            "url": DOMAIN + "/",
            "description": description,
            "publisher": {
                "@type": "Organization",
                "name": SITE,
                "url": DOMAIN + "/",
                "logo": DOMAIN + "/logo.png",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": SITE,
            "url": DOMAIN + "/",
            "logo": DOMAIN + "/logo.png",
        },
        faq_schema(faqs),
    ]
    return pack("", title, description, "home", inner, schemas)


def states_index(states):
    h1 = "All state driving test guides"
    title = "All state driving test and DMV guides"
    description = "Every state and the District of Columbia. Open a guide, then confirm the rule on the official agency page."
    path = "states/"
    crumbs = [("Home", "/"), ("States", "/states/")]
    by_slug = {st["slug"]: st for st in states}
    groups = region_groups()
    blocks = []
    for region in REGIONS:
        lis = []
        for slug, name in groups[region]:
            if slug in by_slug:
                age = by_slug[slug].get("permit_age")
                note = f" Permit: {esc(age)}." if age else ""
                lis.append(f'<li data-state="{esc(name)}"><a href="/{esc(slug)}/">{esc(name)}</a>.{note}</li>')
            else:
                lis.append(f'<li data-state="{esc(name)}">{esc(name)}. Guide not published yet.</li>')
        blocks.append(f'<h2 id="{region.lower()}">{esc(region)}</h2><ul class="cols">{"".join(lis)}</ul>')
    inner_core = (
        "<p>Choose the state where you will apply. Each link opens a guide built from that state's licensing agency. "
        f"Checked {esc(CHECKED_LABEL)}.</p>"
        '<label for="state-filter">Filter states</label>'
        '<input id="state-filter" class="filter" type="search" placeholder="Type a state name" autocomplete="off">'
        + "".join(blocks)
    )
    faqs = []
    body = frame(h1, crumbs, inner_core, faqs, [], [( "/guides/how-to-use/", "How to use these guides"), ("/guides/learner-permit-ages/", "Permit ages by state")])
    return pack(path, title, description, "states", body, content_schemas(h1, path, crumbs, faqs, "US state driving tests"))


def guide_how():
    h1 = "How to use these driving test guides"
    title = h1
    description = "How to read these state driving test guides, what we leave out, and how to confirm a rule."
    path = "guides/how-to-use/"
    crumbs = [("Home", "/"), ("Guides", "/guides/"), ("How to use", "/" + path)]
    inner = """
<div class="answer"><p><strong>Quick answer</strong></p>
<p>Pick the state where you will apply, read the table, then open the official link and confirm the figure before you rely on it.</p></div>
<h2>Pick the right state</h2>
<p>Read the state that will issue the permit or license. If you are moving, that is the new state, not the one on your current card. A license from another state has its own section on the state page.</p>
<h2>Read the table, then the official page</h2>
<p>The state page leads with ages, whether a written test and a road test are required, practice hours, REAL ID, and fees. A fee appears only when the agency page prints a dollar amount. "Not clearly published" means we did not confirm it. It does not mean the rule is zero, waived, or free.</p>
<h2>REAL ID is not the same question as "may I drive"</h2>
<p>REAL ID is a federal card standard. Teen graduated licensing is the state path for young drivers. Both are linked from the state page. The <a href="/guides/real-id/">federal REAL ID guide</a> explains the federal part. The state page lists that state's documents.</p>
<h2>What we do not do</h2>
<p>We do not sell appointments, driving lessons, or insurance. We do not copy a whole handbook. We do not use test prep sites as sources. If a number is not on the official page we opened, it is not on this site.</p>
"""
    faqs = [
        (
            "Can I use this site instead of the state DMV?",
            "No. This is general information. The state agency page controls, and rules and fees change.",
        ),
        (
            "Why is a fee missing?",
            "Because a dollar amount was not confirmed on the official page. Missing means we did not guess.",
        ),
        (
            "How do I report a wrong figure?",
            "Email the address on the contact page with the page address and a link to the official agency page that shows the current rule.",
        ),
    ]
    links = [
        ("/states/", "All states"),
        ("/guides/real-id/", "Federal REAL ID rule"),
        ("/guides/learner-permit-ages/", "Permit ages by state"),
        ("/methodology/", "Sources and methods"),
        ("/disclaimer/", "Disclaimer"),
    ]
    body = frame(h1, crumbs, inner, faqs, [], links)
    return pack(path, title, description, "how", body, content_schemas(h1, path, crumbs, faqs, "How to use the guide"))


def guide_realid():
    fed = load_federal()
    h1 = "REAL ID rules for driver licenses"
    title = "REAL ID rules for state driver licenses"
    description = "REAL ID enforcement, the federal purpose, and links to each state's official document list."
    path = "guides/real-id/"
    crumbs = [("Home", "/"), ("Guides", "/guides/"), ("REAL ID", "/" + path)]
    purposes = "".join(f"<li>{esc(p)}</li>" for p in fed["purposes"])
    inner = f"""
<div class="answer"><p><strong>Quick answer</strong></p>
<p>{esc(fed["enforcement"])} The card is for federal purposes. Your state still sets the driving rules and the document list.</p></div>
<h2>What TSA says it is for</h2>
<p>TSA lists these federal purposes:</p>
<ul>{purposes}</ul>
<p>{ext(fed["sources"][1]["url"], "TSA REAL ID FAQ")}</p>
<p>{esc(fed["not_border"])} {esc(fed["not_cruise"])}</p>
<h2>A non compliant card can still be a license</h2>
<p>{esc(fed["noncompliant_ok"])} {esc(fed["noncompliant_mark"])}</p>
<p>That is why this site does not tell you that you cannot drive without a REAL ID star. Ask the state agency which card you need for driving, and use TSA's list for flights and federal facilities.</p>
<h2>Federal minimum documents</h2>
<p>TSA says that, at a minimum, applicants show full legal name, date of birth, Social Security number, two proofs of address of principal residence, and lawful status. States may ask for more. The state guide is the list to follow, not this sentence.</p>
<h2>Enhanced Driver Licenses</h2>
<p>{esc(fed["edl_states"])} Those five state guides call this out. Everyone else should use the state REAL ID page.</p>
<p>Checked {esc(CHECKED_LABEL)} on the <a href="{esc(fed["sources"][0]["url"])}">DHS REAL ID page</a> and the TSA FAQ.</p>
"""
    faqs = [
        (
            "When did REAL ID enforcement begin?",
            "TSA says REAL ID enforcement began on May 7, 2025.",
        ),
        (
            "Can I use a REAL ID to cross the border or board a cruise?",
            "TSA says REAL ID cards cannot be used for border crossings into Canada, Mexico, or other international travel, and cannot be used for international sea cruise travel.",
        ),
        (
            "Can a state still issue a license that is not REAL ID compliant?",
            "TSA says yes. That card must be marked as not acceptable for official federal purposes.",
        ),
        (
            "Which states issue an Enhanced Driver License?",
            "TSA names Michigan, Minnesota, New York, Vermont, and Washington.",
        ),
    ]
    sources = fed["sources"]
    body = frame(h1, crumbs, inner, faqs, sources, [("/states/", "All states"), ("/guides/how-to-use/", "How to use these guides")])
    return pack(path, title, description, "realid", body, content_schemas(h1, path, crumbs, faqs, "REAL ID"))


def guide_ages(states):
    h1 = "Learner permit age by state"
    title = "Learner permit age by state"
    description = "Learner permit and first license ages by state, each one taken from that state's official page."
    path = "guides/learner-permit-ages/"
    crumbs = [("Home", "/"), ("Guides", "/guides/"), ("Permit ages", "/" + path)]
    rows = []
    for st in sorted(states, key=lambda s: s["name"]):
        permit = esc(st["permit_age"]) if st.get("permit_age") else esc(missing())
        first = esc(st["license_age"]) if st.get("license_age") else esc(missing())
        href = f"/{st['slug']}/permit/" if st.get("_topics", {}).get("permit") else f"/{st['slug']}/"
        rows.append(f"<tr><td>{internal(href, st['name'])}</td><td>{permit}</td><td>{first}</td></tr>")
    inner = (
        "<p>This table lists a minimum age only when that state's licensing agency publishes it. "
        "A cell that says the age was not clearly published is not a guess and it is not zero.</p>"
        '<div class="tablewrap"><table class="list"><thead><tr><th>State</th><th>Learner permit</th><th>First license</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        f"<p>Checked {esc(CHECKED_LABEL)}. Open the state guide for the official link.</p>"
    )
    faqs = [
        (
            "Why does a cell say the age was not clearly published?",
            "The official pages we opened did not state a figure we could confirm. Check the state agency before you apply.",
        ),
        (
            "Is the permit age the same as the license age?",
            "Often no. The permit column is the learner stage. The first license column is the next stage the state publishes, which may be provisional.",
        ),
    ]
    body = frame(h1, crumbs, inner, faqs, [], [("/states/", "All states"), ("/guides/teen-licensing/", "Teen licensing by state")])
    return pack(path, title, description, None, body, content_schemas(h1, path, crumbs, faqs, "Learner permit ages"))


def guide_teen(states):
    h1 = "Teen driver licensing by state"
    title = "Teen driver licensing by state"
    description = "Teen practice hours, night rules, and passenger limits by state, when the agency publishes them."
    path = "guides/teen-licensing/"
    crumbs = [("Home", "/"), ("Guides", "/guides/"), ("Teen licensing", "/" + path)]
    rows = []
    for st in sorted(states, key=lambda s: s["name"]):
        href = f"/{st['slug']}/teen/" if st.get("_topics", {}).get("teen") else f"/{st['slug']}/"

        def cell(key):
            return esc(st[key]) if st.get(key) else esc(missing())

        rows.append(
            f"<tr><td>{internal(href, st['name'])}</td><td>{cell('supervised_hours')}</td><td>{cell('curfew')}</td><td>{cell('passengers')}</td></tr>"
        )
    inner = (
        "<p>Graduated licensing rules for teens differ by state. This table shows practice hours, night rules, and passenger limits only when the state agency publishes them.</p>"
        '<div class="tablewrap"><table class="list"><thead><tr><th>State</th><th>Practice hours</th><th>Night rule</th><th>Passengers</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        f"<p>Checked {esc(CHECKED_LABEL)}. Adult applicants should use the state overview, not this teen table.</p>"
    )
    faqs = [
        (
            "Does every state use the same teen curfew?",
            "No. A night rule appears here only when that state publishes one. Otherwise the cell says it was not clearly published.",
        ),
        (
            "Where are the ages?",
            "Permit and first license ages are on the permit age table and on each state page.",
        ),
    ]
    body = frame(
        h1,
        crumbs,
        inner,
        faqs,
        [],
        [("/guides/learner-permit-ages/", "Permit ages by state"), ("/states/", "All states")],
    )
    return pack(path, title, description, None, body, content_schemas(h1, path, crumbs, faqs, "Teen driver licensing"))


def guides_index():
    h1 = "Driving test guides"
    title = "Driving test guides"
    description = "How to use the state guides, REAL ID, permit ages, and teen licensing, with official sources."
    path = "guides/"
    crumbs = [("Home", "/"), ("Guides", "/guides/")]
    inner = """
<ul class="cols">
<li><a href="/guides/how-to-use/">How to use these guides</a></li>
<li><a href="/guides/real-id/">REAL ID, the federal rule</a></li>
<li><a href="/guides/learner-permit-ages/">Learner permit ages by state</a></li>
<li><a href="/guides/teen-licensing/">Teen licensing by state</a></li>
</ul>
<p>State pages are the place to confirm a figure. These guides compare them or explain the federal REAL ID rule.</p>
"""
    body = frame(h1, crumbs, inner, [], [], [("/states/", "All states"), ("/methodology/", "Sources and methods")])
    return pack(path, title, description, None, body, content_schemas(h1, path, crumbs, [], "Driving test guides"))


def legal_page(path, nav, h1, title, description, inner, legal=True):
    crumbs = [("Home", "/"), (h1, "/" + path)]
    lead = f"<p>Last updated {esc(CHECKED_LABEL)}.</p>" if legal else ""
    body = frame(h1, crumbs, lead + inner, [], [], [], legal=legal)
    schemas = [breadcrumb_schema(crumbs)]
    if not legal:
        schemas.append(article_schema(h1, path, h1))
    return pack(path, title, description, nav, body, schemas)


def static_pages():
    pages = []
    pages.append(
        legal_page(
            "about/",
            None,
            "About",
            "About Which Driving Test",
            "What Which Driving Test is, which states it covers, and how to send a correction.",
            """
<h2>What this site is</h2>
<p>Which Driving Test is an independent guide to state driving tests and license rules. It explains the learner permit, the written test, the road test, REAL ID documents, published fees, moving a license from another state, and teen graduated licensing. A state guide is published when that state's own licensing page can be checked. States still waiting on that check are listed without a guide.</p>
<h2>What this site is not</h2>
<p>It is not a state DMV, BMV, MVD, RMV, or secretary of state. It does not issue permits, book road tests, or take payment. It is not legal advice.</p>
<h2>How the pages are written</h2>
<p>Each state page is drawn from that state's own licensing agency and cites the page. See <a href="/methodology/">sources and methods</a>.</p>
<p>See a wrong figure? <a href="/contact/">Tell us</a> and include the official link.</p>
""",
            legal=False,
        )
    )
    pages.append(
        legal_page(
            "methodology/",
            None,
            "Sources and methods",
            "Sources and methods",
            "How Which Driving Test checks state DMV rules, and which sources it refuses to use.",
            """
<h2>Sources we use</h2>
<p>State pages use that state's official licensing agency only. The name differs. It may be a DMV, BMV, MVD, RMV, Department of Public Safety, Department of Driver Services, or a secretary of state. The federal REAL ID guide uses the Department of Homeland Security and TSA only for the federal rule, not for a state's filing steps.</p>
<h2>Sources we do not use</h2>
<p>Test prep sites, driving schools, insurance sites, and "we will file your DMV paperwork" businesses are not sources. If a figure is not on the official page, we leave it out.</p>
<h2>Fees, ages, and documents</h2>
<p>A dollar amount is copied only when the official page prints it. Ages and practice hours are included only when the official page states them. Document lists are shortened and linked. They are not a full legal extract of the handbook.</p>
<h2>Dates</h2>
<p>The checked date is the day we opened the official page. We do not refresh that date unless the page was opened again. Rules change, so the agency page wins.</p>
""",
            legal=False,
        )
    )
    pages.append(
        legal_page(
            "image-policy/",
            None,
            "Image policy",
            "Image policy",
            "How Which Driving Test handles logos, graphics, and photos.",
            """
<h2>Graphics</h2>
<p>The logo and the social image are original graphics drawn for this site. They are not a state seal, a DMV badge, or a photo of a person.</p>
<h2>Photos</h2>
<p>This version uses no photographs and no agency logos.</p>
<h2>AI generated images</h2>
<p>This version has no AI generated images. If one is added later, the page will label it in plain text as an AI generated image, and it will not be presented as a photo of a real person or a real office.</p>
""",
            legal=False,
        )
    )
    pages.append(
        legal_page(
            "disclaimer/",
            None,
            "Disclaimer",
            "Disclaimer",
            "Disclaimer for Which Driving Test. Not a government site and not legal advice.",
            """
<h2>Not a government site</h2>
<p>Which Driving Test is an independent guide. It is not a state DMV, BMV, MVD, RMV, Department of Motor Vehicles, or any other licensing agency, and it is not affiliated with, endorsed by, or speaking for any of them. Agency names are used only to identify the offices whose public pages we cite.</p>
<h2>Not legal advice</h2>
<p>The pages are general information about published requirements. They are not legal advice, not a determination that you qualify, and not a promise that a test will be waived. Your state agency page controls. Ages, documents, tests, and fees change.</p>
<h2>Fees</h2>
<p>We show a fee only when the official page prints the amount. A missing fee is not a statement that the service is free.</p>
<h2>Corrections</h2>
<p>If a figure is wrong, <a href="/contact/">email us</a> with the official page that shows the current rule.</p>
<h2>Limitation of liability</h2>
<p>To the extent permitted by law, Joshua Israel Ventures LLC is not liable for loss from reliance on this site. See the <a href="/terms/">terms of use</a>.</p>
""",
        )
    )
    pages.append(
        legal_page(
            "terms/",
            None,
            "Terms of use",
            "Terms of Use",
            "Terms of use for Which Driving Test (whichdrivingtest.com).",
            """
<p>These terms govern your use of whichdrivingtest.com ("Which Driving Test", "we", "us"). Which Driving Test is a trade name of Joshua Israel Ventures LLC, a Florida limited liability company. By using the site you agree to these terms.</p>
<h2>Information only</h2>
<p>The site gives general information about published driver licensing rules. It is not a government service, not legal advice, and not a filing service. Always confirm a rule or a fee on the official state page before you apply, pay, or drive.</p>
<h2>Accuracy</h2>
<p>We cite official pages and leave out figures we cannot confirm, but we do not warrant that any page is complete, current, or error free.</p>
<h2>Acceptable use</h2>
<p>You may read the site and share links for personal, non commercial use. You may not scrape it in bulk, republish our original text or compilations without permission, misuse the contact email, or try to disrupt the site.</p>
<h2>Intellectual property</h2>
<p>Original text, design, and compilations belong to Joshua Israel Ventures LLC. State agency names belong to their owners and are used only to identify public offices.</p>
<h2>Third party links</h2>
<p>We link to official agency websites and to federal REAL ID pages. We are not responsible for their content. The site is hosted on GitHub Pages.</p>
<h2>Disclaimer of warranties and limitation of liability</h2>
<p>The site is provided "as is" and "as available". To the fullest extent permitted by law, Joshua Israel Ventures LLC disclaims all warranties, express or implied, and is not liable for indirect, incidental, special, consequential, or punitive damages, or any loss from use of the site. Our total liability for any claim relating to the site is limited to 100 US dollars.</p>
<h2>Indemnity</h2>
<p>You agree to indemnify Joshua Israel Ventures LLC against claims arising from your misuse of the site or your breach of these terms.</p>
<h2>Governing law</h2>
<p>These terms are governed by the laws of the State of Florida, without regard to conflict of law rules. Disputes will be resolved in the state or federal courts located in Florida, and you consent to their jurisdiction.</p>
<h2>Changes</h2>
<p>We may update these terms. The date above is the latest version. Questions: use the <a href="/contact/">contact page</a>.</p>
""",
        )
    )
    pages.append(
        legal_page(
            "privacy/",
            None,
            "Privacy",
            "Privacy Policy",
            "Privacy policy for Which Driving Test (whichdrivingtest.com).",
            """
<p>This policy explains how Which Driving Test (whichdrivingtest.com), a trade name of Joshua Israel Ventures LLC, a Florida limited liability company, handles information.</p>
<h2>Analytics</h2>
<p>This build does not load an analytics beacon. When the public domain is live, the site is set up to use Cloudflare Web Analytics. That tool does not use cookies or local storage and does not track you across sites. It records aggregate details such as the page, referrer, browser, and country.</p>
<h2>Email</h2>
<p>If you email the address on the <a href="/contact/">contact page</a>, we use your message and your address to reply. We do not sell that information. We keep it only as long as needed to handle the message.</p>
<h2>Advertising</h2>
<p>The site shows no ads today. If we add ads later, for example through Google AdSense, third party vendors including Google may use cookies to serve ads based on prior visits. You would be able to opt out of personalized advertising at <a href="https://www.google.com/settings/ads" rel="nofollow noopener" target="_blank">Google Ads Settings</a> and <a href="https://www.aboutads.info/choices/" rel="nofollow noopener" target="_blank">aboutads.info/choices</a>. Where the law requires it, we will ask for consent before advertising cookies are set. We will update this policy before any ads go live.</p>
<h2>Cookies</h2>
<p>Which Driving Test itself sets no cookies. The site works if your browser blocks cookies.</p>
<h2>Hosting</h2>
<p>The site is hosted on GitHub Pages, which may log IP addresses for security and operations.</p>
<h2>Your rights</h2>
<p>You can ask us to access, correct, or delete personal information we hold about you by emailing the contact address. Residents of some states and countries may have additional rights, which we will honor.</p>
<h2>Children</h2>
<p>The site is a general audience reference. It is not directed at children under 13, and we do not knowingly collect personal information from them.</p>
<h2>Changes</h2>
<p>We will post changes on this page with a new date.</p>
""",
        )
    )
    pages.append(
        legal_page(
            "ad-disclosure/",
            None,
            "Advertising disclosure",
            "Advertising and affiliate disclosure",
            "Advertising disclosure for Which Driving Test. No ads and no DMV filing affiliates today.",
            """
<p>Which Driving Test is free to read. Today the site shows no ads and has no affiliate links. We do not take payment from insurance sellers or from businesses that charge to file a license application.</p>
<p>If ads are added later, they will be labeled and kept separate from the guides. An advertiser will not be presented as the state agency, and advertisers will not edit the rules we cite. If affiliate links are added, we will say so, and a commission would not raise the price you pay the agency.</p>
<h2>Editorial independence</h2>
<p>No state agency and no driving school pays for a mention or for a change to a figure. Questions: use the <a href="/contact/">contact page</a>.</p>
""",
        )
    )
    pages.append(
        legal_page(
            "copyright/",
            None,
            "Copyright and DMCA",
            "Copyright and DMCA policy",
            "Copyright and DMCA policy for Which Driving Test (whichdrivingtest.com).",
            """
<p>Original text, design, and compilations on Which Driving Test are owned by Joshua Israel Ventures LLC. Facts are cited to official pages. The site does not use agency logos or handbook scans. See the <a href="/image-policy/">image policy</a>.</p>
<h2>Reporting infringement</h2>
<p>If you believe material on this site infringes your copyright, email the address on the <a href="/contact/">contact page</a> with: your name and contact details; a description of the copyrighted work; the URL of the material; a statement that you have a good faith belief the use is not authorized; a statement, under penalty of perjury, that the information is accurate and that you are the owner or authorized to act for the owner; and your physical or electronic signature. We review notices and remove or disable material when that is the right step.</p>
<h2>Counter notice</h2>
<p>If material you provided was removed and you believe that was a mistake, you may send a counter notice, through the same email, with the details required by 17 U.S.C. 512(g).</p>
<h2>Repeat infringement</h2>
<p>We will act against repeat infringement where that is appropriate.</p>
""",
        )
    )
    contact_h1 = "Contact"
    contact_path = "contact/"
    contact_crumbs = [("Home", "/"), ("Contact", "/contact/")]
    contact_inner = """
<p>Questions and corrections go to <a href="mailto:joshuaofisrael@gmail.com">joshuaofisrael@gmail.com</a>.</p>
<h2>Corrections</h2>
<p>Include the page address, the line that looks wrong, and a link to the state agency page that shows the current rule. We update the checked date when we open that page again.</p>
<p>We read the message to reply. See the <a href="/privacy/">privacy policy</a>.</p>
"""
    contact_body = frame(contact_h1, contact_crumbs, contact_inner, [], [], [("/disclaimer/", "Disclaimer"), ("/methodology/", "Sources and methods")])
    pages.append(
        pack(
            contact_path,
            "Contact Which Driving Test",
            "Contact Which Driving Test with a correction or a question about a state guide.",
            None,
            contact_body,
            [
                breadcrumb_schema(contact_crumbs),
                {
                    "@context": "https://schema.org",
                    "@type": "ContactPage",
                    "name": "Contact Which Driving Test",
                    "url": DOMAIN + "/contact/",
                },
            ],
        )
    )
    return pages


def not_found_page():
    h1 = "Page not found"
    body = f"""
<article class="prose"><h1>{esc(h1)}</h1>
{BANNER}
<p>That page is not on {esc(SITE)}. Choose a state from the menu, or open the <a href="/states/">full state list</a>.</p>
<ul class="cols">
<li><a href="/guides/how-to-use/">How to use these guides</a></li>
<li><a href="/guides/real-id/">REAL ID</a></li>
<li><a href="/guides/learner-permit-ages/">Permit ages</a></li>
<li><a href="/">Home</a></li>
</ul>
</article>
"""
    return pack(
        "404.html",
        "Page not found",
        "That page is not on Which Driving Test. Choose a state guide from the list.",
        None,
        body,
        [],
    )


def all_pages(states):
    published_states = []
    seen = set()
    report = {"published": [], "skipped": [], "topics": {key: [] for key, _label in TOPIC_META}, "missing_states": []}
    for st in states:
        slug = st.get("slug")
        if slug in seen:
            report["skipped"].append({"slug": slug, "reason": "duplicate"})
            continue
        seen.add(slug)
        if not publishable(st):
            report["skipped"].append({"slug": slug, "reason": "not enough confirmed official facts"})
            continue
        topics = ready_topics(st)
        st["_topics"] = topics
        published_states.append(st)
        report["published"].append(slug)
        for key, ok in topics.items():
            if ok:
                report["topics"][key].append(slug)
    published = {st["slug"]: st["name"] for st in published_states}
    for slug, name, _region in STATES:
        if slug not in published:
            report["missing_states"].append(name)
    pages = [home_page(published_states), states_index(published_states), guides_index(), guide_how(), guide_realid(), guide_ages(published_states), guide_teen(published_states)]
    pages.extend(static_pages())
    pages.append(not_found_page())
    for st in published_states:
        topics = st["_topics"]
        pages.append(state_page(st, topics, published))
        for key, builder in TOPIC_BUILDERS.items():
            if topics.get(key):
                pages.append(builder(st, topics, published))
    return pages, report, published
