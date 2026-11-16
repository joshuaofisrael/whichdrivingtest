"""State list, census regions, and land-border neighbors."""

# (slug, name, region)
STATES = [
    ("connecticut", "Connecticut", "Northeast"),
    ("maine", "Maine", "Northeast"),
    ("massachusetts", "Massachusetts", "Northeast"),
    ("new-hampshire", "New Hampshire", "Northeast"),
    ("new-jersey", "New Jersey", "Northeast"),
    ("new-york", "New York", "Northeast"),
    ("pennsylvania", "Pennsylvania", "Northeast"),
    ("rhode-island", "Rhode Island", "Northeast"),
    ("vermont", "Vermont", "Northeast"),
    ("illinois", "Illinois", "Midwest"),
    ("indiana", "Indiana", "Midwest"),
    ("iowa", "Iowa", "Midwest"),
    ("kansas", "Kansas", "Midwest"),
    ("michigan", "Michigan", "Midwest"),
    ("minnesota", "Minnesota", "Midwest"),
    ("missouri", "Missouri", "Midwest"),
    ("nebraska", "Nebraska", "Midwest"),
    ("north-dakota", "North Dakota", "Midwest"),
    ("ohio", "Ohio", "Midwest"),
    ("south-dakota", "South Dakota", "Midwest"),
    ("wisconsin", "Wisconsin", "Midwest"),
    ("alabama", "Alabama", "South"),
    ("arkansas", "Arkansas", "South"),
    ("delaware", "Delaware", "South"),
    ("district-of-columbia", "District of Columbia", "South"),
    ("florida", "Florida", "South"),
    ("georgia", "Georgia", "South"),
    ("kentucky", "Kentucky", "South"),
    ("louisiana", "Louisiana", "South"),
    ("maryland", "Maryland", "South"),
    ("mississippi", "Mississippi", "South"),
    ("north-carolina", "North Carolina", "South"),
    ("oklahoma", "Oklahoma", "South"),
    ("south-carolina", "South Carolina", "South"),
    ("tennessee", "Tennessee", "South"),
    ("texas", "Texas", "South"),
    ("virginia", "Virginia", "South"),
    ("west-virginia", "West Virginia", "South"),
    ("alaska", "Alaska", "West"),
    ("arizona", "Arizona", "West"),
    ("california", "California", "West"),
    ("colorado", "Colorado", "West"),
    ("hawaii", "Hawaii", "West"),
    ("idaho", "Idaho", "West"),
    ("montana", "Montana", "West"),
    ("nevada", "Nevada", "West"),
    ("new-mexico", "New Mexico", "West"),
    ("oregon", "Oregon", "West"),
    ("utah", "Utah", "West"),
    ("washington", "Washington", "West"),
    ("wyoming", "Wyoming", "West"),
]

REGIONS = ["Northeast", "Midwest", "South", "West"]

