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

# Price per item (in local currency units, e.g. NGN)
PRICE_PER_ITEM = 2500

st.set_page_config(
    page_title="Plantain Chips Order",
    page_icon="🍌",
    layout="centered"
)

# Custom CSS for modern visual polish
st.markdown("""
<style>
    .main-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    .total-badge {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f5132;
        background-color: #d1e7dd;
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        display: inline-block;
        margin-top: 0.5rem;
        width: 100%;
        text-align: center;
    }
    .hint-text {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: -0.5rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍌 Place Your Chips Order")
st.markdown("Select your preferred packs of **Ripe** and **Unripe** plantain chips below.")


def get_config_value(name: str, default: str = None) -> str:
    """
    Retrieves configuration values prioritizing Streamlit secrets,
    falling back to os.environ (.env file or system environment variables).
    """
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    val = os.environ.get(name, default)
    return val.strip() if isinstance(val, str) else val


def save_to_database(name: str, whatsapp: str, ripe_chips: int, unripe_chips: int, total: int):
    """
    Saves the order into Supabase.
    Supports 3 modes based on configuration:
      1. Direct Supabase Postgres connection (DATABASE_URL + ENCRYPTION_KEY) [Recommended]
      2. Supabase REST API (SUPABASE_URL + SUPABASE_KEY + ENCRYPTION_KEY)
      3. FastAPI backend (API_URL + API_KEY)
    """
    db_url = get_config_value("DATABASE_URL")
    enc_key = get_config_value("ENCRYPTION_KEY")
    supabase_url = get_config_value("SUPABASE_URL")
    supabase_key = get_config_value("SUPABASE_KEY")
    api_url = get_config_value("API_URL")
    api_key = get_config_value("API_KEY")

    # Mode 1: Direct Postgres Connection (via Supabase DATABASE_URL)
    if db_url:
        import psycopg2
        from cryptography.fernet import Fernet

        if not enc_key:
            raise ValueError("ENCRYPTION_KEY is missing from secrets/.env. Please configure it.")

        fernet = Fernet(enc_key.encode())
        whatsapp_enc = fernet.encrypt(whatsapp.strip().encode()).decode()

        conn = psycopg2.connect(db_url)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (name, whatsapp_enc, ripe_chips, unripe_chips, total) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (name.strip(), whatsapp_enc, ripe_chips, unripe_chips, total),
                )
        finally:
            conn.close()
        return total

    # Mode 2: Supabase REST API (via PostgREST)
    elif supabase_url and supabase_key:
        from cryptography.fernet import Fernet

        if not enc_key:
            raise ValueError("ENCRYPTION_KEY is missing from secrets/.env. Please configure it.")

        fernet = Fernet(enc_key.encode())
        whatsapp_enc = fernet.encrypt(whatsapp.strip().encode()).decode()

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        payload = {
            "name": name.strip(),
            "whatsapp_enc": whatsapp_enc,
            "ripe_chips": ripe_chips,
            "unripe_chips": unripe_chips,
            "total": total,
        }
        res = requests.post(
            f"{supabase_url.rstrip('/')}/rest/v1/orders",
            json=payload,
            headers=headers,
            timeout=15,
        )
        if not res.ok:
            raise RuntimeError(f"Supabase REST error: {res.status_code} - {res.text}")
        return total

    # Mode 3: Traditional FastAPI backend (API_URL + API_KEY)
    elif api_url and api_key:
        res = requests.post(
            f"{api_url.rstrip('/')}/submit",
            json={
                "name": name.strip(),
                "whatsapp": whatsapp.strip(),
                "ripe_chips": ripe_chips,
                "unripe_chips": unripe_chips,
            },
            headers={"X-API-Key": api_key},
            timeout=30,
        )
        if not res.ok:
            raise RuntimeError(f"API server error: {res.status_code} - {res.text}")
        data = res.json()
        return data.get("total", total)

    else:
        raise ValueError(
            "No backend configured! Please add DATABASE_URL + ENCRYPTION_KEY to your .env or secrets.toml."
        )


with st.form("order_form", clear_on_submit=False):
    name = st.text_input(
        "Full Name",
        placeholder="e.g. John Doe",
        max_chars=100
    )

    whatsapp = st.text_input(
        "WhatsApp Phone Number (with country code)",
        placeholder="+2348012345678",
        max_chars=20
    )
    st.markdown(
        "<div class='hint-text'>Format: digits only, optional leading '+'. Example: +2348012345678 or 08012345678</div>",
        unsafe_allow_html=True
    )

    st.markdown("#### 📦 Order Quantities")
    col1, col2 = st.columns(2)
    with col1:
        ripe_chips = st.number_input(
            "🟡 Ripe Chips (packs)",
            min_value=0,
            max_value=1000,
            step=1,
            value=0
        )
    with col2:
        unripe_chips = st.number_input(
            "🟢 Unripe Chips (packs)",
            min_value=0,
            max_value=1000,
            step=1,
            value=0
        )

    total_packs = int(ripe_chips + unripe_chips)
    calculated_total = int(total_packs * PRICE_PER_ITEM)

    st.markdown(
        f"<div class='total-badge'>Total: {calculated_total:,} ({total_packs} pack(s) @ {PRICE_PER_ITEM:,} each)</div><br>",
        unsafe_allow_html=True
    )

    submitted = st.form_submit_button("🛒 Submit Order", use_container_width=True)

if submitted:
    cleaned_name = name.strip()
    cleaned_whatsapp = whatsapp.strip()

    # Validation
    if not cleaned_name:
        st.error("❌ Please enter your full name.")
    elif not re.fullmatch(r"^\+?\d{7,15}$", cleaned_whatsapp):
        st.error("❌ Please enter a valid WhatsApp phone number (7 to 15 digits, optional '+' prefix).")
    elif total_packs < 1:
        st.error("❌ Please select at least 1 pack of ripe or unripe chips.")
    else:
        try:
            with st.spinner("Encrypting and saving your order..."):
                final_total = save_to_database(
                    name=cleaned_name,
                    whatsapp=cleaned_whatsapp,
                    ripe_chips=int(ripe_chips),
                    unripe_chips=int(unripe_chips),
                    total=calculated_total
                )
            st.success(
                f"🎉 Thank you, {cleaned_name}! Your order has been placed successfully:\n\n"
                f"- **Ripe Chips:** {ripe_chips} pack(s)\n"
                f"- **Unripe Chips:** {unripe_chips} pack(s)\n"
                f"- **Total Amount:** {final_total:,}"
            )
            st.balloons()
        except Exception as e:
            st.error(f"❌ Failed to submit order: {e}")
            st.info("💡 If you are the administrator, verify your database connection string and encryption key in your secrets.")
