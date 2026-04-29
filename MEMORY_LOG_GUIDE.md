# 📝 Memory Log System Guide

The TaskPilot memory log system enables users to maintain detailed logs of their tasks, plans, and reflections. Combined with the AI suggestion engine, it helps users identify patterns and improve productivity.

## Features

### 1. **Conversation Memory**
Every interaction with TaskPilot is automatically saved with metadata:
- **Intent tracking**: Automatically categorizes conversations (scheduling, status updates, planning, etc.)
- **Conversation context**: Recent messages are used to provide smarter suggestions
- **7-day summaries**: View patterns and trends in your conversations

### 2. **Personal Memory Logs**
Users can explicitly create memory logs with:
- **Task Notes**: Quick observations about task completion
- **Plans**: Document intentions and upcoming work
- **Reflections**: Journal entries and personal insights
- **Milestones**: Celebrate achievements and progress

### 3. **AI Suggestions**
Based on memory logs and conversation history, TaskPilot generates:
- **Planning suggestions**: Optimize your task structure
- **Habit tracking insights**: Identify productivity patterns
- **Goal alignment recommendations**: Connect tasks to bigger goals
- **Productivity tips**: Personalized advice based on your data

---

## Using Memory Logs via Telegram

### Command: `/log`
Create structured memory log entries.

**Format:**
```
/log <type> <category> <content>
```

**Types:**
- `task_note` - Quick notes about task completion
- `plan` - Planning and intention statements
- `reflection` - Personal insights and journal entries
- `milestone` - Achievements and progress markers

**Categories:**
- `work` - Work-related entries
- `health` - Health and wellness
- `personal` - Personal development
- `learning` - Learning and growth
- Any custom category you prefer

**Examples:**

```
/log task_note work Finished quarterly report 2 days early
/log plan health Start gym routine tomorrow morning
/log reflection personal Today's lesson: consistency beats perfection
/log milestone career Got promotion! 🎉
```

**Response:**
✅ Logged task_note in work:
Finished quarterly report 2 days early

---

### Command: `/memory`
View your 7-day memory log summary.

**Format:**
```
/memory
```

**Response:**
```
📝 Your Memory Log Summary (Last 7 Days)

Total logs: 12

📋 By Type:
  • task_note: 5 entries
  • plan: 4 entries
  • reflection: 2 entries
  • milestone: 1 entry

📂 By Category:
  • work: 8 entries
  • health: 3 entries
  • personal: 1 entry

⭐ Recent High Importance:
  • task_note: Completed major project on budget
  • milestone: Hit personal best time on 5K run
  • reflection: Need to focus on daily standup consistency
```

---

### Command: `/reflect`
Quick way to add personal reflections and journal entries.

**Format:**
```
/reflect <your reflection>
```

**Examples:**

```
/reflect Today was productive, completed 5 tasks and learned something new
/reflect Struggling with focus, need to take more breaks
/reflect Great momentum this week, ready to tackle bigger projects
```

**Response:**
```
✨ Reflection logged:
Today was productive, completed 5 tasks and learned something new

Keep reflecting to understand your patterns better!
```

---

### Command: `/suggest`
Get personalized AI suggestions based on your memory and history.

**Format:**
```
/suggest
```

**Response Example:**
```
💡 Personalized Suggestions:

Based on your 7-day history, here are 5 recommendations:

1. **Schedule Focus Blocks**: You've noted difficulty with focus. Try 90-minute deep work sessions.

2. **Build on Momentum**: You have a 5-day streak! Keep it alive by scheduling tasks consistently.

3. **Time Boxing**: Your reflection mentions completing 5 tasks today. Apply this pace to other days.

4. **Prioritize High-Impact Work**: 60% of your high-importance logs are work-related. Dedicate morning hours.

5. **Daily Reflection Habit**: Your insights are valuable. Try a 5-minute evening reflection for continuous improvement.

Your current Level: 8 | Streak: 5 days | XP: 742
```

---

## Using Memory Logs via API

### Endpoint: `POST /api/v1/api/memory/log`

Create a memory log entry programmatically.

**Request:**
```json
{
  "chat_id": "1234567890",
  "log_data": {
    "log_type": "task_note",
    "content": "Completed quarterly report",
    "category": "work",
    "importance": 4,
    "tags": "productive,report",
    "linked_task_ids": "uuid-123,uuid-456"
  }
}
```

**Response:**
```json
{
  "id": "uuid-789",
  "user_id": "uuid-user",
  "log_type": "task_note",
  "content": "Completed quarterly report",
  "category": "work",
  "importance": 4,
  "tags": "productive,report",
  "linked_task_ids": "uuid-123,uuid-456",
  "created_at": "2024-12-19T10:30:00",
  "updated_at": "2024-12-19T10:30:00"
}
```

---

### Endpoint: `GET /api/v1/api/memory/logs`

Retrieve recent memory logs.

**Query Parameters:**
- `chat_id` (required): User's Telegram chat ID
- `limit` (optional, default=10): Number of logs to return
- `log_type` (optional): Filter by log type (task_note, plan, reflection, milestone)

**Example:**
```
GET /api/v1/api/memory/logs?chat_id=1234567890&limit=5&log_type=task_note
```

