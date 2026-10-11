import re
import os
import requests
import streamlit as st

# Automatically load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Price per item
PRICE_PER_ITEM = 2500

st.set_page_config(
    page_title="Plantain Chips Order",
    page_icon="🍌",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Premium CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── App Background ── */
.stApp {
    background:
        radial-gradient(ellipse 80% 60% at 20% -10%, rgba(120,80,255,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 110%, rgba(255,160,0,0.12) 0%, transparent 55%),
        linear-gradient(160deg, #080612 0%, #0d0b1e 40%, #0a0f1c 100%);
    min-height: 100vh;
}

/* Strip Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none; }
.block-container {
    padding: 2.5rem 1.5rem 4rem;
    max-width: 660px;
}

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 3rem 1.5rem 2.5rem;
    margin-bottom: 0.5rem;
    position: relative;
}
.hero-glow {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -55%);
    width: 320px; height: 160px;
    background: radial-gradient(ellipse, rgba(255,165,0,0.13) 0%, transparent 70%);
    pointer-events: none;
}
.hero-icon {
    font-size: 4rem;
    line-height: 1;
    display: block;
    margin-bottom: 1.1rem;
    filter: drop-shadow(0 0 24px rgba(255,180,0,0.55));
    animation: float 4s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-8px); }
}
.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.8px;
    margin: 0 0 0.6rem;
    line-height: 1.15;
}
.hero-title span {
    background: linear-gradient(90deg, #FFB700, #FF7A00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.38);
    font-weight: 400;
    letter-spacing: 0.2px;
}
.deadline-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255,180,0,0.1);
    border: 1px solid rgba(255,180,0,0.22);
    border-radius: 100px;
    padding: 0.3rem 0.9rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: rgba(255,180,0,0.85);
    margin-top: 1rem;
    letter-spacing: 0.3px;
}
.deadline-notice {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.48);
    margin-top: 0.55rem;
    line-height: 1.45;
    max-width: 440px;
}

/* ── Section Divider ── */
.section-head {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 1.8rem 0 1rem;
}
.section-head-icon {
    width: 30px; height: 30px;
    background: rgba(255,180,0,0.1);
    border: 1px solid rgba(255,180,0,0.2);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
}
.section-head-text {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
}

/* ── Input field overrides ── */
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    color: rgba(255,255,255,0.6) !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 0.4rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.4rem !important;
}

/* Input container styles */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[data-testid="stNumberInput"] div[data-baseweb="base-input"],
div[data-testid="stNumberInput"] > div,
div[data-testid="stNumberInput"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: transparent !important;
    border: none !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 0.9rem !important;
}
div[data-testid="stNumberInput"] input {
    text-align: center !important;
}
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stNumberInput"] > div:focus-within {
    border-color: rgba(255,180,0,0.6) !important;
    box-shadow: 0 0 0 3px rgba(255,180,0,0.12) !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: rgba(255,255,255,0.2) !important;
    font-weight: 400 !important;
}

/* Number input spinner buttons */
div[data-testid="stNumberInput"] button {
    background: rgba(255,255,255,0.08) !important;
    border: none !important;
    color: rgba(255,255,255,0.7) !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stNumberInput"] button:hover {
    background: rgba(255,180,0,0.25) !important;
    color: #FFB700 !important;
}

/* ── Location Radio — sleek cards ── */
div[data-testid="stRadio"] > label { display: none !important; }
div[data-baseweb="radio-group"],
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 0.75rem !important;
    margin: 0.5rem 0 1.25rem !important;
}
div[data-baseweb="radio"],
div[data-testid="stRadio"] div[role="radiogroup"] > label {
    flex: 1 !important;
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    padding: 1.1rem 0.75rem !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: all 0.22s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
div[data-baseweb="radio"]:hover,
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    border-color: rgba(255,180,0,0.35) !important;
    background: rgba(255,180,0,0.05) !important;
    transform: translateY(-2px) !important;
}
/* Selected card */
div[data-baseweb="radio"]:has(input:checked),
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    border-color: rgba(255,180,0,0.75) !important;
    background: rgba(255,180,0,0.12) !important;
    box-shadow: 0 0 0 1px rgba(255,180,0,0.25), 0 8px 24px rgba(255,140,0,0.12) !important;
}
/* Hide radio circle dot */
div[data-baseweb="radio"] [role="radio"],
div[data-baseweb="radio"] svg,
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child,
div[data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}
/* Label text */
div[data-baseweb="radio"] label,
div[data-testid="stRadio"] div[role="radiogroup"] > label * {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.6px !important;
    color: rgba(255,255,255,0.65) !important;
}
div[data-baseweb="radio"]:has(input:checked) label,
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) * {
    color: #FFB700 !important;
}

