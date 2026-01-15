# Demo Script: Schema Matching System

**Purpose:** Walk through the solution for interviews or stakeholders
**Duration:** 15-20 minutes
**Audience:** Technical decision makers

---

## Demo Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEMO FLOW                                 │
│                                                                  │
│   1. The Problem    →    2. The Solution    →    3. The Value   │
│      (2 min)                 (10 min)               (3 min)     │
│                                                                  │
│   Show pain         Show system working      Show ROI           │
│   German names      Auto-match + review      Learning curve     │
│   Manual effort     Trust profiles           Time savings       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: The Problem (2 minutes)

### Opening Hook

> "Let me show you what we're dealing with. Here's a real database schema from a German dental practice system."

### Show the Pain

Display this table:

| Source Column | What It Means | Variations Seen |
|---------------|---------------|-----------------|
| PATNR | Patient ID | PAT_NR, PATIENTENNR, PAT_ID |
| GEBDAT | Birth Date | GEBURTSDATUM, GEB_DATUM, DOB |
| KASSE | Insurance | VERSICHERUNG, INSURANCE, KASSEN |
| BEMERKUNG | Chart Note | NOTIZ, NOTES, ANMERKUNG |

> "Same business concepts, different names in every database. 15 databases, 500 tables each. That's 7,500 tables to map. Manually."

### Quantify the Problem

> "Currently takes 40-80 hours per client. With 15 clients, that's over 1,000 hours a year of manual mapping. And every person maps differently."

---

## Part 2: The Solution (10 minutes)

### 2.1 Start a Mapping Run (1 min)

> "Here's how it works. We connect to a new client database and start the mapping."

**Show API call:**
```json
POST /api/schema-matching/map
{
  "client_id": "munich_dental",
  "connection_id": "conn_123",
  "trust_profile": "standard"
}
```

**Response:**
```json
{
  "run_id": "run_456",
  "status": "running"
}
```

> "The system is now analyzing the schema in the background."

---

### 2.2 Schema Profiling (2 min)

> "First, it profiles every column. Not just names - statistics, sample values, data types."

**Show profiling output:**

| Table | Column | Type | Null % | Distinct | Sample Values |
|-------|--------|------|--------|----------|---------------|
| PATIENT | PATNR | INT | 0% | 5,234 | 1001, 1002, 1003 |
| PATIENT | GEBDAT | VARCHAR | 2% | 3,891 | 19850315, 19901220 |
| PATIENT | MOBIL | VARCHAR | 94% | 12 | NULL, NULL, +49... |

> "Notice MOBIL is 94% NULL. The system flags that as potentially abandoned - it won't waste time matching it."

---

### 2.3 Similarity Matching (2 min)

> "For each column, we run multiple similarity algorithms against our value bank."

**Show matching for PATNR:**

```
Column: PATNR

Value Bank Lookup:
├─ Exact match: ✓ PATNR → patient_id (seen 12 times)
├─ Fuzzy match: PAT_NR (0.92), PATIENTNR (0.88)
└─ Pattern match: Sequential integers → likely ID

Signals:
├─ Name similarity:    95%
├─ Data type match:    90%
├─ Value pattern:      85%
└─ Historical:         92%

Combined Confidence: 94%
Decision: AUTO-ACCEPT (threshold: 90%)
```

> "94% confidence. With standard trust profile, this auto-accepts. No human needed."

---

### 2.4 Human Review Queue (2 min)

> "But not everything auto-accepts. Here's one that needs review."

**Show uncertain mapping:**

```
Column: BEMERKUNG

Value Bank Lookup:
├─ Exact match: ✗ Not found
├─ Fuzzy match: BEMERK (0.71) → chart_note
└─ Pattern match: Long text strings

Combined Confidence: 72%
Decision: PENDING REVIEW (between 70-90%)
```

**Show review interface:**

| Column | Proposed | Confidence | Sample Values | Action |
|--------|----------|------------|---------------|--------|
| BEMERKUNG | chart_note | 72% | "Patient called", "Checkup OK" | [Approve] [Reject] [Remap] |

> "Human reviewer sees the samples, makes the call. One click. And this decision feeds back into the value bank."

---

### 2.5 Trust Profiles (1 min)

> "Different clients get different profiles."

