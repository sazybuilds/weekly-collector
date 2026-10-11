import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
TEST_API_KEY = "test-secret-api-key"
TEST_ENC_KEY = "dYkyCUTuNn8R6E9UbwmEVaU4NjGlVOrEAvnsR68Zhoo="

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_submit_unauthorized_key():
    with patch.dict(os.environ, {"API_KEY": TEST_API_KEY, "ENCRYPTION_KEY": TEST_ENC_KEY, "DATABASE_URL": "mock"}):
        response = client.post(
            "/submit",
            json={"name": "Test User", "whatsapp": "+2348012345678", "ripe_chips": 2, "unripe_chips": 1},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"


def test_submit_invalid_phone():
    with patch.dict(os.environ, {"API_KEY": TEST_API_KEY, "ENCRYPTION_KEY": TEST_ENC_KEY, "DATABASE_URL": "mock"}):
        response = client.post(
            "/submit",
            json={"name": "Test User", "whatsapp": "invalid_phone", "ripe_chips": 2, "unripe_chips": 1},
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 422


def test_submit_zero_items():
    with patch.dict(os.environ, {"API_KEY": TEST_API_KEY, "ENCRYPTION_KEY": TEST_ENC_KEY, "DATABASE_URL": "mock"}):
        response = client.post(
            "/submit",
            json={"name": "Test User", "whatsapp": "+2348012345678", "ripe_chips": 0, "unripe_chips": 0},
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 422
        assert "at least 1 pack" in response.json()["detail"].lower()


@patch("psycopg2.connect")
def test_submit_success(mock_connect):
    # Mock psycopg2 connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    env_vars = {
        "API_KEY": TEST_API_KEY,
        "ENCRYPTION_KEY": TEST_ENC_KEY,
        "DATABASE_URL": "postgresql://mock:mock@localhost:5432/mock"
    }

    with patch.dict(os.environ, env_vars):
        payload = {
            "name": "Adeola Davies",
            "whatsapp": "+2348012345678",
            "ripe_chips": 3,
            "unripe_chips": 2
        }
        response = client.post(
            "/submit",
            json=payload,
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["ripe_chips"] == 3
        assert data["unripe_chips"] == 2
        # (3 + 2) * 2500 = 12500
        assert data["total"] == 12500

        # Verify SQL execute was called
        assert mock_cursor.execute.called
        query, params = mock_cursor.execute.call_args[0]
        assert "INSERT INTO orders" in query
        assert params[0] == "Adeola Davies"
        assert params[1].startswith("gAAAA")  # encrypted whatsapp
        assert params[2] == 3
        assert params[3] == 2
        assert params[4] == 12500