/* ── Pack Cards (Ripe & Unripe) ── */
.pack-card {
    background: rgba(255,255,255,0.03);
    border-radius: 14px;
    padding: 1rem 0.95rem;
    margin-bottom: 0.65rem;
    transition: all 0.22s ease;
    border: 1.5px solid rgba(255, 255, 255, 0.08);
}
.pack-card:hover {
    border-color: rgba(255, 255, 255, 0.22);
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
}
.pack-card-ripe,
.pack-card-unripe {
    border: 1.5px solid rgba(255, 255, 255, 0.09);
    background: rgba(255, 255, 255, 0.03);
}
.pack-card-ripe:hover,
.pack-card-unripe:hover {
    border-color: rgba(255, 255, 255, 0.25);
}

.pack-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
.pack-pill {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.8px;
    padding: 0.22rem 0.6rem;
    border-radius: 100px;
    text-transform: uppercase;
    background: rgba(255, 255, 255, 0.07);
    color: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
}
.pill-ripe,
.pill-unripe {
    background: rgba(255, 255, 255, 0.07);
    color: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
}

.pack-price {
    font-size: 0.95rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.3px;
}
.pack-unit {
    font-size: 0.65rem;
    font-weight: 400;
    color: rgba(255,255,255,0.4);
}

.pack-title {
    font-size: 1.1rem;
    font-weight: 800;
    letter-spacing: -0.3px;
    margin-bottom: 0.2rem;
    display: flex;
    align-items: center;
    gap: 0.45rem;
    color: #ffffff !important;
}
.ripe-text,
.unripe-text {
    color: #ffffff !important;
}

.pack-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.7);
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.25);
}
.dot-ripe,
.dot-unripe {
    background: rgba(255, 255, 255, 0.7);
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.25);
}

.pack-desc {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.4);
    line-height: 1.35;
}

/* Pack inputs — clean white text */
div[data-testid="stColumn"] div[data-testid="stNumberInput"] label {
    color: #ffffff !important;
    font-weight: 700 !important;
}
div[data-testid="stColumn"] div[data-testid="stNumberInput"] > div,
div[data-testid="stColumn"] div[data-testid="stNumberInput"] > div > div {
    border-color: rgba(255, 255, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.04) !important;
}
div[data-testid="stColumn"] div[data-testid="stNumberInput"] > div:focus-within {
    border-color: rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.12) !important;
}
div[data-testid="stColumn"] div[data-testid="stNumberInput"] input {
    color: #ffffff !important;
}
div[data-testid="stColumn"] div[data-testid="stNumberInput"] button {
    color: rgba(255, 255, 255, 0.8) !important;
}
div[data-testid="stColumn"] div[data-testid="stNumberInput"] button:hover {
    color: #ffffff !important;
    background: rgba(255, 255, 255, 0.12) !important;
}

/* Responsive: clean column stacking and clear separation on small screens */
@media (max-width: 640px) {
    div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 1.25rem !important;
    }
    div[data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    div[data-testid="stColumn"]:last-child {
        margin-top: 0.25rem !important;
        padding-top: 1.25rem !important;
        border-top: 1px dashed rgba(255,255,255,0.12) !important;
    }
}

/* ── Order Total ── */
.total-wrap {
    position: relative;
    background: rgba(255,255,255,0.03);
    border: 1.5px solid rgba(255,180,0,0.2);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    margin: 0.25rem 0 1.5rem;
    overflow: hidden;
}
.total-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,183,0,0.06) 0%, rgba(255,100,0,0.04) 100%);
    pointer-events: none;
}
.total-eyebrow {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,180,0,0.5);
    margin-bottom: 0.5rem;
}
.total-number {
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1.5px;
    color: #FFB700;
    line-height: 1;
    text-shadow: 0 0 40px rgba(255,180,0,0.3);
}
.total-detail {
    font-size: 0.76rem;
    color: rgba(255,255,255,0.28);
    margin-top: 0.5rem;
    font-weight: 400;
}

/* ── Submit Button ── */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #FFB700 0%, #FF6200 100%) !important;
    color: #12080a !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.5px !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 1.5rem !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 4px 24px rgba(255,140,0,0.35), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all 0.18s ease !important;
    position: relative !important;
}
.stFormSubmitButton > button:hover {
    filter: brightness(1.1) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(255,140,0,0.45) !important;
}
.stFormSubmitButton > button:active {
    transform: translateY(0) !important;
    filter: brightness(0.97) !important;
    box-shadow: 0 2px 12px rgba(255,140,0,0.3) !important;
}

/* ── Notifications ── */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Divider ── */
.hr { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 0.5rem 0 1.5rem; }

