# Quick Start: Memory Logs & Suggestions 🚀

Get started with memory logging in 5 minutes!

---

## What You Can Do

**Log Your Activity**
- Record task completion, plans, and reflections
- Organize by category (work, health, personal, etc.)
- Mark importance for highlighting key insights

**View Patterns**
- See your 7-day summary by type and category
- Identify productivity trends
- Track what matters most

**Get Suggestions**
- AI generates personalized recommendations
- Based on your logs and conversation history
- Helps improve planning and consistency

---

## Quick Commands

### 1️⃣ Log a Task
```
/log task_note work Finished the quarterly report early!
```
✅ Response: Logged task_note in work: Finished the quarterly report early!

### 2️⃣ Quick Reflection
```
/reflect Today was productive, maintained focus all day
```
✅ Response: Reflection logged: Today was productive...

### 3️⃣ View Your Summary
```
/memory
```
✅ Response: Shows last 7 days with counts by type and category

### 4️⃣ Get AI Suggestions
```
/suggest
```
✅ Response: 💡 5 personalized recommendations based on your data

---

## Command Formats

### /log - Full Structure
```
/log <type> <category> <content>
```

**Types**: task_note, plan, reflection, milestone

**Categories**: work, health, personal, learning, (or your own)

**Examples**:
```
/log task_note work Completed major feature
/log plan health Start morning gym routine
/log reflection personal Learned importance of breaks
/log milestone career Got promoted!
```

### /reflect - Simple Reflection
```
/reflect <your thoughts>
```

**Examples**:
```
/reflect Great day, completed 5 tasks
/reflect Struggled with focus, need more breaks
/reflect Made good progress on learning Python
```

---

## 7-Day Workflow

**Monday Morning**
```
/log plan work Focus on Project X this week
/log plan health Gym 3x this week
```

**Wednesday Evening**
```
/reflect Good progress, stayed consistent
```

**Friday Evening**
```
/memory (check weekly progress)
/suggest (get next week recommendations)
/reflect Completed goals, ready for next week
```

---

## Pro Tips

### 💡 Tip 1: Be Specific
```
✅ /log task_note work Finished API design doc, 2 hours ahead
❌ /log task_note work Did work
```

### 💡 Tip 2: Use Importance
When creating via API:
- **1-2**: Regular observations
- **3**: Standard accomplishments  
- **4**: Important achievements
- **5**: Major milestones

### 💡 Tip 3: Find Patterns
Check `/memory` weekly to notice:
- What types of logs you create most
- Which categories dominate
- Your high-importance entries

### 💡 Tip 4: Act on Suggestions
Use `/suggest` results to:
- Plan next week better
- Avoid past mistakes
- Build on successful patterns

---

## Common Questions

### Q: How often should I log?
**A:** Start with 3-5 logs per week. Daily logging helps most, but quality > quantity.

### Q: What if I forget a detail?
**A:** Logs can include summaries. "/log task_note work Completed features" is fine without specifics.

### Q: Can I edit or delete logs?
**A:** Currently no. Contact support if you need to remove sensitive entries.

### Q: When do suggestions get better?
**A:** After 1-2 weeks of consistent logging, patterns emerge and suggestions improve.

### Q: What if I have no logs?
**A:** Start with `/reflect` for quick entries, then use `/log` for structured logging.

---

## Example Scenarios

### Scenario 1: Building a Habit
```
Day 1: /log task_note health Did morning run - 3 miles
Day 2: /reflect Sore but feeling good about consistency
Day 3: /log task_note health Morning run - easier today
Day 7: /memory → Shows 5 health logs
       /suggest → "You're building momentum, keep it up!"
```

### Scenario 2: Project Tracking
```
Week 1: /log milestone work Started project X
        /log plan work Break into 4 phases
Week 2: /log task_note work Completed phase 1
        /reflect On track for deadline
Week 3: /log task_note work Completed phase 2, ahead of schedule
        /memory → Shows project progress
```

### Scenario 3: Personal Growth
```
/log reflection personal Learning Python this month
/log task_note learning Completed 5 lessons
/reflect Building coding skills for career
/suggest → Get tips on learning pace and goals
```

---

## API Quick Reference

### Create Log (Code)
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/api/memory/log",
    params={"chat_id": "1234567890"},
    json={
        "log_type": "task_note",
        "content": "Completed task",
        "category": "work",
        "importance": 4
    }
)
```

### Get Logs (Code)
```python
response = requests.get(
    "http://localhost:8000/api/v1/api/memory/logs",
    params={
        "chat_id": "1234567890",
        "limit": 10,
        "log_type": "task_note"
    }
)
```

### Get Summary (Code)
```python
response = requests.get(
    "http://localhost:8000/api/v1/api/memory/summary",
    params={"chat_id": "1234567890", "days": 7}
)
```

### Get Suggestions (Code)
```python
response = requests.post(
    "http://localhost:8000/api/v1/api/memory/suggest",
    params={"chat_id": "1234567890"},
    json={"suggestion_type": "planning", "context_days": 7}
)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Command not recognized | Check `/memory` works, verify command format |
| No suggestions | Need 3+ logs in last 7 days, try logging more |
| Logs not in summary | Logs older than 7 days not in current view |
| Bot slow | High usage, please retry in a moment |

---

## Next Steps

1. ✅ Send first log: `/log task_note work Started memory logging`
2. ✅ Send reflection: `/reflect This feature is helpful!`
3. ✅ Check summary: `/memory`
4. ✅ Get suggestions: `/suggest`
5. ✅ Keep logging consistently

---

## Resources

- **Full Guide**: See `MEMORY_LOG_GUIDE.md` for detailed documentation
- **Implementation Details**: See `MEMORY_LOG_IMPLEMENTATION.md`
- **Test Examples**: Check `tests/test_memory_logs.py`

---

## Questions?

Check the troubleshooting section above or review the full `MEMORY_LOG_GUIDE.md` for comprehensive help.

**Happy logging!** 🚀
