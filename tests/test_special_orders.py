import re
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
from cryptography.fernet import Fernet
import requests

PHONE_PATTERN = r"^\+?\d{7,15}$"
TEST_ENC_KEY = "dYkyCUTuNn8R6E9UbwmEVaU4NjGlVOrEAvnsR68Zhoo="


def validate_special_order(name: str, whatsapp: str, special_instructions: str, delivery_date: date):
    cleaned_name = name.strip() if name else ""
    cleaned_whatsapp = whatsapp.strip() if whatsapp else ""
    cleaned_instructions = special_instructions.strip() if special_instructions else ""

    if not cleaned_name:
        raise ValueError("Name required")

    if not re.fullmatch(PHONE_PATTERN, cleaned_whatsapp):
        raise ValueError("Invalid WhatsApp number")

    if not cleaned_instructions:
        raise ValueError("Special instructions required")

    if delivery_date < date.today():
        raise ValueError("Delivery date cannot be in the past")

    return {
        "name": cleaned_name,
        "whatsapp": cleaned_whatsapp,
        "special_instructions": cleaned_instructions,
        "delivery_date": str(delivery_date),
    }


def format_special_order_telegram_message(
    name: str,
    whatsapp: str,
    location: str,
    delivery_date: str,
    special_instructions: str,
    ripe_chips: int = 0,
    unripe_chips: int = 0,
    total: int = 0,
) -> str:
    loc_icon = "🏙️" if location == "MAINLAND" else "🏝️"
    total_packs = ripe_chips + unripe_chips
    message = (
        f"🚨🚨🚨 *SPECIAL ORDER* 🚨🚨🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {name}\n"
        f"📱 *WhatsApp:* `{whatsapp}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟡 *Ripe Chips:* {ripe_chips} pack(s)\n"
        f"🟢 *Unripe Chips:* {unripe_chips} pack(s)\n"
        f"📦 *Total Packs:* {total_packs}\n"
        f"{loc_icon} *Location:* {location}\n"
        f"📅 *Expected Delivery:* {delivery_date}\n"
        f"💰 *Estimated Total:* ₦{total:,}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Special Instructions:*\n"
        f"{special_instructions}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    return message


# ── Test Suite ────────────────────────────────────────────────────────────────

def test_validate_special_order_success():
    tomorrow = date.today() + timedelta(days=1)
    res = validate_special_order(
        name="Chioma Adeleke",
        whatsapp="+2348099887766",
        special_instructions="50 packs for wedding event. Extra sweet ripe chips with custom tags.",
        delivery_date=tomorrow,
    )
    assert res["name"] == "Chioma Adeleke"
    assert res["whatsapp"] == "+2348099887766"
    assert "wedding event" in res["special_instructions"]
    assert res["delivery_date"] == str(tomorrow)


def test_validate_special_order_missing_name():
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValueError, match="Name required"):
        validate_special_order(
            name="   ",
            whatsapp="+2348099887766",
            special_instructions="Need 20 packs spicy unripe chips",
            delivery_date=tomorrow,
        )


def test_validate_special_order_invalid_whatsapp():
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValueError, match="Invalid WhatsApp number"):
        validate_special_order(
            name="Tunde Bakare",
            whatsapp="080-invalid-num",
            special_instructions="Need 20 packs spicy unripe chips",
            delivery_date=tomorrow,
        )


def test_validate_special_order_empty_instructions():
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValueError, match="Special instructions required"):
        validate_special_order(
            name="Tunde Bakare",
            whatsapp="+2348012345678",
            special_instructions="   ",
            delivery_date=tomorrow,
        )


def test_validate_special_order_past_date():
    yesterday = date.today() - timedelta(days=1)
    with pytest.raises(ValueError, match="Delivery date cannot be in the past"):
        validate_special_order(
            name="Tunde Bakare",
            whatsapp="+2348012345678",
            special_instructions="Need 20 packs spicy unripe chips",
            delivery_date=yesterday,
        )


def test_telegram_special_order_message_formatting():
    msg = format_special_order_telegram_message(
        name="Amaka Obi",
        whatsapp="+2348011223344",
        location="ISLAND",
        delivery_date="2026-10-25",
        special_instructions="Custom spicy batch, 30 packs",
        ripe_chips=15,
        unripe_chips=15,
        total=75000,
    )

    # Must contain "SPECIAL ORDER" in CAPS as required
    assert "SPECIAL ORDER" in msg
    assert "Amaka Obi" in msg
    assert "+2348011223344" in msg
    assert "ISLAND" in msg
    assert "2026-10-25" in msg
    assert "Custom spicy batch, 30 packs" in msg
    assert "75,000" in msg


@patch("requests.post")
def test_send_special_order_telegram_call(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    bot_token = "123456:FAKE_TOKEN"
    chat_id = "987654321"
    msg = format_special_order_telegram_message(
        name="Bolanle",
        whatsapp="+2348055667788",
        location="MAINLAND",
        delivery_date="2026-10-20",
        special_instructions="Catering for office event",
    )

    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
        timeout=15,
    )
    assert resp.status_code == 200
    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["chat_id"] == "987654321"
    assert "SPECIAL ORDER" in payload["text"]
    assert "Bolanle" in payload["text"]
