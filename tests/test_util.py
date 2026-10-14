import os
from unittest.mock import MagicMock, patch
import pytest
from cryptography.fernet import Fernet
from util.util import (
    DatabaseError,
    TelegramError,
    get_config_value,
    save_to_database,
    save_special_order_to_database,
    send_telegram_notification,
    send_special_order_telegram,
    PRICE_PER_ITEM,
)

TEST_ENC_KEY = "dYkyCUTuNn8R6E9UbwmEVaU4NjGlVOrEAvnsR68Zhoo="


def test_get_config_value():
    with patch.dict(os.environ, {"SAMPLE_KEY": "sample_val"}):
        assert get_config_value("SAMPLE_KEY") == "sample_val"
        assert get_config_value("NON_EXISTENT_KEY", "default_val") == "default_val"


@patch("psycopg2.connect")
def test_save_to_database_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://mock", "ENCRYPTION_KEY": TEST_ENC_KEY}):
        total = save_to_database(
            name="Alice",
            whatsapp="+2348011223344",
            ripe_chips=2,
            unripe_chips=1,
            location="MAINLAND",
            total=7500,
        )
        assert total == 7500
        mock_cur.execute.assert_called_once()
        args = mock_cur.execute.call_args[0][1]
        assert args[0] == "Alice"
        assert args[2] == 2
        assert args[3] == 1
        assert args[4] == "MAINLAND"
        assert args[5] == 7500


def test_save_to_database_missing_key_raises_database_error():
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://mock", "ENCRYPTION_KEY": ""}):
        with pytest.raises(DatabaseError, match="Data was not stored successfully"):
            save_to_database("Alice", "+2348011223344", 1, 0, "ISLAND", 2500)


@patch("psycopg2.connect")
def test_save_special_order_to_database_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://mock", "ENCRYPTION_KEY": TEST_ENC_KEY}):
        total = save_special_order_to_database(
            name="Bob",
            whatsapp="+2348055667788",
            ripe_chips=10,
            unripe_chips=10,
            location="ISLAND",
            delivery_date="2026-10-25",
            full_instructions="Custom spicy mix",
            total=50000,
        )
        assert total == 50000
        mock_cur.execute.assert_called_once()
        args = mock_cur.execute.call_args[0][1]
        assert args[0] == "Bob"
        assert args[6] == "2026-10-25"
        assert args[7] == "Custom spicy mix"
        assert args[8] is True


def test_send_telegram_missing_credentials_raises_telegram_error():
    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
        with pytest.raises(TelegramError, match="Message not sent to seller"):
            send_telegram_notification("Alice", "+2348011223344", 1, 1, "MAINLAND", 5000)

        with pytest.raises(TelegramError, match="Message not sent to seller"):
            send_special_order_telegram("Alice", "+2348011223344", 1, 1, "MAINLAND", "2026-10-25", "", "Special details", 5000)


@patch("requests.post")
def test_send_telegram_api_failure_raises_telegram_error(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "token123", "TELEGRAM_CHAT_ID": "chat456"}):
        with pytest.raises(TelegramError, match="Message not sent to seller"):
            send_telegram_notification("Alice", "+2348011223344", 2, 0, "MAINLAND", 5000)


@patch("requests.post")
def test_send_telegram_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "token123", "TELEGRAM_CHAT_ID": "chat456"}):
        # Regular notification
        send_telegram_notification("Alice", "+2348011223344", 2, 1, "MAINLAND", 7500)
        assert mock_post.called

        # Special order notification
        mock_post.reset_mock()
        send_special_order_telegram(
            name="Bob",
            whatsapp="+2348055667788",
            ripe_chips=5,
            unripe_chips=5,
            location="ISLAND",
            delivery_date="2026-10-30",
            address="12 Lekki Road",
            special_instructions="Spicy tags",
            total=25000,
        )
        assert mock_post.called
        called_json = mock_post.call_args[1]["json"]
        assert "SPECIAL ORDER" in called_json["text"]
        assert "Bob" in called_json["text"]
