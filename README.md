# 🚀 TaskPilot — AI-Powered Telegram Task Scheduler

<div align="center">

**A production-grade, multi-agent Telegram task scheduler that turns natural language into structured plans, reminders, and weekly insights.**

Built with LangGraph • Llama 3.3 70B • FastAPI • APScheduler

</div>

---

## Why It Stands Out

- **Multi-agent architecture**: Router, Planner, Tracker, Analyzer, Goal Setter, and Chat agents coordinate to interpret intent and act.
- **Natural-language first**: Users speak in plain English; tasks, goals, and updates are structured automatically.
- **Operationally mature**: Async DB, cron-based scheduling, health checks, and production-ready webhook handling.
- **Behavior-aware**: Streaks, XP, dormant mode, and weekly reports keep engagement high without spamming.

---

## Highlights

| Capability | What it delivers |
|-----------|------------------|
| 🧠 **Natural Language Scheduling** | “Remind me to call the bank tomorrow” becomes a task with date + priority |
| 🤖 **Multi-Agent Orchestration** | Six specialized agents collaborate on parsing, planning, and tracking |
| ⏰ **Automated Reminders** | Morning and night check-ins, plus weekly productivity reports |
| 🔄 **Smart Rescheduling** | Missed tasks re-planned without overloading your day |
| 🔥 **Gamification** | Streaks, XP, and levels drive consistency |
| 📱 **Telegram-Ready** | Webhook/polling modes with robust callback handling |

---

## Architecture

```mermaid
flowchart LR
  user(["User"]) --> tg["Telegram"]
  tg --> api["FastAPI Webhook / Polling"]
  api --> orch["OrchestrationService"]
  orch --> graph["LangGraph Pipeline"]
  graph --> router["Router Agent"]
  router --> planner["Planner Agent"]
  router --> tracker["Tracker Agent"]
  router --> goal["Goal Setter"]
  router --> query["Query Handler"]
  planner --> db[(Database)]
  tracker --> db
  goal --> db
  query --> db
  db --> orch
  sched[APScheduler Jobs] --> orch
  orch --> tg
```

## User Flow

```mermaid
sequenceDiagram
  participant U as User
  participant T as Telegram
  participant A as API
  participant O as OrchestrationService
  participant G as LangGraph
  participant D as Database

  U->>T: "Remind me to go to the gym at 6pm except Sundays"
  T->>A: Webhook/Update
  A->>O: handle_incoming_message
  O->>G: process_message
  G->>O: intent + extracted tasks
  O->>D: persist tasks / recurring rules
  O->>T: confirmation + schedule
  T->>U: "Tasks scheduled" message
```

Flow summary:
- User sends a natural-language request.
- Intent is classified and tasks are extracted.
- Tasks (and recurrence rules if any) are saved per user.
- Scheduler jobs deliver reminders and check-ins.

---

## Quick Start (Run via TeleBot)

### 1) Install

```bash
cd "task reminder bot"
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2) Configure

Create `.env`:

```env
LLM_API_KEY=gsk_your_groq_key
LLM_MODEL=llama-3.3-70b-versatile

TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_SECRET=taskpilot_telegram_2026
```

### 3) Run

```bash
python run.py server
```

### 4) Use the TeleBot

- Open Telegram and search for your bot
- Send `/start`
- Try: “Add a task to call John tomorrow at 10am”

---

## Production Webhook Setup

```bash
curl -X POST https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/webhook/telegram"}'

curl https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
```

---

## Railway Deployment

This repo already includes Railway config via Dockerfile + [railway.toml](railway.toml).

### 1) Create a Railway project

- New Project → Deploy from GitHub
- Select this repository

### 2) Add a Postgres database

- Add → Database → PostgreSQL
- Copy the database URL into `DATABASE_URL`

### 3) Set environment variables

Minimum required:

```env
APP_ENV=production
APP_SECRET_KEY=change-me-to-random-secret

LLM_API_KEY=your_key
LLM_MODEL=llama-3.3-70b-versatile

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_SECRET=taskpilot_telegram_2026

DATABASE_URL=postgresql+asyncpg://user:password@host:5432/taskpilot
```

Webhook URL options (pick one):

- `TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/webhook/telegram`
- `PUBLIC_BASE_URL=https://your-domain.com`
- Or leave both empty and Railway will use `RAILWAY_PUBLIC_DOMAIN` automatically.

### 4) Deploy

Railway will build the Dockerfile and run:

```bash
python run.py server
```

On startup, the app will auto-configure Telegram webhook if `TELEGRAM_MODE=webhook` and a public URL is available.

---

## Project Structure

```
├── app/
│   ├── agents/          # LangGraph multi-agent system
│   ├── api/             # FastAPI endpoints
│   ├── core/            # Database, logging
│   ├── crud/            # Data access layer
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic validation
│   ├── services/        # Orchestration, scheduler, Telegram
│   └── main.py          # FastAPI app factory
├── dashboard/           # Web dashboard
├── tests/               # Test suite
├── run.py               # CLI entry point
├── Dockerfile
└── docker-compose.yml
```

---

## Testing

```bash
pytest tests/ -v --cov=app
```

---

## Docker

```bash
docker-compose up -d
```

---

## Live Endpoints

- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

```bash
# No external API needed — test in terminal
python run.py console
```

### Development Webhook (Without SSL)

```bash
# Test webhook locally with dev endpoint
curl -X POST http://localhost:8000/api/v1/webhook/console \
  -H "Content-Type: application/json" \
  -d '{"user_id":"123","message":"Add a task tomorrow"}'
```

### Telegram Polling (Alternative to Webhook)

If webhook setup is difficult, use polling mode:

```env
TELEGRAM_MODE=polling
```

Then start the bot:
```bash
python run.py server
```

---

## 🐳 Docker Deployment with Telegram

```bash
# 1. Update .env with your Telegram bot token
TELEGRAM_BOT_TOKEN=YOUR_TOKEN
MESSAGING_PLATFORM=telegram

# 2. Deploy
docker-compose up -d

# 3. Configure webhook (inside container)
docker exec taskpilot curl -X POST https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/webhook/telegram"}'

# 4. Check logs
docker logs -f taskpilot
```

---

## 📄 Telegram Features

### Supported Commands
- `/start` — Welcome message
- `/help` — Show available commands
- `/tasks` — List all tasks
- `/add` — Add a new task
- `/goals` — View goals

### Message Format
Messages support:
- ✅ Bold text: `**text**`
- 📌 Inline buttons for quick actions
- 🔗 Links: `[text](url)`
- 📊 Code blocks for reports

---

## 📄 License

MIT License — Built with ❤️ using LangGraph + Groq
