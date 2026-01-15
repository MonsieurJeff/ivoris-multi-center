# Interview Questions & Positioning

**Purpose:** Questions to ask them, how to position your solution
**Context:** They rewrote their app due to scalability issues

---

## Part 1: Discovery Questions

### Understanding Their Rewrite

Ask these to understand their pain points:

| Question | What You Learn | How to Position |
|----------|----------------|-----------------|
| "What specifically wasn't scaling - data volume, client count, or code complexity?" | Root cause | Tailor your solution emphasis |
| "How many clients/databases are you managing now?" | Current scale | Show your 15 DB experience |
| "What's the biggest operational pain point today?" | Priority | Lead with that solution |
| "How much time does onboarding a new client take?" | Baseline | Show time savings |

### Understanding Their Current Approach

| Question | What You Learn | Red Flags |
|----------|----------------|-----------|
| "How do you handle schema variations between clients?" | Current solution | Manual = opportunity |
| "Do you have a canonical data model?" | Architecture maturity | If no = bigger project |
| "How do you validate data mappings?" | Quality process | If manual = automation opportunity |
| "What happens when a mapping is wrong?" | Error handling | If no audit = risk |

### Technical Deep Dive

| Question | What You Learn | Shows You |
|----------|----------------|-----------|
| "What's your tech stack for the rewrite?" | Constraints | Can integrate |
| "Are you using any ML/AI currently?" | Sophistication | Where to add value |
| "How do you handle German column names?" | Domain knowledge | You understand the problem |
| "What's your approach to human review?" | Process maturity | Trust profile relevance |

---

## Part 2: Positioning Strategies

### If They Say: "We do it manually"

**Your response:**
> "Manual mapping doesn't scale. With 15+ clients, you need automation. I've designed a system with a learning value bank - each verified mapping makes the next client faster. By client 10, you're at 90%+ auto-match."

**Key points:**
- Value bank compounds knowledge
- Human review only for uncertain cases
- Audit trail for compliance

### If They Say: "We built custom rules"

**Your response:**
> "Rules work until they don't. German column names have too many variations - PATNR, PAT_NR, PATIENTENNUMMER. Instead of writing rules for every case, we use similarity algorithms with learned patterns. The system discovers rules from data."

**Key points:**
- Fuzzy matching handles variations
- Learning > hardcoding
- Weights tuned from real data

### If They Say: "We're considering ML"

**Your response:**
> "ML is powerful but you need the foundation first. Start with similarity matching and a value bank - that gets you to 85%. Then add ML embeddings or classification to push to 95%. ML without ground truth data is guessing."

**Key points:**
- ML is Phase 4, not Phase 1
- Need verified mappings for training
- System works without ML; ML enhances

### If They Say: "We need it fast"

**Your response:**
> "Phase 1-2 gives you core matching in 4 weeks. You can onboard clients with human review while building the learning layer. Incremental delivery - value at each phase."

**Key points:**
- Phased approach
- MVP is usable
- Don't need everything for first client

### If They Say: "How do we know it's correct?"

**Your response:**
> "Trust profiles. Start conservative - auto-accept only at 99% confidence. Critical fields like patient_id always require human review. Full audit trail for every decision. You control the risk tolerance."

**Key points:**
- Configurable thresholds
- Critical entity protection
- Audit trail for compliance

---

## Part 3: Questions That Show Senior Thinking

Ask these to demonstrate your experience:

### Architecture Questions

> "When you rewrote, did you separate the schema mapping concern from the core application? I've found it works better as an independent service."

*Shows: You think in services, separation of concerns*

> "How do you handle schema changes after initial mapping? Incremental re-mapping or full refresh?"

*Shows: You think about maintenance, not just initial build*

### Scale Questions

> "What's your strategy for value bank growth? At some point you need to prune low-confidence patterns."

*Shows: You think about long-term system health*

> "Have you considered federated value banks - sharing patterns across client types while keeping client-specific data isolated?"

*Shows: You think about data architecture*

### Process Questions

> "Who reviews the mappings today? Domain experts or developers? That affects the UI you need."

*Shows: You think about users, not just code*

> "What's your feedback loop when a mapping turns out to be wrong in production?"

*Shows: You think about continuous improvement*

---

## Part 4: Turning Their Challenges Into Your Strengths

| Their Challenge | Your Solution | Document Reference |
|-----------------|---------------|-------------------|
| "Too many variations" | Multi-algorithm similarity (Levenshtein + Jaro-Winkler + Jaccard) | TECHNICAL_SOLUTION.md |
| "Can't trust automation" | Trust profiles with configurable thresholds | TECHNICAL_SOLUTION.md |
| "No time for ML" | System works without ML; add later | IMPLEMENTATION_ROADMAP.md |
| "Need audit trail" | Built-in audit logging for all decisions | TECHNICAL_SOLUTION.md |
| "Slow onboarding" | Learning value bank - each client faster | IMPLEMENTATION_ROADMAP.md |
| "German is hard" | Tested against real German schemas | DATABASE_SIMULATOR.md |

---

## Part 5: Red Flags to Watch For

### They Might Not Be Ready If:

| Red Flag | What It Means | Your Response |
|----------|---------------|---------------|
| "We need it in 2 weeks" | Unrealistic expectations | "MVP in 4 weeks, full system in 10" |
| "We don't have a canonical model" | Bigger problem than matching | "That's step 1 - define the target" |
| "We want 100% automation" | Don't understand the problem | "99% with human safety net is realistic" |
| "We'll figure out testing later" | Quality issues ahead | "Test infrastructure is Phase 1" |

### Questions That Reveal Maturity

| Question | Good Answer | Concerning Answer |
|----------|-------------|-------------------|
| "How do you handle edge cases?" | "Human review queue" | "We fix them in code" |
| "What's your rollback strategy?" | "We can revert mappings" | "We haven't thought about it" |
| "How do you measure accuracy?" | "We track false positives" | "Users tell us when it's wrong" |

---

## Part 6: Closing Strong

### Your Summary Statement

> "I've worked with 15 real databases with German column names - PATNR, GEBDAT, KASSEN. I've designed a system that learns from each client, uses configurable trust profiles for risk management, and includes full audit trails. The roadmap is phased so you get value early while building toward full automation."

### Your Ask

> "I'd love to understand more about your specific challenges. Could you walk me through a recent client onboarding that was painful?"

*This shows: You're solution-oriented, you listen, you care about their problems*

### Follow-Up Offer

> "I have detailed documentation - implementation roadmap, technical architecture, acceptance criteria. Happy to share if it would be helpful for your evaluation."

*This shows: You're prepared, professional, thorough*

---

## Quick Reference: Interview Flow

```
1. DISCOVER
   ├─ What broke? (their rewrite trigger)
   ├─ Current scale? (15 clients context)
   └─ Biggest pain? (where to focus)

2. POSITION
   ├─ Match their pain to your solution
   ├─ Show you understand the domain
   └─ Demonstrate senior thinking

3. DEMONSTRATE
   ├─ Reference your experience (15 databases)
   ├─ Explain phased approach
   └─ Show you've thought about edge cases

4. CLOSE
   ├─ Summarize your fit
   ├─ Ask about their specific challenges
   └─ Offer to share documentation
```

---

*Preparation beats improvisation. Know your material, but listen to their specific needs.*
