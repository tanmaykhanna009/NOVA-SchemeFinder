from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent.parent / "schemes.db"


def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError("schemes.db is missing. Run: python core/setup_database.py")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def total_schemes():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]


def _like(value):
    return f"%{str(value or '').strip().lower()}%"


def search_schemes(age=None, income=None, gender="Any", occupation="Any",
                   state="All India", keyword=None, limit=50):
    """
    Flexible ranked search.

    The old version used every profile field as a hard SQL filter. That meant
    a single imperfect/missing dataset field could make a useful scheme vanish.
    This version keeps only genuinely hard eligibility checks, then ranks
    matches by keyword, occupation, state, age and income.
    """
    limit = min(max(int(limit), 1), 100)
    keyword = (keyword or "").strip().lower()
    occupation = (occupation or "Any").strip()
    state = (state or "All India").strip()

    # Start with a broad candidate pool. Keyword is a ranking signal rather
    # than a mandatory filter, so "What do you want/need?" actually works.
    sql = "SELECT * FROM schemes WHERE 1=1"
    params = []

    # Keep age/income as eligibility constraints only when the database has
    # an explicit value. Unknown values are not treated as disqualifiers.
    if age is not None:
        sql += " AND (age_min IS NULL OR age_min <= ?) AND (age_max IS NULL OR age_max >= ?)"
        params += [age, age]

    if income is not None:
        sql += " AND (income_max IS NULL OR income_max >= ?)"
        params.append(income)

    if gender != "Any":
        sql += " AND (LOWER(gender)=? OR LOWER(gender)='all' OR gender IS NULL OR gender='')"
        params.append(gender.lower())

    # Do NOT hard-filter occupation/state: source records often have
    # "Any", Central, combined state strings, or incomplete beneficiary tags.
    with get_connection() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

    if not rows:
        return []

    wanted_terms = set()
    if keyword:
        wanted_terms.update(t for t in keyword.split() if len(t) > 2)

    occupation_terms = {
        "student": {"student", "education", "scholarship", "school", "college", "study", "fee"},
        "farmer": {"farmer", "agriculture", "kisan", "crop", "farming", "irrigation"},
        "worker": {"worker", "labour", "labor", "employment", "construction", "eshram"},
        "entrepreneur": {"business", "startup", "loan", "enterprise", "msme", "mudra"},
        "artisan": {"artisan", "craft", "vishwakarma", "toolkit", "handicraft"},
        "street vendor": {"vendor", "street", "svanidhi"},
        "unemployed": {"job", "employment", "career", "skill", "training"},
        "women": {"women", "woman", "female", "girl", "widow", "mother"},
        "senior citizen": {"senior", "elder", "pension", "old age"},
    }
    occ_terms = occupation_terms.get(occupation.lower(), set())

    def score(row):
        hay = " ".join(str(row.get(k) or "") for k in (
            "name", "category", "occupation", "summary", "keywords",
            "eligibility", "benefits", "ministry", "state"
        )).lower()
        points = 0

        if wanted_terms:
            for term in wanted_terms:
                if term in hay:
                    points += 14
                    if term in str(row.get("name") or "").lower():
                        points += 10

        if occ_terms:
            points += sum(5 for term in occ_terms if term in hay)

        if state.lower() != "all india":
            st = str(row.get("state") or "").lower()
            if state.lower() in st:
                points += 18
            elif "central" in st or "all india" in st or "all" in st:
                points += 8

        # Prefer records with useful content and a valid application route.
        if row.get("application_url"):
            points += 2
        if row.get("benefits"):
            points += 1
        if row.get("eligibility"):
            points += 1

        return points

    ranked = sorted(rows, key=score, reverse=True)
    return ranked[:limit]


def fetch_all_schemes(limit=5000):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM schemes LIMIT ?", (limit,)
        ).fetchall()]