# Land borders. Alaska and Hawaii have no land border; related slugs are separate.
BORDERS = {
    "alabama": ["florida", "georgia", "mississippi", "tennessee"],
    "alaska": [],
    "arizona": ["california", "colorado", "nevada", "new-mexico", "utah"],
    "arkansas": ["louisiana", "mississippi", "missouri", "oklahoma", "tennessee", "texas"],
    "california": ["arizona", "nevada", "oregon"],
    "colorado": ["arizona", "kansas", "nebraska", "new-mexico", "oklahoma", "utah", "wyoming"],
    "connecticut": ["massachusetts", "new-york", "rhode-island"],
    "delaware": ["maryland", "new-jersey", "pennsylvania"],
    "district-of-columbia": ["maryland", "virginia"],
    "florida": ["alabama", "georgia"],
    "georgia": ["alabama", "florida", "north-carolina", "south-carolina", "tennessee"],
    "hawaii": [],
    "idaho": ["montana", "nevada", "oregon", "utah", "washington", "wyoming"],
    "illinois": ["indiana", "iowa", "kentucky", "missouri", "wisconsin"],
    "indiana": ["illinois", "kentucky", "michigan", "ohio"],
    "iowa": ["illinois", "minnesota", "missouri", "nebraska", "south-dakota", "wisconsin"],
    "kansas": ["colorado", "missouri", "nebraska", "oklahoma"],
    "kentucky": ["illinois", "indiana", "missouri", "ohio", "tennessee", "virginia", "west-virginia"],
    "louisiana": ["arkansas", "mississippi", "texas"],
    "maine": ["new-hampshire"],
    "maryland": ["delaware", "pennsylvania", "virginia", "west-virginia", "district-of-columbia"],
    "massachusetts": ["connecticut", "new-hampshire", "new-york", "rhode-island", "vermont"],
    "michigan": ["indiana", "ohio", "wisconsin"],
    "minnesota": ["iowa", "north-dakota", "south-dakota", "wisconsin"],
    "mississippi": ["alabama", "arkansas", "louisiana", "tennessee"],
    "missouri": ["arkansas", "illinois", "iowa", "kansas", "kentucky", "nebraska", "oklahoma", "tennessee"],
    "montana": ["idaho", "north-dakota", "south-dakota", "wyoming"],
    "nebraska": ["colorado", "iowa", "kansas", "missouri", "south-dakota", "wyoming"],
    "nevada": ["arizona", "california", "idaho", "oregon", "utah"],
    "new-hampshire": ["maine", "massachusetts", "vermont"],
    "new-jersey": ["delaware", "new-york", "pennsylvania"],
    "new-mexico": ["arizona", "colorado", "oklahoma", "texas", "utah"],
    "new-york": ["connecticut", "massachusetts", "new-jersey", "pennsylvania", "vermont"],
    "north-carolina": ["georgia", "south-carolina", "tennessee", "virginia"],
    "north-dakota": ["minnesota", "montana", "south-dakota"],
    "ohio": ["indiana", "kentucky", "michigan", "pennsylvania", "west-virginia"],
    "oklahoma": ["arkansas", "colorado", "kansas", "missouri", "new-mexico", "texas"],
    "oregon": ["california", "idaho", "nevada", "washington"],
    "pennsylvania": ["delaware", "maryland", "new-jersey", "new-york", "ohio", "west-virginia"],
    "rhode-island": ["connecticut", "massachusetts"],
    "south-carolina": ["georgia", "north-carolina"],
    "south-dakota": ["iowa", "minnesota", "montana", "nebraska", "north-dakota", "wyoming"],
    "tennessee": ["alabama", "arkansas", "georgia", "kentucky", "mississippi", "missouri", "north-carolina", "virginia"],
    "texas": ["arkansas", "louisiana", "new-mexico", "oklahoma"],
    "utah": ["arizona", "colorado", "idaho", "nevada", "new-mexico", "wyoming"],
    "vermont": ["massachusetts", "new-hampshire", "new-york"],
    "virginia": ["kentucky", "maryland", "north-carolina", "tennessee", "west-virginia", "district-of-columbia"],
    "washington": ["idaho", "oregon"],
    "west-virginia": ["kentucky", "maryland", "ohio", "pennsylvania", "virginia"],
    "wisconsin": ["illinois", "iowa", "michigan", "minnesota"],
    "wyoming": ["colorado", "idaho", "montana", "nebraska", "south-dakota", "utah"],
}

RELATED = {
    "alaska": ["washington", "hawaii"],
    "hawaii": ["alaska", "california"],
}

EDL_SLUGS = {"michigan", "minnesota", "new-york", "vermont", "washington"}

BY_SLUG = {s[0]: s for s in STATES}


def name_of(slug):
    return BY_SLUG[slug][1]


def in_place(name):
    if name == "District of Columbia":
        return "the District of Columbia"
    return name


def region_groups():
    groups = {r: [] for r in REGIONS}
    for slug, name, region in STATES:
        groups[region].append((slug, name))
    for r in groups:
        groups[r].sort(key=lambda x: x[1])
    return groups
