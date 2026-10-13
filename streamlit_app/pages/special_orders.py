import re
import os
from datetime import date, timedelta
import requests
import streamlit as st

# Automatically load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Price per item (standard reference price)
PRICE_PER_ITEM = 2500

st.set_page_config(
    page_title="Special Order · On the Go Plantain Chips",
    page_icon="⭐",
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
        radial-gradient(ellipse 80% 60% at 20% -10%, rgba(255,160,0,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 110%, rgba(255,80,0,0.14) 0%, transparent 55%),
        linear-gradient(160deg, #100a06 0%, #160f08 40%, #0c0814 100%);
    min-height: 100vh;
}

/* Strip Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none; }
.block-container {
    padding: 2.2rem 1.5rem 4rem;
    max-width: 660px;
}

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 2.5rem 1.5rem 2rem;
    margin-bottom: 0.5rem;
    position: relative;
}
.hero-glow {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -55%);
    width: 340px; height: 180px;
    background: radial-gradient(ellipse, rgba(255,190,0,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero-icon {
    font-size: 3.8rem;
    line-height: 1;
    display: block;
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 26px rgba(255,200,0,0.65));
    animation: float 4s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-7px); }
}
.hero-title {
    font-size: 2.15rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.8px;
    margin: 0 0 0.6rem;
    line-height: 1.18;
}
.hero-title span {
    background: linear-gradient(90deg, #FFC700, #FF7A00, #FF4500);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.92rem;
    color: rgba(255,255,255,0.5);
    font-weight: 400;
    letter-spacing: 0.2px;
}
.special-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: linear-gradient(135deg, rgba(255,180,0,0.15) 0%, rgba(255,80,0,0.12) 100%);
    border: 1.5px solid rgba(255,190,0,0.35);
    border-radius: 100px;
    padding: 0.4rem 1.1rem;
    font-size: 0.76rem;
    font-weight: 700;
    color: #FFB700;
    margin-top: 1rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    box-shadow: 0 0 20px rgba(255,180,0,0.12);
}
.special-banner {
    background: rgba(255,180,0,0.06);
    border: 1px solid rgba(255,180,0,0.18);
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
    margin: 1.2rem 0 1.8rem;
    font-size: 0.8rem;
    color: rgba(255,255,255,0.7);
    line-height: 1.55;
    text-align: left;
}
.special-banner strong {
    color: #FFB700;
}

/* ── Section Divider ── */
.section-head {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 1.8rem 0 1rem;
}
.section-head-icon {
    width: 32px; height: 32px;
    background: rgba(255,180,0,0.12);
    border: 1px solid rgba(255,180,0,0.25);
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
    flex-shrink: 0;
}
.section-head-text {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
}

/* ── Input field overrides ── */
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stDateInput"] label {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    color: rgba(255,255,255,0.65) !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 0.4rem !important;
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
    font-size: 1.02rem !important;
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

/* Textarea overrides (Prominent Star Component) */
div[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(255,180,0,0.35) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 1rem !important;
    transition: all 0.22s ease !important;
    line-height: 1.65 !important;
    box-shadow: inset 0 2px 6px rgba(0,0,0,0.3) !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: #FFB700 !important;
    box-shadow: 0 0 0 4px rgba(255,180,0,0.18), inset 0 2px 6px rgba(0,0,0,0.3) !important;
}
div[data-testid="stTextArea"] textarea::placeholder {
    color: rgba(255,255,255,0.28) !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
}

/* Date input overrides */
div[data-testid="stDateInput"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stDateInput"] input {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.02rem !important;
    font-weight: 600 !important;
}
div[data-testid="stDateInput"] > div > div:focus-within {
    border-color: rgba(255,180,0,0.6) !important;
    box-shadow: 0 0 0 3px rgba(255,180,0,0.12) !important;
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
div[data-baseweb="radio"]:has(input:checked),
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    border-color: rgba(255,180,0,0.75) !important;
    background: rgba(255,180,0,0.12) !important;
    box-shadow: 0 0 0 1px rgba(255,180,0,0.25), 0 8px 24px rgba(255,140,0,0.12) !important;
}
div[data-baseweb="radio"] [role="radio"],
div[data-baseweb="radio"] svg,
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child,
div[data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}
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

/* ── Estimated Total Box ── */
.total-wrap {
    position: relative;
    background: rgba(255,180,0,0.04);
    border: 1.5px solid rgba(255,180,0,0.22);
    border-radius: 16px;
    padding: 1.3rem;
    text-align: center;
    margin: 1.2rem 0;
    overflow: hidden;
}
.total-eyebrow {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,180,0,0.65);
    margin-bottom: 0.4rem;
}
.total-number {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: #FFB700;
    line-height: 1;
    text-shadow: 0 0 30px rgba(255,180,0,0.3);
}
.total-detail {
    font-size: 0.76rem;
    color: rgba(255,255,255,0.45);
    margin-top: 0.5rem;
    line-height: 1.4;
}

/* ── Submit Button ── */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #FFB700 0%, #FF6200 100%) !important;
    color: #12080a !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    letter-spacing: 0.5px !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.95rem 1.5rem !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 4px 26px rgba(255,140,0,0.4), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transition: all 0.2s ease !important;
}
.stFormSubmitButton > button:hover {
    filter: brightness(1.1) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 34px rgba(255,140,0,0.5) !important;
}

