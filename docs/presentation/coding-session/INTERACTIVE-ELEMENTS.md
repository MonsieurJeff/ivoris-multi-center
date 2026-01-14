# Interactive Elements

**Audience engagement points throughout the session**

---

## Why Interact?

- Keeps attention during 55 minutes
- Validates understanding
- Makes it memorable
- Gives you micro-breaks

---

## Interaction Points

### 1. Opening (0:00)

**Ask:**
> "Quick show of hands - who has worked with SQL Server before?"

**Follow-up based on response:**
- Many hands: "Great, some of this will be familiar"
- Few hands: "No problem, I'll explain as we go"

---

### 2. After Docker Setup (10:00)

**Ask:**
> "Why do you think we use Docker instead of installing SQL Server directly?"

**Expected answers:**
- Portability
- Isolation
- Easy to reset

**Your response:**
> "Exactly - and it means you can follow along on Mac, Windows, or Linux with the same commands."

---

### 3. During Schema Exploration (15:00)

**Ask:**
> "Looking at these table names - KARTEI, KASSE, LEISTUNG, PATIENT - which one do you think contains the daily chart entries?"

**Let them guess, then reveal:**
> "KARTEI means 'chart' or 'index card' in German - that's our main table."

---

### 4. Before Finding Insurance (20:00)

**Ask:**
> "The customer wants 'insurance status'. Looking at our tables, where do you think that information lives?"

**Hint if needed:**
> "It's not directly on the patient record..."

**Reveal:**
> "It's in KASSE, linked through PATIENT. This is why we need JOINs."

---

### 5. Before Building Query (25:00)

**Ask:**
> "If we need data from KARTEI, PATIENT, and KASSE - how many JOINs do we need?"

**Answer:**
> "Two JOINs - KARTEI to PATIENT, then PATIENT to KASSE."

---

### 6. After STRING_AGG (35:00)

**Ask:**
> "What happens if a patient has no services that day? What does STRING_AGG return?"

**Answer:**
> "NULL - which is why we wrap it in ISNULL() to get an empty string instead."

---

### 7. Before Python Script (40:00)

**Ask:**
> "We have a working SQL query. What are the benefits of wrapping it in Python instead of just running it manually?"

**Expected answers:**
- Automation
- Error handling
- File output
- Logging

---

### 8. Before Cron (50:00)

**Ask:**
> "What time of day would you run this extraction? Why?"

**Discussion points:**
- Early morning (before clinic opens)
- After business hours (data complete for the day)
- Avoid peak hours

---

## Quick Polls

### Poll 1: Experience Level
> "On a scale of 1-5, how comfortable are you with SQL? Hold up fingers."

Use this to calibrate your pace.

### Poll 2: Output Preference
> "If you were receiving this data, would you prefer JSON or CSV?"

Usually split - validates why we support both.

### Poll 3: Deployment
> "How would you deploy this in production? Cron? Docker? Cloud function?"

Good discussion starter.

---

## Think-Pair-Share

For longer pauses (if you need to fix something):

> "Take 30 seconds to discuss with your neighbor: what's one challenge you'd expect when extracting data from a legacy system?"

Common answers:
- Poor documentation
- Inconsistent data
- No test environment
- German/localized column names

---

## Live Challenges

### Mini-Challenge 1 (during exploration)
> "Can you guess what GEBDAT means?" (Geburtsdatum = birth date)

### Mini-Challenge 2 (during query building)
> "What would happen if we used JOIN instead of LEFT JOIN for KASSE?"
> (Answer: We'd lose patients without insurance)

### Mini-Challenge 3 (during script)
> "Why do we use ensure_ascii=False in json.dump()?"
> (Answer: To preserve German characters like ü, ö, ä)

---

## Reaction Prompts

After showing something works:

> "Pretty cool, right? [pause for reaction]"

After a complex query:

> "Does this make sense so far? Any questions before we move on?"

After an error (if one happens):

> "Ah, let's debug this together. What do you think went wrong?"

---

## Engagement Recovery

If audience seems disengaged:

1. **Change pace:** "Let me show you the end result first, then we'll see how we got there"

2. **Tell a story:** "This reminds me of a time when..."

3. **Make it relevant:** "Imagine you receive a database like this tomorrow..."

4. **Take a break:** "Let's pause for questions"

---

## Closing Interaction

**Ask:**
> "What was the most useful thing you learned today?"

Or:

> "What would you do differently if you were building this?"

---

## Notes

- Wait for responses (silence is okay)
- Acknowledge all answers positively
- Don't call on people directly (can be uncomfortable)
- If no one answers, answer your own question and move on
