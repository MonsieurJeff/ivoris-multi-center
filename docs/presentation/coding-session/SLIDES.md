# Slide Transitions

**Simple slides for section transitions**

Use these as visual breaks between live coding sections.

---

## Slide 1: Title

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                                                            │
│           IVORIS DAILY EXTRACTION PIPELINE                 │
│                                                            │
│              Building a Data Pipeline                      │
│              from Database to Automation                   │
│                                                            │
│                                                            │
│                     [Your Name]                            │
│                     [Date]                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Today we'll build a complete data extraction pipeline from scratch."

---

## Slide 2: The Challenge

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                    THE CHALLENGE                           │
│                                                            │
│     Extract daily chart entries from dental software       │
│                                                            │
│     ┌─────────────────────────────────────────────┐        │
│     │  Datum  │  Pat-ID  │  Insurance  │  Entry  │        │
│     │  Date   │  Patient │  Status     │  Notes  │        │
│     └─────────────────────────────────────────────┘        │
│                         +                                  │
│                  Service Codes                             │
│                                                            │
│     Output: JSON / CSV   │   Schedule: Daily               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "The customer needs these 5 fields extracted every day."

---

## Slide 3: Our Approach

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                    OUR APPROACH                            │
│                                                            │
│     1. Setup    →  Docker + SQL Server                     │
│                                                            │
│     2. Explore  →  Discover the schema                     │
│                                                            │
│     3. Query    →  Build extraction SQL                    │
│                                                            │
│     4. Script   →  Python automation                       │
│                                                            │
│     5. Schedule →  Cron job                                │
│                                                            │
│                                                            │
│                   ~55 minutes                              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "We'll tackle this in 5 steps, building up incrementally."

---

## Slide 4: Section - Setup

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                                                            │
│                                                            │
│                     STEP 1 & 2                             │
│                                                            │
│                  DATABASE SETUP                            │
│                                                            │
│              Docker + SQL Server + Test Data               │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Let's start by getting our database environment running."

---

## Slide 5: Section - Exploration

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                                                            │
│                                                            │
│                     STEP 3 & 4                             │
│                                                            │
│               DATABASE EXPLORATION                         │
│                                                            │
│              Discovering the Schema                        │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Now the detective work - what's in this database?"

---

## Slide 6: Schema Discovery

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                  WHAT WE FOUND                             │
│                                                            │
│     KASSE (Insurance)     LEISTUNG (Services)              │
│         │                      │                           │
│         │ KASSEID              │ PATIENTID + DATUM         │
│         ▼                      ▼                           │
│     PATIENT ◄──────────── KARTEI (Chart)                   │
│         PATIENTID              PATIENTID                   │
│                                                            │
│                                                            │
│     4 tables, 3 relationships, 1 query                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Four tables, with PATIENT at the center. Now let's build the query."

---

## Slide 7: Section - Query Building

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                                                            │
│                                                            │
│                       STEP 5                               │
│                                                            │
│               BUILD THE QUERY                              │
│                                                            │
│              Step by Step SQL                              │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Now we'll build the extraction query incrementally."

---

## Slide 8: Section - Automation

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                                                            │
│                                                            │
│                     STEP 5b & 6                            │
│                                                            │
│                   AUTOMATION                               │
│                                                            │
│              Python Script + Cron Job                      │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Finally, let's automate this to run every day without intervention."

---

## Slide 9: Summary

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                    WHAT WE BUILT                           │
│                                                            │
│     ✓ Docker environment for SQL Server                    │
│                                                            │
│     ✓ Schema exploration techniques                        │
│                                                            │
│     ✓ Multi-table extraction query                         │
│                                                            │
│     ✓ Python script with JSON/CSV output                   │
│                                                            │
│     ✓ Automated daily execution                            │
│                                                            │
│                                                            │
│              Questions?                                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "And that's a complete pipeline from database to daily automation. Questions?"

---

## Slide 10: Resources

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                     RESOURCES                              │
│                                                            │
│                                                            │
│     Repository:    [Your repo URL]                         │
│                                                            │
│     Documentation: docs/presentation/coding-session/       │
│                                                            │
│     Cheatsheet:    CHEATSHEET.md                           │
│                                                            │
│     Contact:       [Your email]                            │
│                                                            │
│                                                            │
│                    Thank you!                              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Say:** "Here are the resources - feel free to reach out with questions."

---

## How to Use These Slides

### Option 1: Markdown Viewer
Display this file in a markdown viewer that supports presentation mode.

### Option 2: Copy to Slides App
Copy each slide's ASCII art into Google Slides / PowerPoint / Keynote.

### Option 3: Terminal
Use a terminal-based presentation tool like `slides` or `lookatme`:
```bash
# Install
pip install lookatme

# Run
lookatme SLIDES.md
```

### Option 4: Just Narrate
Use these as mental markers - no actual slides needed.

---

## Timing for Slides

| Slide | Show At | Duration |
|-------|---------|----------|
| 1. Title | 0:00 | 30 sec |
| 2. Challenge | 0:30 | 1 min |
| 3. Approach | 1:30 | 1 min |
| 4. Setup | 2:30 | (transition) |
| 5. Exploration | 10:00 | (transition) |
| 6. Schema | 20:00 | 1 min |
| 7. Query | 25:00 | (transition) |
| 8. Automation | 40:00 | (transition) |
| 9. Summary | 50:00 | 2 min |
| 10. Resources | 53:00 | 1 min |
