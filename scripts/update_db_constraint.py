import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
if db_url:
    conn = psycopg2.connect(db_url)
    with conn, conn.cursor() as cur:
        # Update constraint so special orders with 0 ripe/unripe are allowed
        cur.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS at_least_one_item;")
        cur.execute(
            "ALTER TABLE orders ADD CONSTRAINT at_least_one_item "
            "CHECK (ripe_chips + unripe_chips > 0 OR is_special = TRUE);"
        )
        print("Updated constraint at_least_one_item successfully.")
    conn.close()
