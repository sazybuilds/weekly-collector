import os
import hmac
import psycopg2
from cryptography.fernet import Fernet
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

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


class Order(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    whatsapp: str = Field(pattern=r"^\+?\d{7,15}$")
    ripe_chips: int = Field(default=0, ge=0, le=1000)
    unripe_chips: int = Field(default=0, ge=0, le=1000)


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
    if total_packs < 1:
        raise HTTPException(status_code=422, detail="Must order at least 1 pack of ripe or unripe chips")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: DATABASE_URL is missing."
        )

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
                "INSERT INTO orders (name, whatsapp_enc, ripe_chips, unripe_chips, total) "
                "VALUES (%s, %s, %s, %s, %s)",
                (o.name.strip(), enc, o.ripe_chips, o.unripe_chips, total),
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database insert error: {exc}")
    finally:
        conn.close()

    return {
        "status": "saved",
        "ripe_chips": o.ripe_chips,
        "unripe_chips": o.unripe_chips,
        "total": total
    }
