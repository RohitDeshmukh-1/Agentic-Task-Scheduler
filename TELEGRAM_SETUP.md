# 🤖 Telegram Setup Guide for TaskPilot

This guide will walk you through setting up TaskPilot to work with Telegram in production.

## Prerequisites

- ✅ Python 3.13+ installed
- ✅ Telegram account
- ✅ Groq API key (from https://console.groq.com)
- ✅ Domain with SSL certificate (for webhook mode)
- ✅ Server running on port 8000 (or your chosen port)

---

## 🚀 Step 1: Create a Telegram Bot

### Quick Steps

1. Open Telegram app or go to https://web.telegram.org
2. Search for **@BotFather** (official bot by Telegram)
3. Send: `/newbot`
4. Choose a name for your bot (e.g., "TaskPilot")
5. Choose a username for your bot (e.g., "my_taskpilot_bot")
6. **Save the API Token** - looks like: `123456789:ABCDefGHIjklMNOpqrsTUVwxyz`

### Example:
```
BotFather: Choose a name for your bot. For example, TetrisBot or google_translating_bot.
You: TaskPilot
BotFather: Good. Now choose a username for your bot. It must end in `bot`. 
You: taskpilot_bot
BotFather: Done! Congratulations on your new bot.
         You will find it at t.me/taskpilot_bot. You can now add a description, about 
         section and profile picture for your bot, see /help for a list of commands.

         Here's your token:
         123456789:ABCDefGHIjklMNOpqrsTUVwxyz
```

---

## 📝 Step 2: Configure Your Environment

Edit your `.env` file:

```env
# ─── Telegram Configuration ───────────────────────────────────
TELEGRAM_BOT_TOKEN=123456789:ABCDefGHIjklMNOpqrsTUVwxyz
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_SECRET=taskpilot_telegram_2026

# ─── Select Telegram as Platform ──────────────────────────────
MESSAGING_PLATFORM=telegram

# ─── LLM (Groq - get free key from console.groq.com) ─────────
LLM_API_KEY=gsk_your_groq_key_here
LLM_MODEL=llama-3.3-70b-versatile

# ─── App Configuration ────────────────────────────────────────
APP_ENV=production
APP_SECRET_KEY=change-me-to-random-secret
APP_HOST=0.0.0.0
APP_PORT=8000

# ─── Database (PostgreSQL recommended for production) ─────────
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/taskpilot
```

---

## 🔗 Step 3: Set Up Webhook (Production Setup)

### Option A: Direct Setup (Recommended)

Your server must have a domain with SSL/TLS certificate (HTTPS).

#### 3.1 Start the server
```bash
python run.py server
```

#### 3.2 Configure Telegram webhook
Replace `your-domain.com` with your actual domain:

```bash
curl -X POST https://api.telegram.org/bot123456789:ABCDefGHIjklMNOpqrsTUVwxyz/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/webhook/telegram"}'
```

#### 3.3 Verify webhook is set
```bash
curl https://api.telegram.org/bot123456789:ABCDefGHIjklMNOpqrsTUVwxyz/getWebhookInfo
```

Expected response:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-domain.com/api/v1/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

### Option B: Using Polling (If Webhook Won't Work)

Polling is easier but less efficient:

```env
TELEGRAM_MODE=polling
```

Then:
```bash
python run.py server
```

The bot will check for updates every 25 seconds instead of using webhooks.

---

## 🐳 Step 4: Docker Deployment

### 4.1 Update `.env` with your Telegram token

```env
TELEGRAM_BOT_TOKEN=your_token_here
MESSAGING_PLATFORM=telegram
```

### 4.2 Deploy with Docker Compose

```bash
docker-compose up -d
```

### 4.3 Get inside the container and set webhook

```bash
# Find the container ID
docker ps

# Set webhook (replace YOUR_TOKEN and your-domain.com)
docker exec taskpilot curl -X POST \
  https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/webhook/telegram"}'

# Check webhook status
docker exec taskpilot curl \
  https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo
```

### 4.4 View logs

```bash
docker logs -f taskpilot
```

---

## 🧪 Step 5: Test Your Bot

### 5.1 Find your bot on Telegram

Go to Telegram and search for: `@your_botname` (e.g., `@taskpilot_bot`)

### 5.2 Start the bot

Send `/start` to your bot

Expected response:
```
👋 Hey! I'm TaskPilot, your AI task companion.

I can help you:
- 📝 Create tasks with natural language
- 🎯 Track your goals
- 📊 Get productivity insights
- 🔥 Build streaks and earn XP
```

### 5.3 Test core functionality

Try these messages:
```
Add a task to call John tomorrow at 2 PM

Create a goal to learn Spanish by June

What tasks do I have today?

Complete the call to John task

Show me my summary
```

---

## 🔧 Troubleshooting

### Issue: "Webhook verification failed"

**Solution:** Make sure your domain:
1. Has a valid SSL certificate (HTTPS)
2. Is accessible from the internet
3. Your server is actually running
4. Firewall allows port 443 (HTTPS)

```bash
# Test from outside your network
curl -I https://your-domain.com
```

### Issue: "Bot not responding"

**Check logs:**
```bash
# Local
tail -f debug.log

# Docker
docker logs -f taskpilot
```

**Verify webhook status:**
```bash
curl https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo
```

### Issue: "Pending updates"

If webhook has pending updates, reset it:

```bash
# Remove webhook
curl -X POST https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":""}'

# Re-set webhook
curl -X POST https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/webhook/telegram"}'
```

### Issue: Database connection errors

Make sure your `DATABASE_URL` in `.env` is correct:
- SQLite: `sqlite+aiosqlite:///./taskbot.db`
- PostgreSQL: `postgresql+asyncpg://user:password@host:5432/dbname`

---

## 🚀 Production Checklist

- [ ] Telegram bot created and token saved
- [ ] `.env` configured with bot token
- [ ] Domain with SSL certificate ready
- [ ] Server running and accessible
- [ ] Webhook endpoint set and verified
- [ ] Bot tested with sample messages
- [ ] Logs being monitored
- [ ] Database backups configured
- [ ] Groq API key configured
- [ ] Scheduler jobs enabled

---

## 📊 Monitoring

### View Active Chats

```bash
# Check database
sqlite3 taskbot.db
> SELECT id, phone_number, display_name, current_streak FROM users;
```

### Check Bot Health

```bash
curl http://localhost:8000/api/v1/health
```

### View Logs

```bash
# Development
python run.py server

# Docker
docker logs -f taskpilot

# Specific log file
tail -f debug.log
```

---

## 🔐 Security Best Practices

1. **Never commit your bot token** to Git
2. **Use environment variables** for all secrets
3. **Enable webhooks with HTTPS only** (not HTTP)
4. **Set strong `APP_SECRET_KEY`** in production
5. **Use PostgreSQL** instead of SQLite in production
6. **Enable logging** for audit trails
7. **Rate limit** API endpoints (can be added if needed)
8. **Regularly rotate** tokens if compromised

---

## 📞 Getting Help

If something goes wrong:

1. **Check logs**: `docker logs taskpilot`
2. **Verify webhook**: `curl api.telegram.org/botTOKEN/getWebhookInfo`
3. **Test connectivity**: `curl -I https://your-domain.com`
4. **Check .env**: Make sure all required variables are set
5. **Restart service**: `docker-compose restart`

---

## 📚 Useful Links

- 🤖 Telegram Bot API: https://core.telegram.org/bots/api
- 🧙 BotFather: https://t.me/BotFather
- 🔑 Groq Console: https://console.groq.com
- 📖 TaskPilot Docs: See README.md

---

Happy task managing! 🚀
