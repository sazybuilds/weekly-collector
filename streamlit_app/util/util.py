import os
import requests
import streamlit as st

# Automatically load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PRICE_PER_ITEM = 2500


class DatabaseError(Exception):
    """Raised when storing an order in the database fails."""
    pass


class TelegramError(Exception):
    """Raised when dispatching a notification to Telegram fails."""
    pass


def get_config_value(name: str, default: str = None) -> str:
    """
    Retrieve configuration value prioritizing Streamlit secrets, then environment variables.
    """
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    val = os.environ.get(name, default)
    return val.strip() if isinstance(val, str) else val


def save_to_database(name: str, whatsapp: str, ripe_chips: int, unripe_chips: int, location: str, total: int) -> int:
    """
    Save regular order to database.
    Raises DatabaseError with a descriptive message if the database operation fails.
    """
    db_url = get_config_value("DATABASE_URL")
    enc_key = get_config_value("ENCRYPTION_KEY")
    supabase_url = get_config_value("SUPABASE_URL")
    supabase_key = get_config_value("SUPABASE_KEY")
    api_url = get_config_value("API_URL")
    api_key = get_config_value("API_KEY")

    try:
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
                "name": name.strip(),
                "whatsapp_enc": whatsapp_enc,
                "ripe_chips": ripe_chips,
                "unripe_chips": unripe_chips,
                "location": location,
                "total": total,
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
                json={
                    "name": name.strip(),
                    "whatsapp": whatsapp.strip(),
                    "ripe_chips": ripe_chips,
                    "unripe_chips": unripe_chips,
                    "location": location,
                },
                headers={"X-API-Key": api_key},
                timeout=30,
            )
            if not res.ok:
                raise RuntimeError(f"API error: {res.status_code} - {res.text}")
            return res.json().get("total", total)

        else:
            raise ValueError("No backend configured. Add DATABASE_URL + ENCRYPTION_KEY to secrets.")

    except Exception as exc:
        raise DatabaseError(f"Data was not stored successfully: {exc}") from exc


def save_special_order_to_database(name: str, whatsapp: str, ripe_chips: int, unripe_chips: int,
                                   location: str, delivery_date, full_instructions: str, total: int) -> int:
    """
    Save special order to database with is_special = TRUE.
    Raises DatabaseError with a descriptive message if the database operation fails.
    """
    db_url = get_config_value("DATABASE_URL")
    enc_key = get_config_value("ENCRYPTION_KEY")
    supabase_url = get_config_value("SUPABASE_URL")
    supabase_key = get_config_value("SUPABASE_KEY")

    try:
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
                "name": name.strip(),
                "whatsapp_enc": whatsapp_enc,
                "ripe_chips": ripe_chips,
                "unripe_chips": unripe_chips,
                "location": location,
                "total": total,
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

    except Exception as exc:
        raise DatabaseError(f"Data was not stored successfully: {exc}") from exc


def send_telegram_notification(name: str, whatsapp: str, ripe_chips: int, unripe_chips: int,
                               location: str, total: int) -> None:
    """
    Send an instant Telegram message to the seller when a regular order is placed.
    Raises TelegramError if credentials are missing or dispatch fails.
    """
    bot_token = get_config_value("TELEGRAM_BOT_TOKEN")
    chat_id = get_config_value("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise TelegramError("Message not sent to seller: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in configuration.")

    loc_icon = "🏙️" if location == "MAINLAND" else "🏝️"
    total_packs = ripe_chips + unripe_chips
    message = (
        f"🛒 *New Order Received!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {name}\n"
        f"📱 *WhatsApp:* `{whatsapp}`\n"
        f"🟡 *Ripe Chips:* {ripe_chips} pack(s)\n"
        f"🟢 *Unripe Chips:* {unripe_chips} pack(s)\n"
        f"📦 *Total Packs:* {total_packs}\n"
        f"{loc_icon} *Location:* {location}\n"
        f"💰 *Total:* ₦{total:,}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    try:
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
            # Fallback to unformatted plain text if Markdown parsing failed
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                },
                timeout=15,
            )
        if not resp.ok:
            raise TelegramError(f"Message not sent to seller: Telegram API returned HTTP {resp.status_code} ({resp.text}).")
    except TelegramError:
        raise
    except Exception as exc:
        raise TelegramError(f"Message not sent to seller: {exc}") from exc


def send_special_order_telegram(name: str, whatsapp: str, ripe_chips: int, unripe_chips: int,
                                location: str, delivery_date, address: str, special_instructions: str,
                                total: int) -> None:
    """
    Send a SPECIAL ORDER notification in CAPS to the seller's Telegram.
    Raises TelegramError if credentials are missing or dispatch fails.
    """
    bot_token = get_config_value("TELEGRAM_BOT_TOKEN")
    chat_id = get_config_value("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise TelegramError("Message not sent to seller: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in configuration.")

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

    try:
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
            # Fallback to unformatted plain text if Markdown parsing failed
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                },
                timeout=15,
            )
        if not resp.ok:
            raise TelegramError(f"Message not sent to seller: Telegram API returned HTTP {resp.status_code} ({resp.text}).")
    except TelegramError:
        raise
    except Exception as exc:
        raise TelegramError(f"Message not sent to seller: {exc}") from exc
