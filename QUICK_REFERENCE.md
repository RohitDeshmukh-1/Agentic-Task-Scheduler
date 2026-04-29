# 🚀 TaskPilot Telegram - Quick Reference

## ⚡ 30-Second Setup

```bash
# 1. Get token from @BotFather on Telegram
# 2. Update .env
TELEGRAM_BOT_TOKEN=your_token_here
MESSAGING_PLATFORM=telegram

# 3. Validate
python validate_telegram_setup.py

# 4. Run
python run.py server

# 5. Find your bot on Telegram (@your_botname)
# 6. Send /start
```

---

## 📝 .env Configuration

```env
# REQUIRED
TELEGRAM_BOT_TOKEN=123456789:ABCDefGHIjklMNOpqrsTUVwxyz
MESSAGING_PLATFORM=telegram

# REQUIRED (Free from console.groq.com)
LLM_API_KEY=gsk_your_key_here

# Optional but recommended
TELEGRAM_MODE=webhook          # or "polling"
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

---

## 🔗 Common Commands

### Get Bot Token
```bash
# Telegram -> @BotFather -> /newbot -> [follow steps]
```

### Set Webhook (Production)
```bash
curl -X POST https://api.telegram.org/botTOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/webhook/telegram"}'
```

### Check Webhook Status
```bash
curl https://api.telegram.org/botTOKEN/getWebhookInfo
```

### Reset Webhook
```bash
curl -X POST https://api.telegram.org/botTOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":""}'
```

### View Logs (Docker)
```bash
docker logs -f taskpilot --tail=100
```

### Check Health
```bash
curl http://localhost:8000/api/v1/health
```

---

## 🤖 Bot User Commands

Send these in Telegram:
- `/start` - Welcome message
- `/help` - Show help
- `Add a task tomorrow` - Natural language
- `Mark complete` - Update task status
- `Show summary` - Daily stats

---

## 🔑 Environment Variables

| Variable | Example | Required |
|----------|---------|----------|
| TELEGRAM_BOT_TOKEN | 123:ABC... | ✅ |
| MESSAGING_PLATFORM | telegram | ✅ |
| LLM_API_KEY | gsk_... | ✅ |
| TELEGRAM_MODE | webhook | ❌ |
| APP_ENV | production | ❌ |
| DATABASE_URL | sqlite:/// | ❌ |

---

## 🚨 Common Issues

### Bot not responding
- ✅ Token is set in .env
- ✅ Server is running
- ✅ Webhook is set (production)
- ✅ Check: `docker logs taskpilot`

### "Webhook verification failed"
- ✅ HTTPS only (not HTTP)
- ✅ Domain has SSL cert
- ✅ Firewall allows 443
- ✅ Reset webhook first

### Import errors
```bash
pip install -r requirements.txt
python validate_telegram_setup.py
```

---

## 📊 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/telegram` | POST | Telegram incoming messages |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |
| `/console` | POST | Dev testing |

---

## 🐳 Docker Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker logs -f taskpilot

# Restart
docker-compose restart

# Rebuild
docker-compose up -d --build
```

---

## 📱 Webhook URL Format

```
https://your-domain.com/api/v1/webhook/telegram
```

Make sure:
- ✅ HTTPS (not HTTP)
- ✅ Valid SSL certificate
- ✅ Domain is accessible
- ✅ Port 443 is open

---

## 🔒 Security Reminders

- 🔐 Never commit TELEGRAM_BOT_TOKEN
- 🔐 Use .env for secrets
- 🔐 Add .env to .gitignore
- 🔐 HTTPS only in production
- 🔐 Strong APP_SECRET_KEY

---

## 📞 Getting Help

1. Run: `python validate_telegram_setup.py`
2. Check: `docker logs taskpilot`
3. Read: `TELEGRAM_SETUP.md`
4. Verify: `.env` file has token

---

## 📚 Documentation

- **MIGRATION_COMPLETE.md** - Full migration summary
- **TELEGRAM_SETUP.md** - Detailed setup guide
- **README.md** - General overview
- **validate_telegram_setup.py** - Diagnostic tool

---

## ✅ Deployment Checklist

- [ ] Bot token from @BotFather
- [ ] .env configured with token
- [ ] `python validate_telegram_setup.py` passes
- [ ] Server starts: `python run.py server`
- [ ] Bot responds in Telegram
- [ ] Webhook set (production only)
- [ ] Logs show no errors
- [ ] Health check passes

---

## 🚀 Ready?

```bash
# 1. Get token (@BotFather)
# 2. Set in .env: TELEGRAM_BOT_TOKEN=...
# 3. Run: python validate_telegram_setup.py
# 4. Run: python run.py server
# 5. Open Telegram, send /start
```

**That's it!** 🎉

---

**Platform**: Telegram  
**Status**: Production-Ready ✅  
**Mode**: Webhook  
**Database**: SQLite (dev) / PostgreSQL (prod)  
**Last Updated**: 2026-04-28
