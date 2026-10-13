import os
import hmac
import psycopg2
import requests
from typing import Optional
from cryptography.fernet import Fernet #whatsapp number encryption
from fastapi import FastAPI, Header, HTTPException #api
from pydantic import BaseModel, Field #input validation

try:
    from dotenv import load_dotenv, find_dotenv #load environment variables
    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

PRICE_PER_ITEM = 2500  # price per pack

app = FastAPI(title="Order Collector API")


def get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: ENCRYPTION_KEY is missing."
        )
    try:
        return Fernet(key.strip().encode())
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Server misconfiguration: Invalid ENCRYPTION_KEY: {exc}"
        )


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """Send message to Telegram with automatic fallback to unformatted text on parse error."""
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
        if resp.ok:
            return True
        # If Markdown entity parsing fails due to user input symbols, retry as plain text
        fallback_resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
            },
            timeout=15,
        )
        return fallback_resp.ok
    except Exception:
        return False


def notify_telegram(
    is_special: bool,
    name: str,
    whatsapp: str,
    ripe_chips: int,
    unripe_chips: int,
    location: str,
    total: int,
    delivery_date: Optional[str] = None,
    address: Optional[str] = None,
    special_instructions: Optional[str] = None,
) -> bool:
    """Send immediate notification to seller via Telegram bot for normal or special order."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return False

    loc_icon = "🏙️" if location == "MAINLAND" else "🏝️"
    total_packs = ripe_chips + unripe_chips

    if is_special:
        address_line = f"🏢 *Address / Landmark:* {address}\n" if address else ""
        price_line = (
            f"💰 *Estimated Total:* ₦{total:,}\n"
            if total > 0
            else "💰 *Quote:* Custom Quote (Pending Seller Review)\n"
        )
        instr = special_instructions.strip() if special_instructions else "No details provided."
        msg = (
            f"🚨🚨🚨 *SPECIAL ORDER* 🚨🚨🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Customer:* {name}\n"
            f"📱 *WhatsApp:* `{whatsapp}`\n"
            f"{loc_icon} *Area:* {location}\n"
            f"{address_line}"
            f"📅 *Expected Delivery:* {delivery_date or 'Flexible'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟡 *Ripe Packs (Est.):* {ripe_chips}\n"
            f"🟢 *Unripe Packs (Est.):* {unripe_chips}\n"
            f"📦 *Total Est. Packs:* {total_packs}\n"
            f"{price_line}"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *SPECIAL ORDER SPECIFICS:*\n"
            f"{instr}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        msg = (
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

    return send_telegram_message(bot_token.strip(), chat_id.strip(), msg)


class Order(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    whatsapp: str = Field(pattern=r"^\+?\d{7,15}$")
    ripe_chips: int = Field(default=0, ge=0, le=1000)
    unripe_chips: int = Field(default=0, ge=0, le=1000)
    location: str = Field(default="MAINLAND")
    is_special: bool = Field(default=False)
    delivery_date: Optional[str] = None
    special_instructions: Optional[str] = None
    address: Optional[str] = None
    custom_total: Optional[int] = None


@app.get("/")
def health():
    return {"ok": True}


@app.post("/submit")
def submit(o: Order, x_api_key: str = Header("")):
    expected = os.environ.get("API_KEY")
    if not expected:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: API_KEY is missing."
        )

    if not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not o.name.strip():
        raise HTTPException(status_code=422, detail="Name required")

    total_packs = o.ripe_chips + o.unripe_chips

    if not o.is_special:
        if total_packs < 1:
            raise HTTPException(
                status_code=422, detail="Must order at least 1 pack of ripe or unripe chips"
            )
    else:
        if not (o.special_instructions and o.special_instructions.strip()):
            raise HTTPException(
                status_code=422, detail="Special instructions required for special orders"
            )

    loc = (o.location or "MAINLAND").strip().upper()
    if loc not in ("MAINLAND", "ISLAND"):
        loc = "MAINLAND"

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: DATABASE_URL is missing."
        )

    if o.custom_total is not None and o.custom_total >= 0:
        total = o.custom_total
    else:
        total = total_packs * PRICE_PER_ITEM

    fernet = get_fernet()
    enc = fernet.encrypt(o.whatsapp.strip().encode()).decode()

    try:
        conn = psycopg2.connect(db_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database connection error: {exc}")

    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO orders (name, whatsapp_enc, ripe_chips, unripe_chips, total, location, delivery_date, special_instructions, is_special) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    o.name.strip(),
                    enc,
                    o.ripe_chips,
                    o.unripe_chips,
                    total,
                    loc,
                    o.delivery_date,
                    o.special_instructions.strip() if o.special_instructions else None,
                    o.is_special,
                ),
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database insert error: {exc}")
    finally:
        conn.close()

    # Dispatch to Telegram bot
    full_special_instructions = o.special_instructions
    if o.is_special and o.address and o.special_instructions:
        if "delivery address:" not in o.special_instructions.lower():
            full_special_instructions = f"Delivery Address: {o.address.strip()}\n\n{o.special_instructions.strip()}"

    telegram_sent = notify_telegram(
        is_special=o.is_special,
        name=o.name.strip(),
        whatsapp=o.whatsapp.strip(),
        ripe_chips=o.ripe_chips,
        unripe_chips=o.unripe_chips,
        location=loc,
        total=total,
        delivery_date=o.delivery_date,
        address=o.address,
        special_instructions=full_special_instructions,
    )

    return {
        "status": "saved",
        "ripe_chips": o.ripe_chips,
        "unripe_chips": o.unripe_chips,
        "location": loc,
        "total": total,
        "is_special": o.is_special,
        "telegram_sent": telegram_sent,
    }


@app.post("/submit-special")
def submit_special(o: Order, x_api_key: str = Header("")):
    """Convenience endpoint dedicated for special orders."""
    o.is_special = True
    return submit(o, x_api_key=x_api_key)
