import os
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from cryptography.fernet import Fernet
import requests
from scripts.send_weekly import main as send_weekly_main

TEST_ENC_KEY = "dYkyCUTuNn8R6E9UbwmEVaU4NjGlVOrEAvnsR68Zhoo="

@patch("psycopg2.connect")
@patch("requests.post")
def test_send_weekly_no_orders(mock_post, mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = []  # No orders

    env_vars = {
        "DATABASE_URL": "postgresql://mock",
        "ENCRYPTION_KEY": TEST_ENC_KEY,
        "TELEGRAM_BOT_TOKEN": "mock-token",
        "TELEGRAM_CHAT_ID": "123456789",
    }

    with patch.dict(os.environ, env_vars):
        send_weekly_main()
        # Telegram must NOT be called if there are no orders
        assert not mock_post.called
        # Delete must NOT be called
        assert not any("DELETE" in str(c) for c in mock_cur.execute.call_args_list)


@patch("psycopg2.connect")
@patch("requests.post")
def test_send_weekly_success(mock_post, mock_connect):
    fernet = Fernet(TEST_ENC_KEY.encode())
    enc_phone = fernet.encrypt(b"+2348012345678").decode()

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # Mock order row: id, name, whatsapp_enc, ripe_chips, unripe_chips, location, total, created_at, is_special, delivery_date, special_instructions
    mock_cur.fetchall.return_value = [
        (1, "John Doe", enc_phone, 2, 3, "MAINLAND", 12500, datetime(2026, 10, 4, 12, 0), False, "", "")
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    env_vars = {
        "DATABASE_URL": "postgresql://mock",
        "ENCRYPTION_KEY": TEST_ENC_KEY,
        "TELEGRAM_BOT_TOKEN": "123456:AAAToken",
        "TELEGRAM_CHAT_ID": "987654321",
    }

    with patch.dict(os.environ, env_vars):
        send_weekly_main()

        # Check Telegram was called
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["chat_id"] == "987654321"
        assert "Weekly orders report" in kwargs["data"]["caption"]
        assert "1 order(s)" in kwargs["data"]["caption"]
        assert "12,500" in kwargs["data"]["caption"]

        # Check CSV content sent
        csv_file_tuple = kwargs["files"]["document"]
        assert csv_file_tuple[0] == "weekly_orders.csv"
        csv_content = csv_file_tuple[1].decode("utf-8")
        assert "+2348012345678" in csv_content
        assert "John Doe" in csv_content
        assert "MAINLAND" in csv_content

        # Check DELETE was executed after success
        delete_calls = [c for c in mock_cur.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) == 1
        assert mock_conn.commit.called


@patch("psycopg2.connect")
@patch("requests.post")
def test_send_weekly_telegram_failure_does_not_delete(mock_post, mock_connect):
    fernet = Fernet(TEST_ENC_KEY.encode())
    enc_phone = fernet.encrypt(b"+2348012345678").decode()

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    mock_cur.fetchall.return_value = [
        (1, "John Doe", enc_phone, 2, 3, "MAINLAND", 12500, datetime(2026, 10, 4, 12, 0), False, "", "")
    ]

    # Simulate Telegram network error
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("Telegram API 500 error")
    mock_post.return_value = mock_resp

    env_vars = {
        "DATABASE_URL": "postgresql://mock",
        "ENCRYPTION_KEY": TEST_ENC_KEY,
        "TELEGRAM_BOT_TOKEN": "123456:AAAToken",
        "TELEGRAM_CHAT_ID": "987654321",
    }

    with patch.dict(os.environ, env_vars):
        with pytest.raises(requests.HTTPError):
            send_weekly_main()

        # Crucial safety assertion: DELETE must NEVER be called if Telegram failed!
        delete_calls = [c for c in mock_cur.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) == 0