/* ── Footer ── */
.footer {
    text-align: center;
    color: rgba(255,255,255,0.15);
    font-size: 0.72rem;
    margin-top: 3rem;
    line-height: 1.8;
}
.footer a { color: rgba(255,180,0,0.4); text-decoration: none; }

/* ── Hint ── */
.hint {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.28);
    margin: -0.3rem 0 1rem 0.1rem;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_config_value(name: str, default: str = None) -> str:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    val = os.environ.get(name, default)
    return val.strip() if isinstance(val, str) else val


def save_to_database(name, whatsapp, ripe_chips, unripe_chips, location, total):
    db_url     = get_config_value("DATABASE_URL")
    enc_key    = get_config_value("ENCRYPTION_KEY")
    supabase_url  = get_config_value("SUPABASE_URL")
    supabase_key  = get_config_value("SUPABASE_KEY")
    api_url    = get_config_value("API_URL")
    api_key    = get_config_value("API_KEY")

    # Mode 1: Direct Postgres
    if db_url:
        import psycopg2
        from cryptography.fernet import Fernet
        if not enc_key:
            raise ValueError("ENCRYPTION_KEY is missing.")
        fernet = Fernet(enc_key.encode())
        whatsapp_enc = fernet.encrypt(whatsapp.strip().encode()).decode()
        conn = psycopg2.connect(db_url)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (name, whatsapp_enc, ripe_chips, unripe_chips, location, total) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (name.strip(), whatsapp_enc, ripe_chips, unripe_chips, location, total),
                )
        finally:
            conn.close()
        return total

    # Mode 2: Supabase REST
    elif supabase_url and supabase_key:
        from cryptography.fernet import Fernet
        if not enc_key:
            raise ValueError("ENCRYPTION_KEY is missing.")
        fernet = Fernet(enc_key.encode())
        whatsapp_enc = fernet.encrypt(whatsapp.strip().encode()).decode()
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        payload = {
            "name": name.strip(), "whatsapp_enc": whatsapp_enc,
            "ripe_chips": ripe_chips, "unripe_chips": unripe_chips,
            "location": location, "total": total,
        }
        res = requests.post(f"{supabase_url.rstrip('/')}/rest/v1/orders",
                            json=payload, headers=headers, timeout=15)
        if not res.ok:
            raise RuntimeError(f"Supabase REST error: {res.status_code} - {res.text}")
        return total

    # Mode 3: FastAPI backend
    elif api_url and api_key:
        res = requests.post(
            f"{api_url.rstrip('/')}/submit",
            json={"name": name.strip(), "whatsapp": whatsapp.strip(),
                  "ripe_chips": ripe_chips, "unripe_chips": unripe_chips, "location": location},
            headers={"X-API-Key": api_key},
            timeout=30,
        )
        if not res.ok:
            raise RuntimeError(f"API error: {res.status_code} - {res.text}")
        return res.json().get("total", total)

    else:
        raise ValueError("No backend configured. Add DATABASE_URL + ENCRYPTION_KEY to secrets.")


