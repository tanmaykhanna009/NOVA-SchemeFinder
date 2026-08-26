import re
from difflib import SequenceMatcher
from core.database import fetch_all_schemes

ALIASES = {
    "student": ["scholarship", "education", "college", "school", "fee", "study"],
    "farmer": ["agriculture", "kisan", "crop", "farming", "irrigation"],
    "worker": ["labour", "labor", "eshram", "construction", "worker", "employment"],
    "entrepreneur": ["business", "startup", "loan", "enterprise", "msme", "mudra"],
    "artisan": ["craft", "vishwakarma", "toolkit", "handicraft"],
    "health": ["medical", "hospital", "insurance", "ayushman", "health"],
    "housing": ["house", "home", "awas", "housing", "rent"],
    "unemployed": ["job", "employment", "career", "work", "skill"],
    "women": ["woman", "women", "female", "girl", "widow"],
}


def norm(value):
    return str(value or "").lower().strip()


def tokens(value):
    return {x for x in re.findall(r"[a-z0-9]+", norm(value)) if len(x) > 2}


def extract_age(text):
    m = re.search(r"\b(\d{1,3})\s*(?:years?\s*old|year[- ]old|y/?o)?\b", norm(text))
    if not m:
        return None
    age = int(m.group(1))
    return age if 0 <= age <= 120 else None


def extract_state(text):
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
        "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
        "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
        "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry"
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
    text = norm(" ".join(str(scheme.get(k, "")) for k in ["name", "category", "occupation", "summary", "keywords", "eligibility"]))
    q = tokens(message)
    value = len(q & tokens(text)) * 4
    role = extract_role(message)
    if role:
        aliases = [role, *ALIASES[role]]
        if any(x in text for x in aliases):
            value += 15
    state = extract_state(message)
    if state and (state.lower() in norm(scheme.get("state")) or "central" in norm(scheme.get("state")) or "all" in norm(scheme.get("state"))):
        value += 10
    age = extract_age(message)
    if age is not None:
        lo, hi = scheme.get("age_min"), scheme.get("age_max")
        if (lo is None or age >= float(lo)) and (hi is None or age <= float(hi)):
            value += 12
    value += SequenceMatcher(None, " ".join(sorted(q)), text[:500]).ratio() * 3
    return value


class SchemeChatbot:
    def respond(self, message):
        message = message.strip()
        if not message:
            return "Tell me what you need — for example: **I'm 19, a student in Uttar Pradesh and need a scholarship.**"
        if norm(message) in {"hi", "hello", "hey"}:
            return "Hey! 🤖 I’m NOVA. Tell me your age, state, occupation, or what kind of help you need."
        schemes = fetch_all_schemes(limit=5000)
        ranked = sorted(((score(s, message), s) for s in schemes), key=lambda x: x[0], reverse=True)
        top = [s for sc, s in ranked[:5] if sc > 2]
        if not top:
            return "I couldn't find a strong match. Try **student**, **farmer**, **business**, **health**, **housing**, **worker**, or **scholarship**."
        lines = ["### NOVA found these matches ✦"]
        for i, scheme in enumerate(top, 1):
            lines.append(
                f"**{i}. {scheme['name']}**\n\n"
                f"{scheme.get('summary') or 'Government support programme.'}\n\n"
                f"**Why it may fit:** {scheme.get('eligibility') or 'Check the current eligibility rules.'}\n\n"
                f"**Official route:** {scheme['application_url']}"
            )
        lines.append("\n*Always verify the latest eligibility and application instructions on the official portal.*")
        return "\n\n---\n\n".join(lines)
