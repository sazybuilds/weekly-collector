"""
FINAL BOSS END-TO-END TEST SUITE
================================
Simulates the entire customer journey and system lifecycle:
1. User orders via Streamlit UI (Regular Order) -> Fernet encryption -> Database insert -> Instant Telegram alert.
2. User orders via Streamlit UI (Special Bespoke Order) -> Encryption -> Database insert (is_special=True) -> Instant Telegram alert with CAPS.
3. Automated Weekly Batch Exporter (scripts/send_weekly.py) -> Reads DB -> Decrypts numbers -> Generates CSV -> Dispatches to Telegram -> Cleans DB table.
4. Error Handling & Resilience (DB failure vs Telegram failure).
"""

import os
import re
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from cryptography.fernet import Fernet
from pathlib import Path
from streamlit.testing.v1 import AppTest

from util.util import (
    DatabaseError,
    TelegramError,
    save_to_database,
    save_special_order_to_database,
    send_telegram_notification,
    send_special_order_telegram,
    PRICE_PER_ITEM,
)
from scripts.send_weekly import main as send_weekly_main

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT_DIR / "streamlit_app" / "app.py")
SPECIAL_ORDERS_PATH = str(ROOT_DIR / "streamlit_app" / "pages" / "special_orders.py")

TEST_ENC_KEY = "dYkyCUTuNn8R6E9UbwmEVaU4NjGlVOrEAvnsR68Zhoo="
TEST_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TEST_CHAT_ID = "987654321"


