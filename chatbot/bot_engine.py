import re
from difflib import SequenceMatcher
from core.database import fetch_all_schemes

ALIASES = {
    "student": ["scholarship", "education", "college", "school", "fee", "study", "student"],
    "farmer": ["agriculture", "kisan", "crop", "farming", "irrigation", "farmer"],
    "worker": ["labour", "labor", "eshram", "construction", "worker", "employment"],
    "entrepreneur": ["business", "startup", "loan", "enterprise", "msme", "mudra", "entrepreneur"],
    "artisan": ["craft", "vishwakarma", "toolkit", "handicraft", "artisan"],
    "street vendor": ["vendor", "street vendor", "svanidhi"],
    "health": ["medical", "hospital", "insurance", "ayushman", "health", "treatment"],
    "housing": ["house", "home", "awas", "housing", "rent"],
    "unemployed": ["job", "employment", "career", "work", "skill", "training", "unemployed"],
    "women": ["woman", "women", "female", "girl", "widow", "mother"],
    "senior citizen": ["senior", "elder", "pension", "old age"],
}

GREETINGS = {"hi", "hello", "hey", "hii", "hiii", "namaste", "namaskar"}
GOODBYES = {
    "bye", "goodbye", "good bye", "see you", "see ya", "cya",
    "thanks bye", "thank you bye", "ok bye", "okay bye"
}
THANKS = {"thanks", "thank you", "thx", "thankyou", "ty"}


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").lower().strip())


def tokens(value):
    return {x for x in re.findall(r"[a-z0-9]+", norm(value)) if len(x) > 2}


def extract_age(text):
    patterns = [
        r"\b(\d{1,3})\s*(?:years?\s*old|year[- ]old|y/?o)\b",
        r"\bage\s*(?:is|of|:)?\s*(\d{1,3})\b",
        r"\bi[' ]?m\s*(\d{1,3})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, norm(text))
        if m:
            age = int(m.group(1))
            return age if 0 <= age <= 120 else None
    return None


def extract_income(text):
    t = norm(text).replace(",", "").replace("₹", "")
    patterns = [
        r"(?:income|salary|earn)\D{0,20}(\d+(?:\.\d+)?)\s*(lakh|lac|lacs|k|thousand|crore)?",
        r"(\d+(?:\.\d+)?)\s*(lakh|lac|lacs|k|thousand|crore)\s*(?:income|annual)?",
    ]
    for pattern in patterns:
        m = re.search(pattern, t)
        if not m:
            continue
        value = float(m.group(1))
        unit = m.group(2) or ""
        if unit in {"lakh", "lac", "lacs"}:
            value *= 100000
        elif unit in {"k", "thousand"}:
            value *= 1000
        elif unit == "crore":
            value *= 10000000
        return int(value)
    return None


def extract_state(text):
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
        "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
        "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry",
        "Chandigarh", "Bihar", "Assam"
    ]
    t = norm(text)
    return next((x for x in sorted(states, key=len, reverse=True) if x.lower() in t), None)


def extract_role(text):
    t = norm(text)
    for role, aliases in ALIASES.items():
        if role in t or any(alias in t for alias in aliases):
            return role
    return None


def score(scheme, message):
    text = norm(" ".join(str(scheme.get(k, "")) for k in [
        "name", "category", "occupation", "summary", "keywords", "eligibility", "benefits"
    ]))
    q = tokens(message)
    value = len(q & tokens(text)) * 4

    role = extract_role(message)
    if role:
        aliases = [role, *ALIASES[role]]
        if any(x in text for x in aliases):
            value += 15

    state = extract_state(message)
    if state:
        st = norm(scheme.get("state"))
        if state.lower() in st:
            value += 14
        elif "central" in st or "all india" in st or "all" in st:
            value += 7

    def safe_float(value):
        if value is None:
            return None
        text = str(value).strip().lower().replace(",", "")
        if text in {"", "null", "none", "nan", "n/a", "na", "-", "unknown"}:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    age = extract_age(message)
    if age is not None:
        lo = safe_float(scheme.get("age_min"))
        hi = safe_float(scheme.get("age_max"))
        if (lo is None or age >= lo) and (hi is None or age <= hi):
            value += 12

    income = extract_income(message)
    if income is not None:
        max_income = safe_float(scheme.get("income_max"))
        if max_income is None or income <= max_income:
            value += 8

    # Fuzzy signal helps with small spelling mistakes.
    value += SequenceMatcher(None, " ".join(sorted(q)), text[:700]).ratio() * 4
    return value


class SchemeChatbot:
    def respond(self, message):
        message = message.strip()
        t = norm(message)

        if not t:
            return "Tell me what you need — for example: **I'm 19, a student in Uttar Pradesh and need a scholarship.**"

        if t in GOODBYES or any(x in t for x in ["goodbye", "see you", "see ya"]):
            return "Bye! 👋 Good luck with your scheme search. Come back anytime if you need help finding a government scheme."

        if t in GREETINGS or any(t.startswith(x + " ") for x in GREETINGS):
            return "Hey! 🤖 I’m NOVA. Tell me your **age, state, occupation and what you need** — for example, *I'm 20, a student in UP and need a scholarship*."

        if t in THANKS or any(x in t for x in ["thank you", "thanks a lot"]):
            return "You're welcome! 🤖 If you want, tell me what you need and I'll search the loaded scheme database."

        if any(x in t for x in ["what can you do", "how can you help", "help me", "how do i use you"]):
            return (
                "I can search the loaded government-scheme database and rank likely matches. "
                "Try messages like:\n\n"
                "- **I'm 18 and need a scholarship**\n"
                "- **I'm a farmer in UP and need financial help**\n"
                "- **I want a business loan**\n"
                "- **I need a housing scheme**\n\n"
                "You can also just type a scheme name or need."
            )

        schemes = fetch_all_schemes(limit=5000)
        ranked = sorted(((score(s, message), s) for s in schemes), key=lambda x: x[0], reverse=True)

        top = [s for sc, s in ranked[:5] if sc > 2]
        if not top:
            return (
                "I couldn't find a strong match yet. Try a broader request such as "
                "**scholarship, farmer, business loan, health, housing, worker, pension, or skill training**."
            )

        lines = ["### NOVA found these matches ✦"]
        for i, scheme in enumerate(top, 1):
            summary = scheme.get("summary") or "Government support programme."
            eligibility = scheme.get("eligibility") or "Check the current eligibility rules."
            benefits = scheme.get("benefits") or "See the official scheme page for current benefits."
            url = scheme.get("application_url") or scheme.get("official_url") or ""
            lines.append(
                f"**{i}. {scheme['name']}**\n\n"
                f"{summary[:700]}\n\n"
                f"**Why it may fit:** {eligibility[:700]}\n\n"
                f"**Benefit:** {benefits[:450]}\n\n"
                f"**Official route:** {url}"
            )
        lines.append("*Always verify the latest eligibility and application instructions on the official portal.*")
        return "\n\n---\n\n".join(lines)
