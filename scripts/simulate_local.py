"""
Local Simulation Script
-----------------------
Simulates the entire end-to-end flow locally:
1. Creates a local SQLite database mimicking the Supabase schema.
2. Simulates placing 3 orders with real Fernet phone number encryption.
3. Displays the raw encrypted rows in the database (demonstrating security).
4. Runs the weekly report generator:
   - Decrypts WhatsApp numbers
   - Writes a real CSV report to disk (simulated_orders.csv)
   - Simulates the Telegram message and summary
   - Clears the database
"""

import os
import sys
import sqlite3
import csv
from datetime import datetime
from cryptography.fernet import Fernet

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PRICE_PER_ITEM = 2500

def main():
    print("=" * 65)
    print("[*] WEEKLY ORDER COLLECTOR: LOCAL END-TO-END SIMULATION")
    print("=" * 65)

    # 1. Get or generate encryption key
    enc_key = os.environ.get("ENCRYPTION_KEY")
    if not enc_key or len(enc_key.strip()) != 44:
        print("[!] Generating temporary Fernet encryption key for simulation...")
        enc_key = Fernet.generate_key().decode()

    fernet = Fernet(enc_key.strip().encode())
    print(f"[*] Fernet ENCRYPTION_KEY: {enc_key.strip()}")

    # 2. Setup SQLite DB mimicking Supabase PostgreSQL
    db_path = "simulated_orders.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            whatsapp_enc TEXT NOT NULL,
            ripe_chips INTEGER NOT NULL DEFAULT 0,
            unripe_chips INTEGER NOT NULL DEFAULT 0,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    print("[*] Local database initialized.")

    # 3. Simulate customer orders
    sample_orders = [
        ("Amaka Eze", "+2348011223344", 2, 3),
        ("Tunde Bakare", "+2348055667788", 4, 0),
        ("Fatima Bello", "+2348099887766", 0, 5),
    ]

    print("\n--- [Phase 1: Customer Order Submissions] ---")
    for name, phone, ripe, unripe in sample_orders:
        total_packs = ripe + unripe
        total_price = total_packs * PRICE_PER_ITEM
        encrypted_phone = fernet.encrypt(phone.encode()).decode()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO orders (name, whatsapp_enc, ripe_chips, unripe_chips, total, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, encrypted_phone, ripe, unripe, total_price, now_str)
        )
        print(f" -> Order received from {name}: {ripe} ripe, {unripe} unripe (Total: {total_price:,})")

    conn.commit()

    # 4. Inspect raw database content
    print("\n--- [Phase 2: Database State (Encrypted Phone Numbers)] ---")
    cur.execute("SELECT id, name, whatsapp_enc, ripe_chips, unripe_chips, total FROM orders")
    db_rows = cur.fetchall()
    for row in db_rows:
        preview_enc = row[2][:25] + "..."
        print(f" Row {row[0]}: Name='{row[1]}' | Phone='{preview_enc}' | Ripe={row[3]} | Unripe={row[4]} | Total={row[5]:,}")

    # 5. Simulate weekly script execution
    print("\n--- [Phase 3: Weekly Export & Decryption Execution] ---")
    cur.execute("SELECT id, name, whatsapp_enc, ripe_chips, unripe_chips, total, created_at FROM orders ORDER BY id")
    rows_to_export = cur.fetchall()

    csv_file = "simulated_weekly_orders.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "whatsapp", "ripe_chips", "unripe_chips", "total_chips", "total", "created_at"])
        for r in rows_to_export:
            decrypted_phone = fernet.decrypt(r[2].encode()).decode()
            writer.writerow([r[0], r[1], decrypted_phone, r[3], r[4], r[3] + r[4], r[5], r[6]])

    total_ripe = sum(r[3] for r in rows_to_export)
    total_unripe = sum(r[4] for r in rows_to_export)
    grand_total = sum(r[5] for r in rows_to_export)

    print(f"[*] Generated CSV file saved to disk: '{csv_file}'")

    # 6. Simulate Telegram delivery
    print("\n--- [Phase 4: Simulated Telegram Delivery to Seller] ---")
    print(f"[Telegram Bot Dispatch]: Sending '{csv_file}' to Chat ID: 123456789")
    print("Caption sent to Telegram:")
    print("--------------------------------------------------")
    print(f"Weekly orders report: {len(rows_to_export)} order(s)")
    print(f"- Ripe chips: {total_ripe} pack(s)")
    print(f"- Unripe chips: {total_unripe} pack(s)")
    print(f"- Total chips: {total_ripe + total_unripe} pack(s)")
    print(f"- Grand total: {grand_total:,}")
    print("--------------------------------------------------")
    print("[Telegram API Response]: HTTP 200 OK (Document delivered)")

    # 7. Safe deletion
    row_ids = [r[0] for r in rows_to_export]
    cur.executemany("DELETE FROM orders WHERE id = ?", [(i,) for i in row_ids])
    conn.commit()

    cur.execute("SELECT count(*) FROM orders")
    remaining = cur.fetchone()[0]
    print(f"\n[*] Cleared processed orders. Remaining rows in DB: {remaining}")
    conn.close()

    # Clean up local simulated sqlite DB
    if os.path.exists(db_path):
        os.remove(db_path)

    print("\n" + "=" * 65)
    print("SUCCESS: Full local simulation completed with 100% fidelity!")
    print("=" * 65)

if __name__ == "__main__":
    main()