@pytest.fixture(autouse=True)
def boss_environment():
    """Sets standard environment secrets for all tests in the final boss suite."""
    env = {
        "DATABASE_URL": "postgresql://postgres:secret@aws-0-eu-west-1.pooler.supabase.com:6543/postgres",
        "ENCRYPTION_KEY": TEST_ENC_KEY,
        "TELEGRAM_BOT_TOKEN": TEST_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TEST_CHAT_ID,
    }
    with patch.dict(os.environ, env):
        yield env


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1: REGULAR ORDER UI -> ENCRYPT -> DATABASE -> INSTANT TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────
class TestFinalBossStage1RegularOrder:
    @patch("psycopg2.connect")
    @patch("requests.post")
    def test_full_regular_order_lifecycle(self, mock_requests_post, mock_psycopg2_connect):
        """Simulate real user placing a regular order through Streamlit UI."""
        # 1. Mock Database
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # 2. Mock Telegram API response
        mock_tg_resp = MagicMock()
        mock_tg_resp.ok = True
        mock_tg_resp.status_code = 200
        mock_requests_post.return_value = mock_tg_resp

        # 3. Simulate Streamlit App execution
        at = AppTest.from_file(APP_PATH, default_timeout=25)
        at.run()
        assert not at.exception

        # Customer fills the Regular Order Form:
        customer_name = "Amaka Okonkwo"
        customer_phone = "+2348012345678"
        at.text_input[0].input(customer_name)
        at.text_input[1].input(customer_phone)
        at.number_input[0].set_value(4)  # 4 ripe packs
        at.number_input[1].set_value(2)  # 2 unripe packs

        # Submit form
        at.button[0].click().run()
        assert not at.exception

        # 4. Verify Database Insertion & Encryption
        assert mock_cur.execute.called
        query, params = mock_cur.execute.call_args[0]
        assert "INSERT INTO orders" in query
        assert params[0] == customer_name
        whatsapp_enc = params[1]
        assert whatsapp_enc != customer_phone  # NOT stored as plain text
        assert whatsapp_enc.startswith("gAAAAA")  # Valid Fernet token format
        assert params[2] == 4  # ripe
        assert params[3] == 2  # unripe
        assert params[4] == "MAINLAND"  # default location
        expected_total = 6 * PRICE_PER_ITEM
        assert params[5] == expected_total  # 15,000

        # Cryptographically decrypt in the test to ensure integrity
        fernet = Fernet(TEST_ENC_KEY.encode())
        decrypted_phone = fernet.decrypt(whatsapp_enc.encode()).decode()
        assert decrypted_phone == customer_phone

        # 5. Verify Telegram Instant Dispatch
        assert mock_requests_post.called
        tg_call_args = mock_requests_post.call_args
        tg_url = tg_call_args[0][0]
        assert tg_url == f"https://api.telegram.org/bot{TEST_BOT_TOKEN}/sendMessage"
        payload = tg_call_args[1]["json"]
        assert payload["chat_id"] == TEST_CHAT_ID
        assert "🛒 *New Order Received!*" in payload["text"]
        assert customer_name in payload["text"]
        assert customer_phone in payload["text"]
        assert "4 pack(s)" in payload["text"]
        assert "2 pack(s)" in payload["text"]
        assert "₦15,000" in payload["text"]
        assert "MAINLAND" in payload["text"]

        # 6. Verify UI success presentation
        assert len(at.success) >= 1
        assert "Order placed" in at.success[0].value
        assert customer_name in at.success[0].value


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: SPECIAL BESPOKE ORDER UI -> ENCRYPT -> DATABASE -> INSTANT TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────
class TestFinalBossStage2SpecialOrder:
    @patch("psycopg2.connect")
    @patch("requests.post")
    def test_full_special_order_lifecycle(self, mock_requests_post, mock_psycopg2_connect):
        """Simulate real user requesting a custom catering/special order."""
        # 1. Mock DB and Telegram
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_tg_resp = MagicMock()
        mock_tg_resp.ok = True
        mock_tg_resp.status_code = 200
        mock_requests_post.return_value = mock_tg_resp

        # 2. Simulate Streamlit Special Orders page
        at = AppTest.from_file(SPECIAL_ORDERS_PATH, default_timeout=25)
        at.run()
        assert not at.exception

        sp_name = "Chinedu Eke"
        sp_phone = "+2348099887766"
        sp_address = "Plot 14 Admiralty Way, Lekki Phase 1"
        sp_instructions = "Wedding reception catering: 30 sweet ripe + 20 extra spicy unripe packs with gold ribbons."
        target_delivery = date.today() + timedelta(days=10)

        at.text_input[0].input(sp_name)
        at.text_input[1].input(sp_phone)
        at.radio[0].set_value("🏝️  ISLAND")
        at.date_input[0].set_value(target_delivery)
        at.text_input[2].input(sp_address)
        at.text_area[0].input(sp_instructions)
        at.number_input[0].set_value(30)
        at.number_input[1].set_value(20)

        # Submit special order
        at.button[0].click().run()
        assert not at.exception

        # 3. Verify Database Insertion for Special Order
        assert mock_cur.execute.called
        query, params = mock_cur.execute.call_args[0]
        assert "INSERT INTO orders" in query
        assert "delivery_date" in query
        assert "special_instructions" in query
        assert "is_special" in query
        assert params[0] == sp_name

        # Phone encryption
        sp_enc_phone = params[1]
        fernet = Fernet(TEST_ENC_KEY.encode())
        assert fernet.decrypt(sp_enc_phone.encode()).decode() == sp_phone

        assert params[2] == 30  # ripe
        assert params[3] == 20  # unripe
        assert params[4] == "ISLAND"  # chosen location
        assert params[5] == 50 * PRICE_PER_ITEM  # 125,000
        assert params[6] == str(target_delivery)
        assert sp_address in params[7]
        assert sp_instructions in params[7]
        assert params[8] is True  # is_special MUST be True

        # 4. Verify Telegram High-Priority Alert
        assert mock_requests_post.called
        payload = mock_requests_post.call_args[1]["json"]
        assert payload["chat_id"] == TEST_CHAT_ID
        assert "🚨🚨🚨 *SPECIAL ORDER* 🚨🚨🚨" in payload["text"]
        assert sp_name in payload["text"]
        assert sp_phone in payload["text"]
        assert "ISLAND" in payload["text"]
        assert sp_address in payload["text"]
        assert str(target_delivery) in payload["text"]
        assert "30" in payload["text"]
        assert "20" in payload["text"]
        assert "Wedding reception catering" in payload["text"]

        # 5. Verify UI success confirmation
        assert len(at.success) >= 1
        assert "Special Order Received" in at.success[0].value
        assert sp_name in at.success[0].value


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: WEEKLY ACCUMULATION & FULL EXPORT/CLEANUP (scripts/send_weekly.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestFinalBossStage3WeeklyExport:
    @patch("psycopg2.connect")
    @patch("requests.post")
    def test_weekly_report_full_export_and_cleanup(self, mock_requests_post, mock_psycopg2_connect):
        """Simulate Wednesday 5 PM automated job exporting decrypted CSV and cleaning table."""
        fernet = Fernet(TEST_ENC_KEY.encode())
        enc1 = fernet.encrypt(b"+2348011112222").decode()
        enc2 = fernet.encrypt(b"+2348033334444").decode()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        # Simulate 2 accumulated orders in DB: 1 regular + 1 special order
        mock_cur.fetchall.return_value = [
            (
                101,
                "Regular Buyer",
                enc1,
                3,
                1,
                "MAINLAND",
                10000,
                datetime(2026, 10, 10, 14, 0),
                False,
                "",
                "",
            ),
            (
                102,
                "Special Event Buyer",
                enc2,
                20,
                20,
                "ISLAND",
                100000,
                datetime(2026, 10, 12, 16, 30),
                True,
                "2026-10-25",
                "Spicy wedding batches",
            ),
        ]

        mock_tg_resp = MagicMock()
        mock_tg_resp.ok = True
        mock_tg_resp.status_code = 200
        mock_requests_post.return_value = mock_tg_resp

        # Run the weekly batch exporter
        send_weekly_main()

        # 1. Telegram sendDocument was invoked
        assert mock_requests_post.called
        kwargs = mock_requests_post.call_args[1]
        assert kwargs["data"]["chat_id"] == TEST_CHAT_ID
        assert "Weekly orders report — 2 order(s)" in kwargs["data"]["caption"]
        assert "Grand total: ₦110,000" in kwargs["data"]["caption"]
        assert "Mainland orders: 1" in kwargs["data"]["caption"]
        assert "Island orders: 1" in kwargs["data"]["caption"]

        # 2. CSV Content properly decrypted
        csv_filename, csv_bytes = kwargs["files"]["document"]
        assert csv_filename == "weekly_orders.csv"
        csv_str = csv_bytes.decode("utf-8")

        # Plain phone numbers must be restored for seller delivery
        assert "+2348011112222" in csv_str
        assert "+2348033334444" in csv_str
        assert "Regular Buyer" in csv_str
        assert "Special Event Buyer" in csv_str
        assert "Spicy wedding batches" in csv_str

        # 3. Database rows cleared only after success
        delete_calls = [c for c in mock_cur.execute.call_args_list if "DELETE FROM orders" in str(c)]
        assert len(delete_calls) == 1
        assert mock_conn.commit.called


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4: FAULT TOLERANCE & ATOMICITY (Partials and Failures)
# ─────────────────────────────────────────────────────────────────────────────
class TestFinalBossStage4FaultTolerance:
    @patch("psycopg2.connect")
    @patch("requests.post")
    def test_database_failure_never_calls_telegram(self, mock_requests_post, mock_psycopg2_connect):
        """When DB fails, Telegram must NEVER be notified and DatabaseError is raised."""
        mock_psycopg2_connect.side_effect = Exception("DB Connection refused: connection pool exhausted")

        with pytest.raises(DatabaseError, match="Data was not stored successfully"):
            save_to_database("Alice", "+2348011223344", 2, 1, "MAINLAND", 7500)

        # Telegram was completely spared
        assert not mock_requests_post.called

    @patch("requests.post")
    def test_telegram_failure_raises_telegram_error(self, mock_requests_post):
        """When Telegram fails, TelegramError is raised with distinct message."""
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 502
        mock_resp.text = "Bad Gateway"
        mock_requests_post.return_value = mock_resp

        with pytest.raises(TelegramError, match="Message not sent to seller"):
            send_telegram_notification("Alice", "+2348011223344", 2, 1, "MAINLAND", 7500)

    @patch("psycopg2.connect")
    @patch("requests.post")
    def test_weekly_export_telegram_failure_does_not_clear_db(self, mock_requests_post, mock_psycopg2_connect):
        """If weekly Telegram fails, never delete orders from the database."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        fernet = Fernet(TEST_ENC_KEY.encode())
        mock_cur.fetchall.return_value = [
            (1, "John", fernet.encrypt(b"+2348012345678").decode(), 2, 2, "MAINLAND", 10000, datetime.now(), False, "", "")
        ]

        # Telegram failure
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.raise_for_status.side_effect = Exception("HTTP 500 Telegram Down")
        mock_requests_post.return_value = mock_resp

        with pytest.raises(Exception, match="Telegram Down"):
            send_weekly_main()

        # Database rows must NOT be deleted
        delete_calls = [c for c in mock_cur.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) == 0