/* ── Navigation bar at top ── */
.nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    color: rgba(255,180,0,0.75);
    font-size: 0.82rem;
    font-weight: 600;
    text-decoration: none;
    letter-spacing: 0.3px;
    padding: 0.4rem 0.8rem;
    background: rgba(255,180,0,0.08);
    border: 1px solid rgba(255,180,0,0.18);
    border-radius: 100px;
    transition: all 0.2s ease;
}
.back-link:hover {
    color: #FFB700;
    background: rgba(255,180,0,0.15);
    border-color: rgba(255,180,0,0.35);
}

/* ── Footer ── */
.footer {
    text-align: center;
    color: rgba(255,255,255,0.2);
    font-size: 0.72rem;
    margin-top: 3rem;
    line-height: 1.8;
}
.hint {
    font-size: 0.74rem;
    color: rgba(255,255,255,0.35);
    margin: -0.2rem 0 0.9rem 0.1rem;
    line-height: 1.45;
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


def send_special_order_telegram(name, whatsapp, ripe_chips, unripe_chips, location, delivery_date, address, special_instructions, total):
    """Send a SPECIAL ORDER notification in CAPS to the seller's Telegram."""
    bot_token = get_config_value("TELEGRAM_BOT_TOKEN")
    chat_id   = get_config_value("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise ValueError("Telegram is not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to secrets.")

    loc_icon = "🏙️" if location == "MAINLAND" else "🏝️"
    total_packs = ripe_chips + unripe_chips
    address_line = f"🏢 *Address / Landmark:* {address}\n" if address else ""
    price_line = f"💰 *Estimated Total:* ₦{total:,}\n" if total > 0 else "💰 *Quote:* Custom Quote (Pending Seller Review)\n"

    message = (
        f"🚨🚨🚨 *SPECIAL ORDER* 🚨🚨🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Customer:* {name}\n"
        f"📱 *WhatsApp:* `{whatsapp}`\n"
        f"{loc_icon} *Area:* {location}\n"
        f"{address_line}"
        f"📅 *Expected Delivery:* {delivery_date}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟡 *Ripe Packs (Est.):* {ripe_chips}\n"
        f"🟢 *Unripe Packs (Est.):* {unripe_chips}\n"
        f"📦 *Total Est. Packs:* {total_packs}\n"
        f"{price_line}"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *SPECIAL ORDER SPECIFICS:*\n"
        f"{special_instructions}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        },
        timeout=15,
    )
    if not resp.ok:
        raise RuntimeError(f"Telegram API error: {resp.status_code} - {resp.text}")


def save_special_order_to_database(name, whatsapp, ripe_chips, unripe_chips, location, delivery_date, full_instructions, total):
    """Save the special order to the database with is_special = TRUE."""
    db_url     = get_config_value("DATABASE_URL")
    enc_key    = get_config_value("ENCRYPTION_KEY")
    supabase_url  = get_config_value("SUPABASE_URL")
    supabase_key  = get_config_value("SUPABASE_KEY")

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
                    "INSERT INTO orders (name, whatsapp_enc, ripe_chips, unripe_chips, location, total, delivery_date, special_instructions, is_special) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (name.strip(), whatsapp_enc, ripe_chips, unripe_chips, location, total,
                     str(delivery_date), full_instructions.strip(), True),
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
            "delivery_date": str(delivery_date),
            "special_instructions": full_instructions.strip(),
            "is_special": True,
        }
        res = requests.post(f"{supabase_url.rstrip('/')}/rest/v1/orders",
                            json=payload, headers=headers, timeout=15)
        if not res.ok:
            raise RuntimeError(f"Supabase REST error: {res.status_code} - {res.text}")
        return total

    else:
        raise ValueError("No backend configured. Add DATABASE_URL + ENCRYPTION_KEY to secrets.")


