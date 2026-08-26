"""Build NOVA's local database from 1500 real scheme records.

Source dataset: SmartDuke Technologies' Indian Government Schemes Dataset 2026,
whose dataset card says the records originate from myscheme.gov.in.
The first 500 usable rows are downloaded from the dataset CSV on Hugging Face.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "schemes.db"
CACHE_PATH = BASE / "schemes_cache.json"

DATASET = "smartduketech/indian-government-schemes-2025"
API = "https://datasets-server.huggingface.co/rows"
TARGET = 1500


def clean(value, default=""):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    text = re.sub(r"<[^>]+>", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def first_url(*values):
    for value in values:
        value = clean(value)
        if value.startswith("http://") or value.startswith("https://"):
            return value
    return ""


def category(raw):
    text = clean(raw)
    if not text:
        return "Government Support"
    # Keep the first two meaningful categories readable in the cards.
    parts = [p.strip() for p in re.split(r"[,;]", text) if p.strip()]
    return " • ".join(parts[:2]) if parts else "Government Support"


def occupation(raw):
    text = clean(raw).lower()
    if "student" in text: return "Student"
    if "farmer" in text or "agric" in text: return "Farmer"
    if "business" in text or "enterprise" in text or "entrepreneur" in text: return "Entrepreneur"
    if "artisan" in text or "craft" in text: return "Artisan"
    if "worker" in text or "labour" in text or "labor" in text: return "Worker"
    if "woman" in text or "female" in text: return "Women"
    if "fisher" in text: return "Fisher"
    if "senior" in text or "elder" in text or "pension" in text: return "Senior Citizen"
    return "Any"


def fetch_rows():
    """Download the source CSV and return the first 1500 usable, unique records."""
    import csv
    import io

    csv_url = "https://huggingface.co/datasets/smartduketech/indian-government-schemes-2025/resolve/main/Schemes.csv?download=true"
    response = requests.get(csv_url, timeout=90, headers={"User-Agent": "NOVA-SchemeFinder/1.0"})
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"

    reader = csv.DictReader(io.StringIO(response.text))
    records = []
    seen = set()

    for row in reader:
        name = clean(row.get("name"))
        if not name:
            continue
        official = first_url(row.get("apply_url"), row.get("official_url"))
        if not official:
            continue

        key = (name.lower(), official)
        if key in seen:
            continue
        seen.add(key)

        state_raw = clean(row.get("state"))
        eligible_states = clean(row.get("eligibility_state"))
        state = state_raw or eligible_states or "Central"

        records.append({
            "name": name,
            "ministry": clean(row.get("ministry")) or clean(row.get("department")),
            "state": state,
            "occupation": occupation(row.get("beneficiary_type")),
            "category": category(row.get("category")),
            "summary": clean(row.get("description"))[:900],
            "eligibility": clean(row.get("eligibility_text"))[:1800],
            "benefits": clean(row.get("benefits"))[:1600],
            "keywords": " ".join([
                clean(row.get("name")), clean(row.get("category")),
                clean(row.get("beneficiary_type")), clean(row.get("state"))
            ]),
            "application_url": official,
            "official_url": first_url(row.get("official_url"), official),
            "age_min": row.get("eligibility_age_min") or None,
            "age_max": row.get("eligibility_age_max") or None,
            "gender": clean(row.get("eligibility_gender")) or "all",
            "income_max": row.get("eligibility_income_max") or None,
            "residence": clean(row.get("eligibility_residence")) or "both",
            "disability": str(row.get("eligibility_disability", "")).lower() == "true",
            "bpl": str(row.get("eligibility_bpl", "")).lower() == "true",
        })
        if len(records) >= TARGET:
            break

    if len(records) < TARGET:
        raise RuntimeError(f"Only found {len(records)} usable scheme records; expected at least {TARGET}.")
    return records[:TARGET]

def create_db(records):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS schemes")
    conn.execute("""
        CREATE TABLE schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ministry TEXT,
            state TEXT,
            occupation TEXT,
            category TEXT,
            summary TEXT,
            eligibility TEXT,
            benefits TEXT,
            keywords TEXT,
            application_url TEXT NOT NULL,
            official_url TEXT,
            age_min REAL,
            age_max REAL,
            gender TEXT,
            income_max REAL,
            residence TEXT,
            disability INTEGER,
            bpl INTEGER
        )
    """)
    conn.executemany("""
        INSERT INTO schemes
        (name,ministry,state,occupation,category,summary,eligibility,benefits,keywords,
         application_url,official_url,age_min,age_max,gender,income_max,residence,disability,bpl)
        VALUES (:name,:ministry,:state,:occupation,:category,:summary,:eligibility,:benefits,:keywords,
                :application_url,:official_url,:age_min,:age_max,:gender,:income_max,:residence,:disability,:bpl)
    """, records)
    conn.commit()
    conn.close()
    CACHE_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def setup():
    try:
        records = fetch_rows()
        create_db(records)
        print(f"NOVA database ready: {len(records)} scheme records.")
        print("Source: SmartDuke Technologies / myScheme-derived 2026 dataset.")
        print("Links are taken from the dataset's apply_url/official_url fields; no fake URLs are generated.")
    except Exception as exc:
        if CACHE_PATH.exists():
            records = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            create_db(records)
            print(f"Network fetch failed ({exc}). Rebuilt database from cached {len(records)} records.")
        else:
            raise RuntimeError(
                "Could not download the 500-scheme dataset. Connect to the internet and run "
                "python core/setup_database.py again."
            ) from exc


if __name__ == "__main__":
    setup()