**Response:**
```json
[
  {
    "id": "uuid-1",
    "user_id": "uuid-user",
    "log_type": "task_note",
    "content": "Finished early",
    "category": "work",
    "importance": 3,
    "created_at": "2024-12-19T10:30:00"
  },
  {
    "id": "uuid-2",
    "user_id": "uuid-user",
    "log_type": "task_note",
    "content": "Completed report",
    "category": "work",
    "importance": 4,
    "created_at": "2024-12-18T14:20:00"
  }
]
```

---

### Endpoint: `GET /api/v1/api/memory/summary`

Get 7-day memory log summary.

**Query Parameters:**
- `chat_id` (required): User's Telegram chat ID
- `days` (optional, default=7): Number of days to analyze

**Example:**
```
GET /api/v1/api/memory/summary?chat_id=1234567890&days=14
```

**Response:**
```json
{
  "total_logs": 12,
  "by_type": {
    "task_note": ["Finished early", "Completed report"],
    "plan": ["Start gym routine"],
    "reflection": ["Good day today"]
  },
  "by_category": {
    "work": ["Finished early", "Completed report"],
    "health": ["Start gym routine"],
    "personal": ["Good day today"]
  },
  "recent_high_importance": [
    {
      "type": "task_note",
      "content": "Completed major project"
    }
  ]
}
```

---

### Endpoint: `POST /api/v1/api/memory/suggest`

Get AI-generated suggestions.

**Request:**
```json
{
  "chat_id": "1234567890",
  "request": {
    "suggestion_type": "planning",
    "context_days": 7
  }
}
```

**Suggestion Types:**
- `planning` - Task organization and scheduling suggestions
- `optimization` - Performance improvement recommendations
- `habit_tracking` - Pattern insights and habit forming tips
- `goal_alignment` - How to better align tasks with goals

**Response:**
```json
{
  "suggestion_type": "planning",
  "suggestions": [
    "Schedule focus blocks for deep work",
    "Build on your current 5-day streak",
    "Prioritize high-impact work in mornings"
  ],
  "reasoning": "Based on your recent planning, conversation history, and task patterns",
  "confidence": 0.8,
  "related_logs": [
    "Finished quarterly report",
    "Struggled with focus today",
    "Great momentum this week"
  ]
}
```

---

## Memory Log Categories

### Recommended Categories:

| Category | Best For | Examples |
|----------|----------|----------|
| **work** | Professional tasks and career | Projects, reports, meetings |
| **health** | Physical and mental wellness | Exercise, meditation, sleep |
| **personal** | Personal growth and life | Habits, relationships, hobbies |
| **learning** | Education and skill building | Courses, books, new skills |
| **goals** | Goal tracking and milestones | Targets, achievements, progress |

You can also create custom categories that fit your workflow!

---

## Best Practices

### 1. **Be Specific**
- ✅ "Completed quarterly report 2 days early using new framework"
- ❌ "Did work"

### 2. **Log Consistently**
- Log at least 3-5 times per week for meaningful patterns
- Use `/reflect` for quick daily notes
- Use `/log` for structured observations

### 3. **Use Importance Levels**
- **1-2**: Routine, regular observations
- **3**: Standard accomplishments
- **4-5**: Major achievements or important insights

### 4. **Link Related Tasks**
- When creating logs with `/log`, add `linked_task_ids` for context
- Helps AI understand the relationship between logs and actual tasks

### 5. **Review Regularly**
- Check `/memory` summary weekly
- Use insights from `/suggest` to improve planning
- Look for patterns in high-importance logs

---

## Data Privacy

All memory logs are:
- ✅ **Private**: Only visible to you and the system
- ✅ **Encrypted**: Stored securely in PostgreSQL
- ✅ **Contextual**: Used only for generating your personalized suggestions
- ✅ **Deletable**: Contact support if you need your memory logs deleted

Your data is never shared with third parties or used for training purposes.

---

## Troubleshooting

### Issue: Command not recognized
**Solution:** Make sure you're using the correct format. Try `/memory` to verify the bot is responsive.

### Issue: Not getting suggestions
**Solution:** You need at least 3-5 memory logs in the last 7 days. Start by logging your activities with `/log` or `/reflect`.

### Issue: Missing logs in summary
**Solution:** Logs must be created in the last 7 days to appear in `/memory`. Older logs are preserved but not included in the current summary.

---

## Example Workflow

**Monday Morning:**
```
/log plan work Quarterly planning: focus on 3 major projects
/log health personal Gym routine: start 6am workouts
```

**Wednesday Evening:**
```
/reflect Finished project A early. New framework saved 2 days of work.
```

**Friday Evening:**
```
/memory
(Review your week's progress)

/suggest
(Get recommendations for next week)

/reflect Great week! Maintained 5-day streak, completed 2 major projects.
```

---

## Next Steps

1. **Start logging**: Use `/log` to create your first memory entry
2. **Review patterns**: Check `/memory` weekly to identify trends
3. **Get insights**: Use `/suggest` to discover improvements
4. **Build habits**: Reflect consistently with `/reflect`
5. **Optimize**: Apply suggestions and track improvements

Happy logging! 🚀
