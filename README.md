# 💸 Finance Tracker Telegram Bot

Personal finance tracker bot for 3–5 users. Track expenses, money lent, and view monthly reports — all from Telegram.

---

## Features

| Section | Capabilities |
|---------|-------------|
| 💸 Expenses | Log expenses by category, custom categories, smart amount parser |
| 💵 Money Lent | Track who owes you, mark as returned, edit/delete entries |
| 📊 Monthly Report | Category breakdown, active lent summary, previous months |

---

## Tech Stack

- **Python 3.12**
- **python-telegram-bot v21** (webhook, async)
- **FastAPI** + **Uvicorn** (webhook server + `/health` endpoint)
- **PostgreSQL** via **Neon** (async with `asyncpg`)
- **SQLAlchemy 2.0** ORM (async)
- **Alembic** migrations
- **Railway** deployment

---

## Project Structure

```
finance_bot/
├── bot.py                  # Entry point: FastAPI app + bot wiring
├── config.py               # Environment config
├── requirements.txt
├── Procfile
├── alembic.ini
├── .env.example
├── handlers/
│   ├── start.py            # /start, main menu
│   ├── expenses.py         # Expense conversation
│   ├── money_lent.py       # Money lent conversation
│   └── reports.py          # Monthly reports
├── database/
│   ├── db.py               # Async engine + session
│   ├── models.py           # SQLAlchemy ORM models
│   └── repositories.py     # Repository pattern
├── services/
│   ├── expense_service.py
│   ├── lent_service.py
│   └── report_service.py
├── utils/
│   ├── parser.py           # Amount/lent entry parser
│   ├── keyboards.py        # All keyboard builders
│   └── scheduler.py        # Month/timezone helpers
└── migrations/
    ├── env.py
    └── versions/
        └── 001_initial.py
```

---

## Local Setup

### 1. Clone and install

```bash
git clone <repo>
cd finance_bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN, DATABASE_URL, WEBHOOK_URL
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Expose local server (for webhook testing)

```bash
# Install ngrok or use cloudflared
ngrok http 8000
# Set WEBHOOK_URL=https://xxxx.ngrok.io in .env
```

### 5. Start the bot

```bash
python bot.py
```

---

## Railway Deployment

### 1. Create Railway project

```bash
railway login
railway init
railway link
```

### 2. Set environment variables in Railway dashboard

```
BOT_TOKEN=...
DATABASE_URL=postgresql://...   # from Neon
WEBHOOK_URL=https://your-app.up.railway.app
TIMEZONE=Asia/Tashkent
```

Railway auto-injects `PORT`.

### 3. Deploy

```bash
git push  # Railway auto-deploys on push
# or:
railway up
```

### 4. Run migrations on Railway

```bash
railway run alembic upgrade head
```

---

## Amount Parser Examples

| Input | Parsed |
|-------|--------|
| `29000` | 29,000 UZS |
| `29 000` | 29,000 UZS |
| `29,000` | 29,000 UZS |
| `29k` | 29,000 UZS |
| `1.5m` | 1,500,000 UZS |
| `100$` | 100 USD |
| `100 USD` | 100 USD |
| `29000 Osh` | 29,000 UZS, note: "Osh" |

---

## Health Check

```
GET /health
→ {"status": "ok", "bot": "Finance Tracker"}
```

---

## Database Tables

| Table | Description |
|-------|-------------|
| `users` | Telegram user records |
| `expenses` | Individual expense entries |
| `money_lent` | Lent money tracking |
| `custom_categories` | Per-user custom categories |
| `month_state` | Month transition tracking |

---

## License

MIT
