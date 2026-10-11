import os
import io
import csv
import sys
import requests
import psycopg2
from cryptography.fernet import Fernet

# Automatically load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    # Verify environment variables
    required_vars = [
        "DATABASE_URL",
        "ENCRYPTION_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        sys.exit(f"Error: Missing required environment variables: {', '.join(missing)}")

    database_url = os.environ["DATABASE_URL"]
    encryption_key = os.environ["ENCRYPTION_KEY"].strip()
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    chat_id = os.environ["TELEGRAM_CHAT_ID"].strip()

    try:
        fernet = Fernet(encryption_key.encode())
    except Exception as e:
        sys.exit(f"Error: Invalid ENCRYPTION_KEY: {e}")

    # Connect to PostgreSQL (Supabase)
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(database_url)
    except Exception as e:
        sys.exit(f"Database connection error: {e}")

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, whatsapp_enc, ripe_chips, unripe_chips, location, total, created_at "
            "FROM orders ORDER BY location, id"
        )
        rows = cur.fetchall()

        if not rows:
            print("No orders this week.")
            return

        print(f"Fetched {len(rows)} order(s). Building CSV and decrypting numbers...")
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow([
            "id",
            "name",
            "whatsapp",
            "ripe_chips",
            "unripe_chips",
            "total_chips",
            "location",
            "total",
            "created_at",
        ])

        for r in rows:
            # Columns: 0:id, 1:name, 2:whatsapp_enc, 3:ripe_chips, 4:unripe_chips, 5:location, 6:total, 7:created_at
            try:
                decrypted_number = fernet.decrypt(r[2].encode()).decode()
            except Exception as e:
                print(f"Warning: Failed to decrypt row {r[0]}: {e}")
                decrypted_number = "[Decryption Failed]"

            created_str = (
                r[7].strftime("%Y-%m-%d %H:%M")
                if hasattr(r[7], "strftime")
                else str(r[7])
            )
            total_chips = r[3] + r[4]
            w.writerow([r[0], r[1], decrypted_number, r[3], r[4], total_chips, r[5], r[6], created_str])

        total_ripe = sum(r[3] for r in rows)
        total_unripe = sum(r[4] for r in rows)
        grand_total = sum(r[6] for r in rows)

        mainland_count = sum(1 for r in rows if r[5] == "MAINLAND")
        island_count = sum(1 for r in rows if r[5] == "ISLAND")

        csv_bytes = buf.getvalue().encode("utf-8")

        print("Sending CSV to Telegram...")
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        caption = (
            f"📦 Weekly orders report — {len(rows)} order(s)\n"
            f"\n"
            f"🟡 Ripe chips: {total_ripe} pack(s)\n"
            f"🟢 Unripe chips: {total_unripe} pack(s)\n"
            f"📦 Total chips: {total_ripe + total_unripe} pack(s)\n"
            f"💰 Grand total: ₦{grand_total:,}\n"
            f"\n"
            f"📍 Mainland orders: {mainland_count}\n"
            f"🏝️ Island orders: {island_count}"
        )

        resp = requests.post(
            telegram_url,
            data={"chat_id": chat_id, "caption": caption},
            files={"document": ("weekly_orders.csv", csv_bytes)},
            timeout=30,
        )

        # Safety check: STOP before deleting if Telegram failed
        resp.raise_for_status()
        print("Telegram delivered successfully.")

        # Delete only rows that were successfully exported
        row_ids = [r[0] for r in rows]
        cur.execute("DELETE FROM orders WHERE id = ANY(%s)", (row_ids,))
        conn.commit()
        print(f"Sent and cleared {len(rows)} orders.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
