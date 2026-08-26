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


def search_schemes(age=None, income=None, gender="Any", occupation="Any", state="All India", keyword=None, limit=50):
    sql = "SELECT * FROM schemes WHERE 1=1"
    params = []
    if age is not None:
        sql += " AND (age_min IS NULL OR age_min <= ?) AND (age_max IS NULL OR age_max >= ?)"
        params += [age, age]
    if income is not None:
        sql += " AND (income_max IS NULL OR income_max >= ?)"
        params.append(income)
    if gender != "Any":
        sql += " AND (LOWER(gender)=? OR LOWER(gender)='all')"
        params.append(gender.lower())
    if occupation != "Any":
        sql += " AND (LOWER(occupation)=? OR LOWER(occupation)='any')"
        params.append(occupation.lower())
    if state != "All India":
        sql += " AND (LOWER(state)=? OR LOWER(state)='central' OR LOWER(state)='all india' OR LOWER(state) LIKE '%all%')"
        params.append(state.lower())
    if keyword:
        sql += """ AND (
            LOWER(name) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(category) LIKE ?
            OR LOWER(occupation) LIKE ? OR LOWER(keywords) LIKE ? OR LOWER(eligibility) LIKE ?
        )"""
        q = f"%{keyword.lower()}%"
        params += [q, q, q, q, q, q]
    # Rank closer records first: exact occupation/state/keyword matches naturally bubble up.
    sql += " ORDER BY CASE WHEN LOWER(state)=LOWER(?) THEN 0 ELSE 1 END, name LIMIT ?"
    params += [state, min(max(int(limit), 1), 100)]
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def fetch_all_schemes(limit=5000):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM schemes LIMIT ?", (limit,)).fetchall()]