# ── Creator credit ───────────────────────────────────────────────────────────
st.markdown("""
<div style="
    text-align: center;
    padding: 0.55rem 1rem;
    margin-bottom: 0.25rem;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 1.2px;
    color: rgba(255,255,255,0.2);
    border-bottom: 1px solid rgba(255,255,255,0.05);
">
    ✦ &nbsp;CREATED BY &nbsp;<span style="
        color: rgba(255,180,0,0.5);
        font-weight: 700;
        letter-spacing: 2px;
    ">OSAZUWA</span>&nbsp; ✦
</div>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-glow"></div>
    <span class="hero-icon">🍌</span>
    <h1 class="hero-title">Order Fresh<br><span>Plantain Chips</span></h1>
    <p class="hero-sub">Homemade. Crispy. Delivered weekly.</p>
    <div style="display:flex;flex-direction:column;align-items:center">
        <span class="deadline-pill">⏰ &nbsp;Orders close every Wednesday at 5 PM</span>
        <div class="deadline-notice">Orders made later than 5pm might not be delivered as expected but be delivered the following week.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Order Form ────────────────────────────────────────────────────────────────
with st.form("order_form", clear_on_submit=False):

    # Customer details
    st.markdown("""
    <div class="section-head">
        <div class="section-head-icon">👤</div>
        <span class="section-head-text">Your Details</span>
    </div>
    """, unsafe_allow_html=True)

    name = st.text_input("Full Name", placeholder="e.g. Amaka Johnson", max_chars=100)
    whatsapp = st.text_input("WhatsApp Number", placeholder="+2348012345678", max_chars=20)
    st.markdown(
        "<div class='hint'>Include country code · digits only · e.g. +2348012345678</div>",
        unsafe_allow_html=True,
    )

    # ── Delivery Area ──
    st.markdown("""
    <div class="section-head" style="margin-top:0.5rem">
        <div class="section-head-icon">📍</div>
        <span class="section-head-text">Delivery Area</span>
    </div>
    """, unsafe_allow_html=True)

    location = st.radio(
        "Delivery Area",
        options=["🏙️  MAINLAND", "🏝️  ISLAND"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )
    # Normalise to bare keyword
    location = "MAINLAND" if "MAINLAND" in location else "ISLAND"

    # Pack selection
    st.markdown("""
    <div class="section-head" style="margin-top:0.5rem">
        <div class="section-head-icon">📦</div>
        <span class="section-head-text">Choose Your Packs</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="pack-card">
            <div class="pack-top-bar">
                <span class="pack-pill">SWEET &amp; GOLDEN</span>
                <span class="pack-price">₦2,500 <span class="pack-unit">/pk</span></span>
            </div>
            <div class="pack-title">
                <span class="pack-dot"></span> Ripe Chips
            </div>
            <div class="pack-desc">Naturally sweet, crispy plantain slices</div>
        </div>
        """, unsafe_allow_html=True)
        ripe_chips = st.number_input(
            "Ripe Chips (Sweet & Golden)",
            min_value=0,
            max_value=999,
            step=1,
            value=0,
            key="ripe_chips_qty",
        )

    with col2:
        st.markdown("""
        <div class="pack-card">
            <div class="pack-top-bar">
                <span class="pack-pill">SAVOURY &amp; CRISP</span>
                <span class="pack-price">₦2,500 <span class="pack-unit">/pk</span></span>
            </div>
            <div class="pack-title">
                <span class="pack-dot"></span> Unripe Chips
            </div>
            <div class="pack-desc">Lightly salted, savory crunch in every bite</div>
        </div>
        """, unsafe_allow_html=True)
        unripe_chips = st.number_input(
            "Unripe Chips (Savoury & Crisp)",
            min_value=0,
            max_value=999,
            step=1,
            value=0,
            key="unripe_chips_qty",
        )

    # Live total
    total_packs = int(ripe_chips + unripe_chips)
    calculated_total = int(total_packs * PRICE_PER_ITEM)

    if total_packs > 0:
        detail = f"{ripe_chips} ripe + {unripe_chips} unripe = {total_packs} pack(s) × ₦{PRICE_PER_ITEM:,}"
    else:
        detail = "Select packs above to calculate your total"

    st.markdown(f"""
    <div class="total-wrap">
        <div class="total-eyebrow">Order Total</div>
        <div class="total-number">₦{calculated_total:,}</div>
        <div class="total-detail">{detail}</div>
    </div>
    """, unsafe_allow_html=True)

    submitted = st.form_submit_button("🛒  Place My Order", use_container_width=True)


# ── Submission handler ────────────────────────────────────────────────────────
if submitted:
    cleaned_name     = name.strip()
    cleaned_whatsapp = whatsapp.strip()

    if not cleaned_name:
        st.error("❌ Please enter your full name.")
    elif not re.fullmatch(r"^\+?\d{7,15}$", cleaned_whatsapp):
        st.error("❌ Please enter a valid WhatsApp number (7–15 digits, optional '+' prefix).")
    elif total_packs < 1:
        st.error("❌ Please select at least 1 pack of ripe or unripe chips.")
    else:
        try:
            with st.spinner("Placing your order..."):
                final_total = save_to_database(
                    name=cleaned_name,
                    whatsapp=cleaned_whatsapp,
                    ripe_chips=int(ripe_chips),
                    unripe_chips=int(unripe_chips),
                    location=location,
                    total=calculated_total,
                )
            loc_icon = "🏙️" if location == "MAINLAND" else "🏝️"
            st.success(
                f"🎉 Order placed, **{cleaned_name}**!\n\n"
                f"- 🟡 Ripe Chips: **{ripe_chips}** pack(s)\n"
                f"- 🟢 Unripe Chips: **{unripe_chips}** pack(s)\n"
                f"- {loc_icon} Location: **{location}**\n"
                f"- 💰 Total: **₦{final_total:,}**"
            )
            st.balloons()
        except Exception as e:
            st.error(f"❌ Order failed: {e}")
            st.info("💡 Admin: check DATABASE_URL and ENCRYPTION_KEY in your secrets.")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    🔒 Your data is encrypted &amp; never shared<br>
    Orders collected weekly · Closes every <strong style="color:rgba(255,180,0,0.35)">Wednesday at 5 PM</strong>
</div>
""", unsafe_allow_html=True)
