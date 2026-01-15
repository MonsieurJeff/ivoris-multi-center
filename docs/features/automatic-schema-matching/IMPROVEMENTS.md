# Possible Improvements

**Architecture:** MCP-Native Agent
**Status:** Backlog

---

## Overview

This document captures improvement ideas for the MCP-native schema matching agent, organized by priority.

### Priority Legend

| Priority | Meaning | When to Consider |
|----------|---------|------------------|
| **P0** | Critical | Before production |
| **P1** | High | After initial rollout |
| **P2** | Medium | Based on user feedback |
| **P3** | Low | Nice to have |

---

## 1. MCP Server Enhancements

### 1.1 Database Server (P1)

**Parallel Sampling**
```python
# Current: Sequential column sampling
for column in columns:
    samples = await sample_column(column)

# Improved: Parallel sampling
samples = await asyncio.gather(*[
    sample_column(col) for col in columns
])
```

**Smart Sampling**
- Stratified sampling (common + rare + edge values)
- Detect patterns in samples (dates, codes, free text)
- Cache samples across agent runs

**Schema Change Detection**
- Hash schema structure
- Detect new/modified/deleted columns
- Incremental re-mapping

---

### 1.2 Value Bank Server (P1)

**Fuzzy Matching Improvements**
- Multiple algorithms (Levenshtein, Jaro-Winkler, Soundex)
- Language-aware matching (German compound words)
- Abbreviation expansion (PATNR → PATIENT_NUMMER)

**Federated Value Banks**
```
┌─────────────────────────────────────────────────────────────┐
│                  FEDERATED VALUE BANKS                       │
│                                                              │
│    ┌───────────┐    ┌───────────┐    ┌───────────┐         │
│    │  German   │    │   Swiss   │    │  Austrian │         │
│    │  Server   │    │   Server  │    │   Server  │         │
│    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘         │
│          └────────────────┴────────────────┘                 │
│                           │                                  │
│                    Agent queries all                        │
└─────────────────────────────────────────────────────────────┘
```

**Value Confidence Decay**
- Values used frequently = higher confidence
- Values not seen in 12 months = lower confidence
- Automatic pruning of low-confidence values

---

### 1.3 Review Server (P2)

**Bulk Review Actions**
```yaml
tools:
  - name: bulk_approve
    description: "Approve multiple similar mappings at once"
    parameters:
      pattern: "PATNR% → patient_id"
      mappings: [id1, id2, id3]
```

**Review Prioritization**
- Critical entities first (patient_id, insurance_id)
- Group similar mappings
- Show confidence distribution

**Async Review Flow**
- Agent continues with other mappings while waiting
- Resume from where it left off
- Partial results available immediately

---

## 2. Agent Improvements

### 2.1 Prompt Engineering (P1)

**Domain-Specific Prompts**
```yaml
prompts:
  dental_practice:
    system: "You are a dental practice database expert..."
    examples:
      - column: "PATNR"
        entity: "patient_id"
        reasoning: "Common German abbreviation..."

  general_healthcare:
    system: "You are a healthcare database expert..."
```

**Few-Shot Examples**
- Include verified mappings as examples in prompt
- Adapt examples based on database language/region

**Chain-of-Thought**
- Explicit reasoning steps
- Self-verification before proposing

---

### 2.2 Multi-Agent Architecture (P3)

```
┌─────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT SYSTEM                        │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               COORDINATOR AGENT                      │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │                               │
│          ┌───────────────────┼───────────────────┐          │
│          ▼                   ▼                   ▼          │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐   │
│   │  EXPLORER  │      │  MATCHER   │      │  VALIDATOR │   │
│   │   AGENT    │      │   AGENT    │      │   AGENT    │   │
│   └────────────┘      └────────────┘      └────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Parallel table exploration
- Specialized agents for different domains
- Better separation of concerns

---

### 2.3 Confidence Calibration (P1)

**Problem:** Agent confidence may not match actual accuracy.

**Solution:** Calibrate based on historical accuracy.

```python
def calibrate_confidence(raw_confidence, entity_type):
    # Historical accuracy for this entity type
    historical = get_historical_accuracy(entity_type)

    # Platt scaling
    calibrated = platt_scale(raw_confidence, historical)

    return calibrated
```

---

## 3. Security & Compliance

### 3.1 PII Detection (P1)

**Automatic Masking**
```python
def mask_samples(values):
    masked = []
    for v in values:
        if looks_like_email(v):
            masked.append("****@****.***")
        elif looks_like_phone(v):
            masked.append("+** *** ****")
        else:
            masked.append(v)
    return masked
```

**PII Types:**
- Email addresses
- Phone numbers
- Names (NER-based)
- National IDs
- Credit card numbers

---

### 3.2 Audit Trail (P1)

**Comprehensive Logging**
```python
@dataclass
class AuditEntry:
    timestamp: datetime
    run_id: str
    action: str  # "proposed", "accepted", "rejected", "flagged"
    entity: str
    confidence: float
    reasoning: str
    decided_by: str  # "agent" or user_id
    previous_state: dict
    new_state: dict
