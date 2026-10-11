<div align="center">

<img src="https://em-content.zobj.net/source/apple/391/banana_1f34c.png" width="72" alt="Plantain Chips">

# Weekly Order Collector

**A privacy-first, automated order management system for weekly plantain chips deliveries.**  
Built with Streamlit · Supabase · GitHub Actions · Telegram

[![Made with Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Community_Cloud-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/features/actions)

---

*Created by **Osazuwa***

</div>

---

## ✨ What It Does

Customers visit a beautiful web form, pick their chips, choose their delivery zone (Mainland or Island), and submit. Every **Wednesday at 5 PM**, an automated report is sent to the seller's Telegram — a decrypted CSV of all orders, broken down by location, with a clean summary. The database is then wiped clean for the next week.

Zero manual work. Zero spreadsheets. Zero exposed phone numbers.

---

## 🏗️ How It Works

```
Customer's Phone / Browser
         │
         ▼
Streamlit Community Cloud  (streamlit_app/app.py)
   ├─ Collects name, WhatsApp, packs, location
   ├─ Encrypts WhatsApp number with Fernet (AES-128)
   └─ Saves encrypted order to Supabase
         │
         ▼
Supabase  (PostgreSQL · orders table)
         ▲
         │  Every Wednesday at 16:00 UTC / 5:00 PM WAT
         │
GitHub Actions  (scripts/send_weekly.py)
   ├─ Reads all orders from Supabase
   ├─ Decrypts WhatsApp phone numbers
   ├─ Builds orders.csv (sorted by location)
   ├─ Sends CSV + summary to seller via Telegram Bot
   └─ Deletes delivered orders — ready for next week
```

---

## 📂 Project Structure

```
weekly-collector/
├── .github/
│   └── workflows/
│       └── weekly.yml           # Runs every Wednesday 5 PM WAT (+ manual trigger)
├── scripts/
│   ├── send_weekly.py           # Core export: DB → CSV → Telegram → cleanup
│   ├── generate_keys.py         # Generates ENCRYPTION_KEY + API_KEY
│   └── requirements.txt
├── sql/
│   └── schema.sql               # Supabase table + RLS policies
├── streamlit_app/
│   ├── app.py                   # Customer-facing order form (premium dark UI)
│   ├── requirements.txt
│   └── .streamlit/
│       └── secrets.toml         # Local secrets (gitignored)
├── .env                         # Local env vars (gitignored)
├── .gitignore
└── README.md
```

---

## 🔑 Secrets Reference

| Secret | Used In | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | Streamlit + GitHub Actions | Supabase PostgreSQL connection URI |
| `ENCRYPTION_KEY` | Streamlit + GitHub Actions | 44-char Fernet key for WhatsApp encryption |
| `TELEGRAM_BOT_TOKEN` | GitHub Actions only | Bot token from `@BotFather` |
| `TELEGRAM_CHAT_ID` | GitHub Actions only | Recipient's Telegram user/chat ID |

---

## 🚀 Deployment in 4 Steps

### 1 · Generate Secrets

```powershell
python scripts/generate_keys.py
```

Save the `ENCRYPTION_KEY` (44 characters ending in `=`) securely. **You cannot recover it if lost.**

---

### 2 · Set Up Supabase

1. Create a free project at [supabase.com](https://supabase.com) named `weekly-collector`.
2. Open **SQL Editor → New Query**, paste `sql/schema.sql`, click **Run**.
3. Go to **Settings → Database → Connection string → URI → Mode: Session**.
4. Copy the URI and replace `[YOUR-PASSWORD]`:

```
postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```

> **Existing deployment?** Run this to add the location column:
> ```sql
> ALTER TABLE orders ADD COLUMN IF NOT EXISTS location TEXT NOT NULL DEFAULT 'MAINLAND' CHECK (location IN ('MAINLAND', 'ISLAND'));
> ```

---

### 3 · Set Up Telegram Bot

1. Search `@BotFather` in Telegram → send `/newbot` → follow the prompts.
2. Save the token as `TELEGRAM_BOT_TOKEN`.
3. Open your bot's link and click **Start**, then send any message.
4. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and find `"chat":{"id": ...}`.
5. That number is your `TELEGRAM_CHAT_ID`.

---

### 4 · Push & Deploy

**GitHub** — add 4 repository secrets under *Settings → Secrets → Actions*:
`DATABASE_URL` · `ENCRYPTION_KEY` · `TELEGRAM_BOT_TOKEN` · `TELEGRAM_CHAT_ID`

**Streamlit Cloud** — deploy at [share.streamlit.io](https://share.streamlit.io):
- Main file: `streamlit_app/app.py`
- Advanced secrets (paste 2 only):
```toml
DATABASE_URL = "your-supabase-uri"
ENCRYPTION_KEY = "your-44-char-key"
```

---

## 🔄 Day-to-Day

| | |
|---|---|
| **Schedule** | Every Wednesday at 5:00 PM WAT (16:00 UTC) |
| **Manual trigger** | GitHub → Actions → Weekly report → Run workflow |
| **View live orders** | Supabase Dashboard → Table Editor → `orders` |
| **Phone numbers** | Always encrypted in the DB (`gAAAA...` format) |
| **After each report** | Table is automatically cleared for the next batch |

---

## 🛡️ Privacy & Security

- Customer WhatsApp numbers are **encrypted with Fernet (AES-128-CBC)** before leaving the browser.
- The database only stores the encrypted blob — never a raw phone number.
- Decryption only happens inside GitHub Actions, in memory, during the weekly export.
- Row Level Security (RLS) on Supabase ensures anonymous users can only insert — never read or delete.

---

<div align="center">

Made with ❤️ by **Osazuwa**

</div>
