# ================================================================
# DYNAMIC URL EXTRACTION & CSV ENRICHMENT SYSTEM
# ================================================================

import re
import html
import difflib
from pathlib import Path
from urllib.parse import unquote, urlparse
import pandas as pd

# ================================================================
# PATH CONFIGURATION
# ================================================================

BASE_DIR = Path(__file__).resolve().parent
RAW_FOLDER = BASE_DIR / "data" / "raw"
OUTPUT_FOLDER = BASE_DIR / "data" / "processed"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# ================================================================
# STATIC FALLBACK DICTIONARIES
# ================================================================

STATE_MAP = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "delhi": "Delhi",
    "nct of delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "chandigarh": "Chandigarh",
}

REGION_MAP = {
    "Delhi": "North",
    "Haryana": "North",
    "Punjab": "North",
    "Rajasthan": "North",
    "Uttar Pradesh": "North",

    "Andhra Pradesh": "South",
    "Karnataka": "South",
    "Kerala": "South",
    "Tamil Nadu": "South",
    "Telangana": "South",

    "Gujarat": "West",
    "Maharashtra": "West",
    "Goa": "West",

    "Bihar": "East",
    "West Bengal": "East",
    "Odisha": "East",

    "Madhya Pradesh": "Central",
    "Chhattisgarh": "Central",
}

CITY_MAP = {
    "new delhi": ("New Delhi", "Delhi"),
    "delhi": ("Delhi", "Delhi"),
    "mumbai": ("Mumbai", "Maharashtra"),
    "pune": ("Pune", "Maharashtra"),
    "bengaluru": ("Bengaluru", "Karnataka"),
    "bangalore": ("Bengaluru", "Karnataka"),
    "hyderabad": ("Hyderabad", "Telangana"),
    "chennai": ("Chennai", "Tamil Nadu"),
    "kolkata": ("Kolkata", "West Bengal"),
    "ahmedabad": ("Ahmedabad", "Gujarat"),
    "gurgaon": ("Gurugram", "Haryana"),
    "gurugram": ("Gurugram", "Haryana"),
    "noida": ("Noida", "Uttar Pradesh"),
    "lucknow": ("Lucknow", "Uttar Pradesh"),
    "jaipur": ("Jaipur", "Rajasthan"),
    "chandigarh": ("Chandigarh", "Chandigarh"),
}

SORTED_CITIES = sorted(
    CITY_MAP.items(),
    key=lambda x: len(x[0]),
    reverse=True
)

URL_STOP_WORDS = {
    "www", "com", "in", "org", "net", "co",
    "india", "the", "and", "or", "of", "for",
    "with", "from", "near", "reviews", "review",
    "listing", "listings", "directory", "search",
    "page", "pages", "html", "htm", "php", "aspx"
}

# ================================================================
# NORMALIZATION & PARSING
# ================================================================

def normalize_url(value):

    if not value or pd.isna(value):
        return ""

    url = str(value).strip()

    url = html.unescape(url)

    match = re.search(
        r'https?://[^\s\)\]\>]+',
        url,
        flags=re.IGNORECASE
    )

    if match:
        url = match.group(0)

    return unquote(url).strip(' <>"\'. ,;')