```

**Queries:**
- "Who approved this mapping?"
- "What changed in the last 24 hours?"
- "Show all agent decisions for client X"

---

## 4. Performance

### 4.1 Caching (P1)

| Layer | What to Cache | TTL | Storage |
|-------|---------------|-----|---------|
| **Schema metadata** | Table/column info | Until change detected | Redis |
| **Column samples** | Sample values | 24 hours | Redis |
| **Value bank lookups** | Match results | 1 hour | In-memory |
| **Agent context** | Conversation state | Session | Memory |

---

### 4.2 Batch Operations (P1)

**Batch Value Bank Checks**
```python
# Current: N calls
for column in columns:
    result = check_column_name(column)

# Improved: 1 call
results = check_column_names_batch(columns)
```

**Expected improvement:** 5-10x faster for large schemas.

---

## 5. User Experience

### 5.1 Progress Visibility (P1)

**Real-time Updates**
```json
{
  "run_id": "abc123",
  "status": "running",
  "progress": {
    "tables_total": 50,
    "tables_complete": 23,
    "current_table": "KARTEI",
    "mappings_proposed": 145,
    "pending_reviews": 12
  },
  "agent_status": "Analyzing column BEMERKUNG..."
}
```

---

### 5.2 Natural Language Interface (P2)

**Interactive Mapping**
```
User: "Map the PATIENT table"
Agent: "I found 12 columns. PATNR looks like patient_id (99% confidence).
        BEMERKUNG might be chart_note but I'm only 75% sure. Should I proceed?"
User: "Yes, BEMERKUNG is chart_note"
Agent: "Got it. I'll remember that for future databases."
```

---

### 5.3 Comparison View (P2)

**Cross-Database View**
```
┌─────────────────────────────────────────────────────────────┐
│ Entity: patient_id                                           │
├─────────────────────────────────────────────────────────────┤
│ Center      │ Column Name  │ Type    │ Confidence           │
├─────────────────────────────────────────────────────────────┤
│ Munich      │ PATNR        │ INT     │ 99%                  │
│ Hamburg     │ PATIENT_NR   │ INT     │ 95%                  │
│ Vienna      │ PAT_ID       │ VARCHAR │ 92%                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Future Considerations

### 6.1 Self-Hosted LLM (P3)

**When to consider:**
- Data sovereignty requirements
- High volume (cost savings at scale)
- Offline operation

**Options:**
- Llama 3
- Mistral
- Fine-tuned smaller models

---

### 6.2 Cross-Language Support (P3)

**Beyond German/English:**
- French: `NOM_PATIENT`, `DATE_NAISSANCE`
- Spanish: `NOMBRE_PACIENTE`, `FECHA_NACIMIENTO`
- Italian: `NOME_PAZIENTE`, `DATA_NASCITA`

**Implementation:** Language detection + localized value banks.

---

### 6.3 Schema Evolution Tracking (P3)

**Track changes over time:**
```
Timeline:
├─ 2024-01 Initial mapping (v1)
├─ 2024-03 Added PATIENT.EMAIL (v2)
├─ 2024-06 Renamed DELKZ → IS_DELETED (v3)
└─ 2024-09 Dropped KARTEI.FAX (v4)
```

---

## Summary: Priority Roadmap

### Before Production (P0)
*No P0 items - MCP architecture is ready for implementation*

### After Initial Rollout (P1)
1. Database server: Parallel sampling, caching
2. Value bank: Fuzzy matching improvements
3. Agent: Confidence calibration
4. Security: PII detection, audit trail
5. Performance: Caching layer
6. UX: Progress visibility

### Based on User Feedback (P2)
7. Review server: Bulk actions, prioritization
8. Agent: Domain-specific prompts
9. UX: Natural language interface, comparison view

### Nice to Have (P3)
10. Multi-agent architecture
11. Self-hosted LLM
12. Cross-language support
13. Schema evolution tracking

---

## What Changed from Pipeline Design

Many improvements from the original `IMPROVEMENTS.md` are no longer needed because MCP handles them:

| Original Improvement | Status |
|---------------------|--------|
| Pipeline orchestration | **Eliminated** - Agent handles flow |
| Phase state machine | **Eliminated** - No rigid phases |
| Complex service layers | **Eliminated** - 3 MCP servers |
| Hardcoded thresholds | **Eliminated** - Agent reasoning |
| Review queue logic | **Simplified** - MCP Review Server |

See [archive/pipeline-design/](archive/pipeline-design/) for the original design.

---

## References

- [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) - Current architecture
- [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) - Test scenarios
- [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) - Test infrastructure

---

*Updated: 2024-01-15*
*Status: Backlog*
