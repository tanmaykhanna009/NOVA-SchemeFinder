from __future__ import annotations

import streamlit as st

from core.database import search_schemes, total_schemes
from core.setup_database import setup as setup_database
from chatbot.bot_engine import SchemeChatbot

st.set_page_config(page_title="NOVA • Scheme Finder", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource(show_spinner=False)
def ensure_database():
    """Prepare the local SQLite cache once per deployed app instance."""
    try:
        if total_schemes() >= 1500:
            return total_schemes()
    except FileNotFoundError:
        pass
    setup_database()
    return total_schemes()

try:
    with st.spinner("NOVA is loading its 1500-scheme universe for this deployment…"):
        ensure_database()
except Exception as exc:
    st.error("NOVA could not load the 500-scheme database.")
    st.code(str(exc))
    st.info("The deployed app needs internet access on its first launch so it can cache the scheme dataset locally.")
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
*{font-family:'Space Grotesk',sans-serif}
.stApp{background:#050816;color:#f8fafc;overflow-x:hidden}
.stApp:before{content:"";position:fixed;inset:-20%;background:radial-gradient(circle at 18% 18%,#4f46e544,transparent 25%),radial-gradient(circle at 82% 8%,#06b6d433,transparent 24%),radial-gradient(circle at 52% 92%,#ec489933,transparent 28%);filter:blur(25px);z-index:-2}
.block-container{max-width:1500px;padding:1.2rem 2.2rem 4rem}
.nova{position:relative;padding:42px;border-radius:34px;overflow:hidden;background:linear-gradient(135deg,#101735d9,#111827a8);border:1px solid #ffffff22;box-shadow:0 30px 100px #0008,inset 0 1px #fff2;perspective:1200px}
.nova:after{content:"";position:absolute;width:380px;height:380px;border-radius:50%;right:-100px;top:-160px;background:linear-gradient(135deg,#22d3ee55,#8b5cf633);filter:blur(2px);box-shadow:0 0 90px #22d3ee33}
.logo{font-size:12px;letter-spacing:4px;color:#67e8f9;font-weight:700}.nova h1{font-size:58px;line-height:1;margin:12px 0;background:linear-gradient(90deg,#fff,#67e8f9,#c4b5fd);-webkit-background-clip:text;color:transparent}.nova p{max-width:800px;color:#a7b0ca;font-size:17px;line-height:1.7}
.metric{padding:18px;border-radius:20px;background:#ffffff08;border:1px solid #ffffff18;box-shadow:inset 0 1px #fff1;transform:translateZ(18px)}
.metric b{font-size:28px;color:#fff}.metric span{display:block;color:#8490ad;font-size:12px;margin-top:4px}
.panel{padding:22px;border-radius:24px;background:#0b1124cc;border:1px solid #ffffff15;box-shadow:0 20px 60px #0006}
.scheme3d{background:linear-gradient(145deg,#111a35,#0b1022);border:1px solid #ffffff18;border-radius:24px;padding:22px;min-height:290px;box-shadow:12px 18px 45px #0007,inset 0 1px #fff1;transition:.35s;transform:perspective(900px) rotateX(1deg) rotateY(-1deg)}
.scheme3d:hover{transform:perspective(900px) rotateX(-2deg) rotateY(3deg) translateY(-8px) scale(1.01);border-color:#67e8f966;box-shadow:20px 30px 70px #0009,0 0 35px #22d3ee18}
.scheme3d h3{color:#f8fafc;font-size:20px;margin:0 0 12px}.small{color:#8d99b5;font-size:12px;line-height:1.65}.chip{display:inline-block;padding:6px 9px;border-radius:999px;background:#67e8f912;border:1px solid #67e8f933;color:#67e8f9;font-size:10px;margin:2px;font-weight:700}
.stButton>button,.stLinkButton>a{border-radius:12px!important;border:1px solid #67e8f944!important;background:linear-gradient(135deg,#67e8f916,#8b5cf616)!important;font-weight:700!important}
.stButton>button:hover,.stLinkButton>a:hover{border-color:#67e8f9aa!important;box-shadow:0 0 25px #22d3ee22!important}
/* NOVA's age control follows the cyan/violet background palette. */
[data-testid="stSlider"] [role="slider"]{background:#67e8f9!important;border:3px solid #c4b5fd!important;box-shadow:0 0 18px #22d3ee88!important}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div{background:linear-gradient(90deg,#22d3ee,#8b5cf6)!important}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div{background:#17203b!important}
.help-wrap{display:flex;justify-content:flex-end;align-items:center;gap:10px;margin-bottom:8px}
.help-bubble{padding:9px 14px;border-radius:18px 18px 4px 18px;background:#101a35ee;border:1px solid #67e8f955;color:#dbeafe;font-size:13px;box-shadow:0 0 22px #22d3ee22;white-space:nowrap}
.robot-button{font-size:25px!important;min-height:48px!important;width:52px!important;padding:0!important;border-radius:50%!important}
.chat-panel{position:sticky;top:16px;max-height:calc(100vh - 32px);overflow-y:auto}
.chat-title{font-size:20px;font-weight:700;background:linear-gradient(90deg,#fff,#67e8f9);-webkit-background-clip:text;color:transparent}
.chat-note{color:#7f8baa;font-size:11px;line-height:1.5}
[data-testid="stTabs"] button{color:#94a3b8!important}
</style>
""", unsafe_allow_html=True)

if "nova_help" not in st.session_state:
    st.session_state.nova_help = False
if "nova_results" not in st.session_state:
    st.session_state.nova_results = None
if "nova_bot" not in st.session_state:
    st.session_state.nova_bot = SchemeChatbot()
if "nova_messages" not in st.session_state:
    st.session_state.nova_messages = [
        {"role": "assistant", "content": "Hey! 🤖 I’m NOVA. Tell me what you need and I’ll search the scheme universe."}
    ]

# Top-right robot + speech bubble.
h1, h2 = st.columns([8.5, 1.5])
with h2:
    st.markdown('<div class="help-wrap"><div class="help-bubble">Need help?</div>', unsafe_allow_html=True)
    if st.button("🤖", key="help_toggle", help="Open NOVA assistant", use_container_width=True):
        st.session_state.nova_help = not st.session_state.nova_help
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""<div class="nova"><div class="logo">NOVA // PUBLIC BENEFIT INTELLIGENCE</div>
<h1>Find what you're eligible for.</h1>
<p>A futuristic government-scheme recommender built for students, young professionals, families, workers, entrepreneurs and everyone in between.</p></div>""", unsafe_allow_html=True)

m1,m2,m3 = st.columns(3)
with m1: st.markdown(f'<div class="metric"><b>{total_schemes()}+</b><span>scheme records loaded</span></div>', unsafe_allow_html=True)
with m2: st.markdown('<div class="metric"><b>OFFICIAL</b><span>portal/application links from the dataset</span></div>', unsafe_allow_html=True)
with m3: st.markdown('<div class="metric"><b>AI</b><span>explainable local matching + chatbot</span></div>', unsafe_allow_html=True)
st.write("")

# When the assistant is open, it occupies about 30% of the right side.
main_col, chat_col = st.columns([7, 3] if st.session_state.nova_help else [1, 0.0001], gap="large")

with main_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("◈ Build your profile")
    age = st.slider("Age", 0, 100, 19, help="Move the handle to your age. The cyan/violet style matches NOVA's background.")
    occupation = st.selectbox("I am a", ["Any", "Student", "Farmer", "Worker", "Entrepreneur", "Artisan", "Street Vendor", "Unemployed", "Women", "Senior Citizen"])
    state = st.selectbox("My state / coverage", ["All India","Andhra Pradesh","Assam","Bihar","Chhattisgarh","Delhi","Gujarat","Haryana","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Odisha","Punjab","Rajasthan","Tamil Nadu","Telangana","Uttar Pradesh","Uttarakhand","West Bengal"])
    income = st.number_input("Annual household income (₹)", min_value=0, max_value=10000000, value=300000, step=10000)
    keyword = st.text_input("What do you want?", placeholder="scholarship, business loan, health, housing...")
    run = st.button("⚡ Scan the scheme universe", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if run or st.session_state.nova_results is None:
        st.session_state.nova_results = search_schemes(
            age, income, "Any", occupation, state, keyword.strip() or None, 8
        )

    results = st.session_state.nova_results
    st.subheader("✦ Your matches")
    st.caption(f"{len(results)} result(s) surfaced from the {total_schemes()}-record local recommendation engine.")
    if results:
        c1, c2 = st.columns(2)
        for i, scheme in enumerate(results):
            with c1 if i % 2 == 0 else c2:
                summary = scheme.get("summary") or "Government support programme."
                eligibility = scheme.get("eligibility") or "Check the current eligibility rules on the official portal."
                benefits = scheme.get("benefits") or "See the official scheme page for current benefits."
                st.markdown(f"""<div class="scheme3d"><div class="chip">{scheme['category']}</div><div class="chip">{scheme['state']}</div>
                <h3>{scheme['name']}</h3><div class="small">{summary}</div><br>
                <div class="small"><b>Eligibility:</b> {eligibility[:600]}</div><br>
                <div class="small"><b>Benefit:</b> {benefits[:500]}</div></div>""", unsafe_allow_html=True)
                st.link_button("Open official portal ↗", scheme["application_url"], use_container_width=True)
    else:
        st.info("No strong match. Try All India, a broader keyword, or a different occupation.")

with chat_col:
    if st.session_state.nova_help:
        st.markdown('<div class="panel chat-panel"><div class="chat-title">🤖 NOVA assistant</div><div class="chat-note">30% side panel • grounded in the loaded scheme records</div>', unsafe_allow_html=True)
        for message in st.session_state.nova_messages:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🧑"):
                st.markdown(message["content"])
        with st.form("nova_chat", clear_on_submit=True):
            q = st.text_input("Ask NOVA", placeholder="I'm 20, a student in UP and need a scholarship")
            send = st.form_submit_button("Send →", type="primary", use_container_width=True)
        if send and q.strip():
            st.session_state.nova_messages.append({"role": "user", "content": q.strip()})
            answer = st.session_state.nova_bot.respond(q.strip())
            st.session_state.nova_messages.append({"role": "assistant", "content": answer})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.caption("NOVA is a school-project recommendation tool, not a government authority. Scheme rules can change. Verify current eligibility and application instructions on the linked official portal before applying.")