def normalize_text(text):

    if not text or pd.isna(text):
        return ""

    text = unquote(str(text))

    text = html.unescape(text).lower()

    text = re.sub(
        r"[-_/]+",
        " ",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def get_url_path_segments(url):

    """Dynamically split URL into manageable path segments."""

    if not url:
        return []

    try:

        path = unquote(
            urlparse(url).path
        )

        path = re.sub(
            r"\.(html?|php|aspx?)$",
            "",
            path,
            flags=re.IGNORECASE
        )

        return [
            normalize_text(p)
            for p in path.split('/')
            if p
        ]

    except:

        return []


# ================================================================
# DYNAMIC EXTRACTION LOGIC
# ================================================================

def extract_dynamic_location(url):

    """Dynamically extracts location based on URL structure."""

    segments = get_url_path_segments(url)

    location_markers = [
        'city',
        'location',
        'in',
        'l',
        'place'
    ]

    for i, segment in enumerate(segments):

        if (
            segment in location_markers
            and i + 1 < len(segments)
        ):

            potential_city = segments[i + 1]

            if len(potential_city) > 2:
                return potential_city.title()

    if segments:

        first_seg = segments[0]

        for city_key, _ in SORTED_CITIES:

            if first_seg == city_key:
                return first_seg.title()

    return ""


def extract_city(url, state):

    dyn_city = extract_dynamic_location(url)

    if dyn_city:

        if dyn_city.lower() in CITY_MAP:

            return CITY_MAP[
                dyn_city.lower()
            ][0]

        return dyn_city

    text = normalize_text(
        unquote(
            urlparse(url).path
        )
    )

    for city_key, city_info in SORTED_CITIES:

        city_name, city_state = city_info

        if state and city_state != state:
            continue

        if re.search(
            r"\b" +
            re.escape(city_key) +
            r"\b",
            text,
            re.IGNORECASE
        ):

            return city_name

    return ""


def extract_state(url):

    text = normalize_text(
        unquote(
            urlparse(url).path
        )
    )

    for state_key, state_name in sorted(
        STATE_MAP.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):

        if re.search(
            r"\b" +
            re.escape(state_key) +
            r"\b",
            text,
            re.IGNORECASE
        ):

            return state_name

    return ""


def extract_category_dynamic(
    url,
    keyword=""
):

    """Dynamically extracts category from URL structure or keyword."""

    segments = get_url_path_segments(url)

    cat_markers = [
        'category',
        'c',
        'services',
        'products',
        'event'
    ]

    for i, segment in enumerate(segments):

        if (
            segment in cat_markers
            and i + 1 < len(segments)
        ):

            return segments[i + 1].title()

    text = normalize_text(
        unquote(
            urlparse(url).path
        )
    )

    broad_categories = {

        "Restaurant": [
            "restaurant",
            "food",
            "cafe",
            "dining",
            "eatery"
        ],

        "Hotel": [
            "hotel",
            "resort",
            "stay",
            "accommodation"
        ],

        "Education": [
            "tutor",
            "classes",
            "training",
            "course",
            "institute"
        ],

        "B2B/Manufacturing": [
            "manufacturer",
            "supplier",
            "exporter",
            "wholesaler"
        ],

        "Events": [
            "event",
            "workshop",
            "tickets",
            "booking"
        ]
    }

    search_space = (
        text +
        " " +
        normalize_text(keyword)
    )

    for cat, patterns in broad_categories.items():

        for pat in patterns:

            if re.search(
                r"\b" +
                re.escape(pat) +
                r"\b",
                search_space,
                re.IGNORECASE
            ):

                return cat

    return ""


def extract_url_keywords_dynamic(
    url,
    keyword,
    metadata_set
):

    """Fuzzy matching for URL keywords extraction."""

    url_tokens = set([
        t
        for t in re.findall(
            r"[a-z0-9]+",
            normalize_text(
                unquote(
                    urlparse(url).path
                )
            )
        )
        if len(t) > 1
        and t not in URL_STOP_WORDS
    ])

    keyword_tokens = [
        t
        for t in re.findall(
            r"[a-z0-9]+",
            normalize_text(keyword)
        )
        if len(t) > 1
    ]

    matched = []
    remaining = []

    for token in url_tokens:

        if token in metadata_set:
            continue

        matches = difflib.get_close_matches(
            token,
            keyword_tokens,
            n=1,
            cutoff=0.8
        )

        if matches:

            matched.append(token)

        else:

            remaining.append(token)

    return (
        " ".join(matched),
        " ".join(remaining)
    )


def extract_source(url):

    clean_url = normalize_url(url)

    if not clean_url:
        return ""

    try:

        domain = (
            urlparse(clean_url)
            .netloc
            .lower()
            .strip()
        )

        return (
            domain[4:]
            if domain.startswith("www.")
            else domain
        )

    except:

        return ""


# ================================================================
# MAIN PROCESSOR
# ================================================================

def extract_location_data(
    url,
    keyword=""
):

    clean_url = normalize_url(url)

    if not clean_url:

        return {
            col: ""
            for col in [
                "City",
                "State",
                "Country",
                "Region",
                "URL_Location",
                "Area",
                "Category",
                "Business Category",
                "Product Category",
                "Source",
                "URL_Keyword",
                "Unknown",
                "Remaining_Url_Keywords"
            ]
        } | {
            "Priority Rank": 1
        }

    state = extract_state(
        clean_url
    )

    city = extract_city(
        clean_url,
        state
    )

    country = (
        "India"
        if state
        or city
        or re.search(
            r"\bindia\b",
            normalize_text(clean_url),
            re.IGNORECASE
        )
        else ""
    )

    region = REGION_MAP.get(
        state,
        ""
    )

    category = extract_category_dynamic(
        clean_url,
        keyword
    )

    source = extract_source(
        clean_url
    )

    metadata_tokens = set(
        re.findall(
            r"[a-z0-9]+",
            normalize_text(
                f"{city} {state} {country} {category}"
            )
        )
    )

    url_kw, rem_kw = extract_url_keywords_dynamic(
        clean_url,
        keyword,
        metadata_tokens
    )

    return {
        "City": city,
        "State": state,
        "Country": country,
        "Region": region,
        "URL_Location": city,
        "Area": "",
        "Category": category,
        "Business Category": category,
        "Product Category": category,
        "Source": source,
        "URL_Keyword": url_kw,
        "Unknown": "",
        "Remaining_Url_Keywords": rem_kw,

        # Temporary value.
        # Final Priority Rank is calculated from Volume below.
        "Priority Rank": 1,
    }


def process_file(file_path):

    print(
        f"\n{'='*80}\n"
        f"PROCESSING: {file_path.name}\n"
        f"{'='*80}"
    )
    try:
        df = pd.read_csv(
            file_path,
            encoding='utf-8-sig',
            low_memory=False
        )

        # Remove duplicate columns such as Keyword.1,
        # Estimated Visits.1, CPC.1, etc.
        duplicate_columns = [
            col
            for col in df.columns
            if re.search(r'\.\d+$', str(col))
        ]

        if duplicate_columns:
            print(f"Removing duplicate columns: {duplicate_columns}")
            df.drop(columns=duplicate_columns, inplace=True)

    except Exception as e:
        print(
            f"ERROR reading CSV: {e}"
        )

    except Exception as e:

        print(
            f"ERROR reading CSV: {e}"
        )

        return False

    url_col = next(
        (
            col
            for col in df.columns
            if 'url' in col.lower()
            or 'ranking' in col.lower()
        ),
        None
    )

    if not url_col:

        print(
            "ERROR: URL column not found."
        )

        return False

    if "Keyword" not in df.columns:

        df["Keyword"] = ""

    print(
        "Extracting dynamic URL information..."
    )

    results = [
        extract_location_data(
            row.get(
                url_col,
                ""
            ),
            row.get(
                "Keyword",
                ""
            )
        )
        for _, row in df.iterrows()
    ]

    res_df = pd.DataFrame(
        results
    )

    for col in res_df.columns:

        df[col] = res_df[col]

    # ============================================================
    # PRIORITY RANKING BASED ON VOLUME
    # Higher Volume = Higher Priority
    # Same Volume = Same Priority
    # No priority number will be skipped
    #
    # Example:
    # 50000 -> 1
    # 40000 -> 2
    # 30100 -> 3
    # 30100 -> 3
    # 25000 -> 4
    # 20000 -> 5
    # ============================================================

    df["Volume"] = pd.to_numeric(
        df["Volume"],
        errors="coerce"
    ).fillna(0)

    df["Priority Rank"] = pd.qcut(
    df["Volume"].rank(method="first"),
    q=5,
    labels=[5, 4, 3, 2, 1]
).astype(int)
    

    # ============================================================
    # REQUIRED COLUMNS
    # ============================================================

    required_cols = [
        "No",
        "Keyword",
        "Volume",
        "Position",
        "Estimated Visits",
        "CPC",
        "Paid Difficulty",
        "SEO Difficulty",
        "Ranking URL",
        "City",
        "State",
        "Country",
        "Region",
        "URL_Location",
        "Area",
        "Category",
        "Business Category",
        "Product Category",
        "Source",
        "URL_Keyword",
        "Unknown",
        "Remaining_Url_Keywords",
        "Priority"
    ]

    for col in required_cols:

        if col not in df.columns:

            df[col] = (
                1
                if col == "Priority Rank"
                else ""
            )

    df = df[
        [
            c
            for c in required_cols
            if c in df.columns
        ]
        +
        [
            c
            for c in df.columns
            if c not in required_cols
        ]
    ]

    output_path = (
        OUTPUT_FOLDER /
        f"{file_path.stem}_enriched_new.csv"
    )

    try:

        df.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"\nOutput saved to: {output_path}"
        )

        return True

    except Exception as e:

        print(
            f"Error saving: {e}"
        )

        return False


# ================================================================
# MAIN
# ================================================================

def main():

    csv_files = (
        [
            f
            for f in RAW_FOLDER.iterdir()
            if f.is_file()
            and f.suffix.lower() == ".csv"
        ]
        if RAW_FOLDER.exists()
        else []
    )

    print(
        f"\nCSV files found: {len(csv_files)}"
    )

    successful = sum(
        1
        for file in csv_files
        if process_file(file)
    )

    print(
        f"\n{'='*80}\n"
        f"FINAL REPORT: "
        f"{successful}/{len(csv_files)} Successful\n"
        f"{'='*80}"
    )


if __name__ == "__main__":
    main()