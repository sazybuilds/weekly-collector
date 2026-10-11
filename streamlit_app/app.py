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
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: rgba(255,255,255,0.55) !important;
    letter-spacing: 0.4px !important;
    text-transform: uppercase !important;
    margin-bottom: 0.4rem !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    padding: 0.7rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.3) !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    background: rgba(255,180,0,0.05) !important;
    border-color: rgba(255,180,0,0.55) !important;
    box-shadow: 0 0 0 3px rgba(255,180,0,0.1), inset 0 1px 2px rgba(0,0,0,0.2) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: rgba(255,255,255,0.2) !important;
    font-weight: 400 !important;
}

/* Number input spinner buttons */
div[data-testid="stNumberInput"] button {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.09) !important;
    color: rgba(255,255,255,0.6) !important;
    border-radius: 8px !important;
}
div[data-testid="stNumberInput"] button:hover {
    background: rgba(255,180,0,0.15) !important;
    border-color: rgba(255,180,0,0.3) !important;
    color: #FFB700 !important;
}

/* ── Location Radio — card style ── */
div[data-testid="stRadio"] > label { display: none !important; }
div[data-baseweb="radio-group"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 0.75rem !important;
    margin: 0.5rem 0 1.25rem !important;
}
div[data-baseweb="radio"] {
    flex: 1 !important;
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    padding: 1.25rem 1rem !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: all 0.22s ease !important;
    align-items: center !important;
    justify-content: center !important;
}
div[data-baseweb="radio"]:hover {
    border-color: rgba(255,180,0,0.35) !important;
    background: rgba(255,180,0,0.05) !important;
    transform: translateY(-2px) !important;
}
/* Selected card */
div[data-baseweb="radio"]:has(input:checked) {
    border-color: rgba(255,180,0,0.7) !important;
    background: rgba(255,180,0,0.1) !important;
    box-shadow: 0 0 0 1px rgba(255,180,0,0.25), 0 8px 24px rgba(255,140,0,0.12) !important;
}
/* Hide radio circle dot */
div[data-baseweb="radio"] [role="radio"],
div[data-baseweb="radio"] svg { display: none !important; }
/* Label text */
div[data-baseweb="radio"] > div:last-child,
div[data-baseweb="radio"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.6px !important;
    color: rgba(255,255,255,0.65) !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-baseweb="radio"]:has(input:checked) > div:last-child,
div[data-baseweb="radio"]:has(input:checked) label {
    color: #FFB700 !important;
}

/* ── Pack Selector Row ── */
.pack-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}
.pack-block {
    background: rgba(255,255,255,0.03);
    border: 1.5px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1rem 1rem 0.75rem;
    transition: border-color 0.2s;
}
.pack-block:focus-within {
    border-color: rgba(255,180,0,0.4);
}
.pack-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.6rem;
}
.pack-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-ripe   { background: #FFD000; box-shadow: 0 0 6px rgba(255,208,0,0.5); }
.dot-unripe { background: #44E070; box-shadow: 0 0 6px rgba(68,224,112,0.4); }
.pack-label {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: rgba(255,255,255,0.55);
    text-transform: uppercase;
}
.pack-desc {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.25);
    margin-top: 0.1rem;
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
    <div style="display:flex;justify-content:center">
        <span class="deadline-pill">⏰ &nbsp;Orders close every Wednesday at 5 PM</span>
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
    <div class="pack-row">
        <div class="pack-block">
            <div class="pack-header">
                <div class="pack-dot dot-ripe"></div>
                <div>
                    <div class="pack-label">Ripe Chips</div>
                    <div class="pack-desc">Sweet &amp; golden · ₦2,500</div>
                </div>
            </div>
        </div>
        <div class="pack-block">
            <div class="pack-header">
                <div class="pack-dot dot-unripe"></div>
                <div>
                    <div class="pack-label">Unripe Chips</div>
                    <div class="pack-desc">Savoury &amp; crisp · ₦2,500</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ripe_chips = st.number_input(
            "Ripe Chips (packs)", min_value=0, max_value=999, step=1, value=0,
            label_visibility="collapsed",
        )
    with col2:
        unripe_chips = st.number_input(
            "Unripe Chips (packs)", min_value=0, max_value=999, step=1, value=0,
            label_visibility="collapsed",
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