# ── Top Navigation Bar ────────────────────────────────────────────────────────
col_nav_left, col_nav_right = st.columns([1, 1])
with col_nav_left:
    try:
        st.page_link("app.py", label="← Back to Regular Orders", icon="🍌")
    except Exception:
        st.markdown('<a class="back-link" href="/" target="_self">← Back to Regular Orders</a>', unsafe_allow_html=True)
with col_nav_right:
    st.markdown("""
    <div style="text-align: right; font-size: 0.72rem; color: rgba(255,255,255,0.25); padding-top: 0.3rem;">
        ✦ &nbsp;CREATED BY &nbsp;<strong style="color: rgba(255,180,0,0.6);">OSAZUWA</strong>
    </div>
    """, unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-glow"></div>
    <span class="hero-icon">⭐</span>
    <h1 class="hero-title">Special Order<br><span>"On the Go" Plantain Chips</span></h1>
    <p class="hero-sub">Custom Recipes · Event Catering · Bulk Batches · Flexible Dates</p>
    <div>
        <span class="special-badge">✨ BESPOKE &amp; BULK ORDERS</span>
    </div>
    <div class="special-banner">
        <strong>How Special Orders Work:</strong> Need custom seasoning (extra spicy, unsalted, garlic herb), bulk party tubs, custom gift packaging, or delivery on a specific date? Tell us exactly what you need in the form below. Once received, the seller will personally review your request and message you on WhatsApp to confirm details &amp; pricing!
    </div>
</div>
""", unsafe_allow_html=True)


# ── Special Order Form ────────────────────────────────────────────────────────
with st.form("special_order_form", clear_on_submit=False):

    # 1. Contact details
    st.markdown("""
    <div class="section-head">
        <div class="section-head-icon">👤</div>
        <span class="section-head-text">1. Your Contact Details</span>
    </div>
    """, unsafe_allow_html=True)

    name = st.text_input("Full Name", placeholder="e.g. Amaka Johnson", max_chars=100)
    whatsapp = st.text_input("WhatsApp Number", placeholder="+2348012345678", max_chars=20)
    st.markdown(
        "<div class='hint'>Include country code · digits only · e.g. +2348012345678</div>",
        unsafe_allow_html=True,
    )

    # 2. Delivery & Logistics
    st.markdown("""
    <div class="section-head" style="margin-top:0.8rem">
        <div class="section-head-icon">📍</div>
        <span class="section-head-text">2. Delivery Logistics</span>
    </div>
    """, unsafe_allow_html=True)

    location = st.radio(
        "Delivery Area",
        options=["🏙️  MAINLAND", "🏝️  ISLAND"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )
    location = "MAINLAND" if "MAINLAND" in location else "ISLAND"

    col_date, col_addr = st.columns(2)
    with col_date:
        delivery_date = st.date_input(
            "Expected Delivery Date",
            value=date.today() + timedelta(days=7),
            min_value=date.today() + timedelta(days=1),
            help="When do you need this order ready and delivered?",
        )
    with col_addr:
        address = st.text_input(
            "Delivery Landmark / Address (Optional)",
            placeholder="e.g. Admiralty Way, Lekki Phase 1",
            max_chars=200,
        )

    # 3. The Core Feature: Order Specifics Text Area
    st.markdown("""
    <div class="section-head" style="margin-top:0.8rem">
        <div class="section-head-icon">📝</div>
        <span class="section-head-text">3. Describe Your Special Order</span>
    </div>
    """, unsafe_allow_html=True)

    special_instructions = st.text_area(
        "Special Order Specifics (More information about your order)",
        placeholder="Type all details of what you want to order here:\n\n"
                    "• Chip Details: e.g. I want 55 ripe chips and 35 unripe chips\n"
                    "• Timing & Special Requests: e.g. deliver before 12 PM on event day",
        height=210,
        max_chars=2000,
        help="Ensure important information is put in",
    )
    st.markdown(
        "<div class='hint'>⭐ This text area is the main information the seller uses to prepare your custom batch.</div>",
        unsafe_allow_html=True,
    )

    # 4. Optional Quick Pack Breakdown
    st.markdown("""
    <div class="section-head" style="margin-top:0.8rem">
        <div class="section-head-icon">📦</div>
        <span class="section-head-text">4. Estimated Pack Breakdown (Optional Guide)</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ripe_chips = st.number_input(
            "🟡 Ripe Packs (Sweet)",
            min_value=0,
            max_value=9999,
            step=1,
            value=0,
            key="special_ripe_qty",
            help="If ordering by standard packs, enter your target ripe count.",
        )
    with col2:
        unripe_chips = st.number_input(
            "🟢 Unripe Packs (Savoury)",
            min_value=0,
            max_value=9999,
            step=1,
            value=0,
            key="special_unripe_qty",
            help="If ordering by standard packs, enter your target unripe count.",
        )

    total_packs = int(ripe_chips + unripe_chips)
    estimated_total = int(total_packs * PRICE_PER_ITEM)

    if total_packs > 0:
        st.markdown(f"""
        <div class="total-wrap">
            <div class="total-eyebrow">Estimated Base Total ({total_packs} packs)</div>
            <div class="total-number">₦{estimated_total:,}</div>
            <div class="total-detail">
                {ripe_chips} ripe + {unripe_chips} unripe × standard ₦{PRICE_PER_ITEM:,}/pack.<br>
                <em>Note: Custom seasonings, bulk discounts, or special packaging will be confirmed via WhatsApp.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="total-wrap" style="padding: 1rem;">
            <div class="total-eyebrow">Custom Pricing Notice</div>
            <div class="total-detail" style="font-size:0.8rem; color: rgba(255,255,255,0.6);">
                No standard pack count selected above. The seller will calculate your custom quote based on the specifics described in the text area.
            </div>
        </div>
        """, unsafe_allow_html=True)

    submitted = st.form_submit_button("⭐  Submit Special Order Request", use_container_width=True)


# ── Submission handler ────────────────────────────────────────────────────────
if submitted:
    cleaned_name     = name.strip()
    cleaned_whatsapp = whatsapp.strip()
    cleaned_instructions = special_instructions.strip()
    cleaned_address = address.strip()

    if not cleaned_name:
        st.error("❌ Please enter your full name.")
    elif not re.fullmatch(r"^\+?\d{7,15}$", cleaned_whatsapp):
        st.error("❌ Please enter a valid WhatsApp number (7–15 digits, optional '+' prefix).")
    elif not cleaned_instructions:
        st.error("❌ Please type your order details in the 'Describe Your Special Order' text area.")
    else:
        # Build combined instructions including address if supplied
        full_instructions = cleaned_instructions
        if cleaned_address:
            full_instructions = f"Delivery Address: {cleaned_address}\n\n{cleaned_instructions}"

        try:
            with st.spinner("Submitting your special order to the seller…"):
                # Save to database
                final_total = save_special_order_to_database(
                    name=cleaned_name,
                    whatsapp=cleaned_whatsapp,
                    ripe_chips=int(ripe_chips),
                    unripe_chips=int(unripe_chips),
                    location=location,
                    delivery_date=delivery_date,
                    full_instructions=full_instructions,
                    total=estimated_total,
                )
                # Notify seller on Telegram with CAPS SPECIAL ORDER
                send_special_order_telegram(
                    name=cleaned_name,
                    whatsapp=cleaned_whatsapp,
                    ripe_chips=int(ripe_chips),
                    unripe_chips=int(unripe_chips),
                    location=location,
                    delivery_date=str(delivery_date),
                    address=cleaned_address,
                    special_instructions=cleaned_instructions,
                    total=final_total,
                )

            loc_icon = "🏙️" if location == "MAINLAND" else "🏝️"
            st.success(
                f"⭐ **Special Order Received, {cleaned_name}!**\n\n"
                f"- 📅 Expected Delivery: **{delivery_date}**\n"
                f"- {loc_icon} Location: **{location}**\n"
                f"- 📦 Est. Packs: **{ripe_chips} Ripe** / **{unripe_chips} Unripe**\n\n"
                f"Your order specifics have been dispatched directly to the seller's Telegram. "
                f"The seller will contact you shortly on WhatsApp (**{cleaned_whatsapp}**) to confirm details and finalize your custom quote! 🍌"
            )
            st.balloons()
        except Exception as e:
            st.error(f"❌ Special order submission failed: {e}")
            st.info("💡 Admin: check TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and DATABASE_URL in your secrets.")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    🔒 Data is encrypted &amp; sent directly to the seller<br>
    "On the Go" Plantain Chips · Freshly handcrafted for every order
</div>
""", unsafe_allow_html=True)
