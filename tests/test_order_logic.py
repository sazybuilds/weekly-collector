import re
import pytest

PHONE_PATTERN = r"^\+?\d{7,15}$"
PRICE_PER_ITEM = 2500

def validate_order(name: str, whatsapp: str, ripe_chips: int, unripe_chips: int):
    cleaned_name = name.strip() if name else ""
    cleaned_whatsapp = whatsapp.strip() if whatsapp else ""

    if not cleaned_name:
        raise ValueError("Name required")

    if not re.fullmatch(PHONE_PATTERN, cleaned_whatsapp):
        raise ValueError("Invalid WhatsApp number")

    if ripe_chips < 0 or unripe_chips < 0:
        raise ValueError("Quantities cannot be negative")

    total_packs = ripe_chips + unripe_chips
    if total_packs < 1:
        raise ValueError("Must order at least 1 pack")

    total_price = total_packs * PRICE_PER_ITEM
    return {
        "name": cleaned_name,
        "whatsapp": cleaned_whatsapp,
        "ripe_chips": ripe_chips,
        "unripe_chips": unripe_chips,
        "total_packs": total_packs,
        "total_price": total_price,
    }


def test_valid_phone_numbers():
    valid_phones = [
        "+2348012345678",
        "08012345678",
        "+1234567",
        "+123456789012345",
        "2348099887766",
    ]
    for phone in valid_phones:
        assert re.fullmatch(PHONE_PATTERN, phone) is not None


def test_invalid_phone_numbers():
    invalid_phones = [
        "",
        "   ",
        "abc12345678",
        "+234 801 234 5678",  # spaces
        "+234-801-234-5678", # dashes
        "123456",            # too short (6 digits)
        "+1234567890123456", # too long (16 digits)
        "++2348012345678",
    ]
    for phone in invalid_phones:
        assert re.fullmatch(PHONE_PATTERN, phone.strip()) is None


def test_order_price_calculation():
    # 2 ripe + 3 unripe = 5 packs * 2500 = 12500
    res = validate_order("John Doe", "+2348012345678", 2, 3)
    assert res["total_packs"] == 5
    assert res["total_price"] == 12500

    # 1 ripe + 0 unripe = 1 pack * 2500 = 2500
    res2 = validate_order("Jane Doe", "08012345678", 1, 0)
    assert res2["total_packs"] == 1
    assert res2["total_price"] == 2500


def test_order_zero_packs_fails():
    with pytest.raises(ValueError, match="Must order at least 1 pack"):
        validate_order("John Doe", "+2348012345678", 0, 0)


def test_order_negative_packs_fails():
    with pytest.raises(ValueError, match="Quantities cannot be negative"):
        validate_order("John Doe", "+2348012345678", -1, 2)


def test_order_empty_name_fails():
    with pytest.raises(ValueError, match="Name required"):
        validate_order("   ", "+2348012345678", 1, 1)
