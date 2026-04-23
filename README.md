# 🚀 TaskPilot — AI-Powered WhatsApp Task Scheduler

<div align="center">

**An intelligent, multi-agent task management system that helps you organize your life through WhatsApp.**

Built with LangGraph • Llama 3.3 70B • FastAPI • APScheduler

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Natural Language Scheduling** | Just say "Remind me to call the bank tomorrow" — TaskPilot understands |
| 🤖 **Multi-Agent AI System** | 6 specialized LangGraph agents (Router, Planner, Tracker, Analyzer, Goal Setter, Chat) |
| ⏰ **Automated Reminders** | Morning task list at 8 AM, Night completion check at 9 PM |
| 📊 **Weekly AI Reports** | AI-generated insights about your productivity patterns |
| 🔥 **Streaks & Gamification** | XP, levels, streaks — stay motivated with game mechanics |
| 🎯 **Goal Tracking** | Set long-term goals, break them into daily tasks |
| 📱 **WhatsApp Integration** | Works via Meta Cloud API or Console mode for development |
| 🌐 **Premium Dashboard** | Stunning web dashboard for visual task management |
| 🔄 **Smart Rescheduling** | Missed tasks auto-reschedule without overloading your day |
| 😴 **Dormant Mode** | Bot backs off if you're unresponsive — no spam! |

## 🏗️ Architecture

```
User ──→ WhatsApp ──→ Webhook ──→ LangGraph Pipeline ──→ Database
                                       │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                       Router →  Planner/Tracker → Response
                                       │
                                  APScheduler
                              (Morning/Night/Weekly)
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd "task reminder bot"
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` with your Groq API key (already configured):

```env
LLM_API_KEY=gsk_your_groq_key
LLM_MODEL=llama-3.3-70b-versatile
WHATSAPP_MODE=console
```

### 3. Run the Server

```bash
# HTTP server with dashboard
python run.py server

# Interactive console chat
python run.py console
```

### 4. Access

- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## 📁 Project Structure

```
├── app/
│   ├── agents/          # LangGraph multi-agent system
│   │   ├── graph.py     # Main orchestrator
│   │   ├── router_agent.py
│   │   ├── planner_agent.py
│   │   ├── tracker_agent.py
│   │   └── analyzer_agent.py
│   ├── api/             # FastAPI endpoints
│   │   └── endpoints/
│   ├── core/            # Database, logging
│   ├── crud/            # Data access layer
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic validation
│   ├── services/        # Business logic
│   │   ├── orchestrator.py
│   │   ├── scheduler.py
│   │   ├── whatsapp.py
│   │   └── message_formatter.py
│   └── main.py          # FastAPI app factory
├── dashboard/           # Premium web dashboard
├── tests/               # Test suite
├── run.py               # CLI entry point
├── Dockerfile
└── docker-compose.yml
```

## 🧪 Testing

```bash
pytest tests/ -v --cov=app
```

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

## 📱 WhatsApp Setup (Production)

1. Create a Meta Developer App at https://developers.facebook.com
2. Enable WhatsApp Business API
3. Set webhook URL to `https://your-domain/api/v1/webhook/whatsapp`
4. Update `.env` with your credentials:
   ```env
   WHATSAPP_MODE=meta_cloud
   WHATSAPP_PHONE_NUMBER_ID=your_id
   WHATSAPP_ACCESS_TOKEN=your_token
   WHATSAPP_VERIFY_TOKEN=your_verify_token
   ```

## 📄 License

MIT License — Built with ❤️ using LangGraph + Groq