| Profile | Auto-Accept | Review | Use Case |
|---------|-------------|--------|----------|
| Conservative | ≥99% | ≥80% | First client, critical data |
| Standard | ≥90% | ≥70% | Normal operations |
| Permissive | ≥80% | ≥50% | Trusted, low-risk |

> "Pilot client? Conservative. 10th client with same schema? Permissive. You control the risk."

---

### 2.6 Learning (2 min)

> "Here's the magic. Watch what happens after we approve BEMERKUNG → chart_note."

**Before (Client 1):**
```
BEMERKUNG → chart_note: NOT in value bank
Confidence: 72%
Decision: REVIEW
```

**After approval:**
```
Value bank updated:
+ BEMERKUNG → chart_note (source: munich_dental)
```

**Client 2:**
```
BEMERKUNG → chart_note: FOUND in value bank
Confidence: 95%
Decision: AUTO-ACCEPT
```

> "Client 2 never sees a review for BEMERKUNG. The system learned from Client 1."

---

## Part 3: The Value (3 minutes)

### Show the Learning Curve

| Client | Auto-Match | Review Items | Time |
|--------|------------|--------------|------|
| 1 | 60% | 200 | 8 hours |
| 5 | 80% | 100 | 4 hours |
| 10 | 90% | 50 | 2 hours |
| 15 | 95% | 25 | 1 hour |

> "By client 15, we're at 95% auto-match. One hour instead of 80."

### Show the ROI

| Metric | Manual | Automated | Savings |
|--------|--------|-----------|---------|
| Hours/client | 74 | 7.5 | 90% |
| Annual hours | 1,110 | 112 | 998 hours |
| Annual cost | $111K | $11K | $100K |

> "That's $100,000 per year. The system pays for itself after 20 clients."

### Close Strong

> "And the hidden value: consistency. Every mapping follows the same rules. Full audit trail. Knowledge captured in the value bank, not in someone's head."

---

## Q&A Preparation

### Expected Questions

| Question | Answer |
|----------|--------|
| "What about edge cases?" | "Goes to review queue. Human decides, system learns." |
| "What if it's wrong in production?" | "Audit trail shows exactly what happened. Rollback is one API call." |
| "How long to build?" | "10-12 weeks. MVP with human review at week 6." |
| "What about ML?" | "Phase 4. System works without it. ML pushes from 90% to 95%." |

### Questions to Ask Them

> "What does your current onboarding process look like?"
> "What's the most painful part of schema mapping today?"
> "Have you tried automating this before? What went wrong?"

---

## Demo Environment Setup

### If Doing Live Demo

| Component | Setup |
|-----------|-------|
| Test database | Zone D clean database |
| Value bank | Pre-seeded with 50 patterns |
| API | Running locally or staging |
| Sample client | Ready to map |

### If Doing Slides Only

| Slide | Content |
|-------|---------|
| 1 | Problem statement (German columns) |
| 2 | Solution overview (architecture diagram) |
| 3 | Profiling output |
| 4 | Matching example (PATNR) |
| 5 | Review queue |
| 6 | Trust profiles |
| 7 | Learning curve chart |
| 8 | ROI numbers |

---

## Timing Guide

| Section | Duration | Running Total |
|---------|----------|---------------|
| Problem setup | 2 min | 2 min |
| Start mapping | 1 min | 3 min |
| Schema profiling | 2 min | 5 min |
| Similarity matching | 2 min | 7 min |
| Human review | 2 min | 9 min |
| Trust profiles | 1 min | 10 min |
| Learning | 2 min | 12 min |
| Value/ROI | 3 min | 15 min |
| Q&A buffer | 5 min | 20 min |

---

## Backup Talking Points

### If They're Technical

- Multi-algorithm similarity (Levenshtein, Jaro-Winkler, Jaccard)
- Async processing with Celery
- PostgreSQL for audit, Redis for caching
- Confidence aggregation formula

### If They're Business

- 90% time reduction
- $100K annual savings
- Compound learning value
- Risk control via trust profiles

### If They're Skeptical

- Show Zone D test results
- Reference 15 real databases analyzed
- Explain phased approach (value at each phase)
- Offer to share detailed documentation

---

*Practice the demo. Know your numbers. Let the system do the talking.*
