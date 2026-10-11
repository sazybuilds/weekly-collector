# 📦 Weekly Order Collector (Supabase Edition)

An automated, privacy-focused order collection application built with **Streamlit**, **Supabase (PostgreSQL)**, **GitHub Actions**, and **Telegram**.

---

## 🏗️ Architecture Overview

In this edition, **Supabase completely replaces Neon and Oracle Cloud VM**:

```
Customer's Phone / Browser
         │
         ▼
Streamlit Community Cloud (streamlit_app/app.py)
   • Validates name, phone, ripe & unripe chips quantities
   • Calculates order total ((Ripe + Unripe packs) × 2,500)
   • Encrypts WhatsApp phone number with Fernet
   • Directly saves order into Supabase
         │
         ▼
Supabase Database (PostgreSQL table: orders)
         ▲
         │ Every Monday at 13:00 UTC (or manual click)
         │
GitHub Actions (scripts/send_weekly.py)
   • Reads all weekly orders
   • Decrypts WhatsApp phone numbers
   • Generates CSV report
   • Sends CSV document to the seller via Telegram Bot
   • Safely clears delivered orders from the database
```

### Why Supabase only?
- **No Oracle Cloud VM needed**: You do not need to create an Oracle Cloud account, set up credit card verification, configure Linux VMs, manage SSH keys, open firewall ports, configure Caddy HTTPS reverse proxy, or manage DuckDNS.
- **Streamlit connects directly**: Streamlit Community Cloud runs secure Python server-side, encrypting data with Fernet before it touches the database.
- **Unified platform**: Database, pooling, backups, and SQL management are all handled in Supabase.

---

## 📂 Project Structure

```
weekly-collector/
├── .github/
│   └── workflows/
│       └── weekly.yml          # GitHub Actions weekly schedule & manual trigger
├── api/
│   ├── main.py                 # FastAPI server (optional / local testing)
│   └── requirements.txt
├── scripts/
│   ├── send_weekly.py          # Script: reads DB -> generates CSV -> Telegram -> deletes sent orders
│   ├── generate_keys.py        # Helper to generate API_KEY and ENCRYPTION_KEY
│   └── requirements.txt
├── sql/
│   └── schema.sql              # Supabase table definition & RLS policies
├── streamlit_app/
│   ├── app.py                  # Streamlit web application for customers
│   ├── requirements.txt
│   └── .streamlit/
│       └── secrets.toml.example # Example secrets file for local development
├── .gitignore
├── order_collector_guide.pdf   # Original guide
└── README.md
```

---

## 🚀 Quick Setup Steps

### 1. Generate Application Secrets
Run the key generation script:
```powershell
python scripts/generate_keys.py
```
This produces:
- `API_KEY`
- `ENCRYPTION_KEY` (44 characters ending in `=`)

*Keep your `ENCRYPTION_KEY` in a secure place. If you lose it, stored phone numbers cannot be decrypted.*

---

### 2. Set Up Supabase
1. Go to [supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and name it `weekly-collector`. Choose a region close to your target audience and set a strong database password.
3. In the left navigation, open **SQL Editor** > **New Query**.
4. Paste the content of `sql/schema.sql` and click **Run**.
5. Go to **Project Settings** (gear icon) > **Database**.
6. Scroll down to **Connection string** > select **URI** > select **Mode: Session** (or **Transaction**, port `6543`).
7. Copy the connection string. Replace `[YOUR-PASSWORD]` with the database password you created in step 2:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
   *This is your `DATABASE_URL`.*

---

### 3. Create Telegram Bot
1. In Telegram, search for `@BotFather` (with the verified blue tick).
2. Send `/newbot`.
3. Enter a display name (e.g. `Weekly Orders Bot`).
4. Enter a username ending in `bot` (e.g. `my_weekly_orders_bot`).
5. Copy the bot token provided (e.g. `123456789:AAExampleTokenText`). *This is `TELEGRAM_BOT_TOKEN`.*
6. Open your new bot's link (`https://t.me/YOUR_BOT_USERNAME`) and click **Start**.
7. In your browser, open:
   ```
   https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
   ```
8. Look for `"chat":{"id": 123456789}`. That number is your `TELEGRAM_CHAT_ID`.

---

### 4. Local Testing
1. Create a virtual environment and install dependencies:
   ```powershell
   uv venv --python 3.12
   .venv\Scripts\activate
   uv pip install -r streamlit_app/requirements.txt -r scripts/requirements.txt
   ```
2. Copy `streamlit_app/.streamlit/secrets.toml.example` to `streamlit_app/.streamlit/secrets.toml` and fill in your `DATABASE_URL` and `ENCRYPTION_KEY`.
3. Run the Streamlit web form:
   ```powershell
   cd streamlit_app
   streamlit run app.py
   ```
4. Fill out an order and click **Submit Order**. Verify the order appears encrypted in Supabase under **Table Editor** > `orders`.
5. Test the weekly export script:
   ```powershell
   cd ..
   $env:DATABASE_URL="your-supabase-db-url"
   $env:ENCRYPTION_KEY="your-encryption-key"
   $env:TELEGRAM_BOT_TOKEN="your-telegram-token"
   $env:TELEGRAM_CHAT_ID="your-telegram-chat-id"
   python scripts/send_weekly.py
   ```
   Verify that a CSV arrives on Telegram and that the table is cleared.

---

### 5. Deploy to Production
1. Push this repository to a **Private** repository on GitHub.
2. In GitHub, go to **Settings** > **Secrets and variables** > **Actions** > **New repository secret** and add:
   - `DATABASE_URL`
   - `ENCRYPTION_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. In [share.streamlit.io](https://share.streamlit.io), deploy your app:
   - Repository: `YOUR_USERNAME/weekly-collector`
   - Main file path: `streamlit_app/app.py`
   - Under **Advanced settings** > **Secrets**, paste:
     ```toml
     DATABASE_URL = "postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require"
     ENCRYPTION_KEY = "your-encryption-key"
     ```
4. Click **Deploy**. Your app is live!
