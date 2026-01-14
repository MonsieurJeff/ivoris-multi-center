# Possible Improvements

**Purpose:** Document potential enhancements, future considerations, and ideas for the Automatic Schema Matching feature.
**Status:** Backlog / Future Consideration

---

## Overview

This document captures improvement ideas organized by category and priority. These are not commitments—they're options to consider as the feature matures.

### Priority Legend

| Priority | Meaning | When to Consider |
|----------|---------|------------------|
| **P0** | Critical | Before production |
| **P1** | High | After initial rollout |
| **P2** | Medium | Based on user feedback |
| **P3** | Low | Nice to have |

---

## 1. Open Technical Decisions

These questions from the design phase need resolution before or during implementation.

### 1.1 Background Job Framework (P0)

| Option | Pros | Cons |
|--------|------|------|
| **Celery + Redis** | Industry standard, battle-tested, good monitoring | Complex setup, Redis dependency |
| **RQ (Redis Queue)** | Simpler than Celery, Python-native | Less features, still needs Redis |
| **Dramatiq** | Modern, good defaults, multiple backends | Smaller community |
| **Built-in threading** | No dependencies, simple | No persistence, no distributed |
| **APScheduler** | Good for scheduled tasks | Not ideal for job queues |

**Recommendation:** Celery for enterprise, RQ for simpler deployments.

**Decision criteria:**
- Do we need distributed workers? → Celery
- Single server, simple queues? → RQ
- No Redis available? → Dramatiq with RabbitMQ

---

### 1.2 LLM Integration (P0)

| Option | Pros | Cons |
|--------|------|------|
| **Direct API (OpenAI/Anthropic)** | Simple, no abstraction | Vendor lock-in |
| **LangChain** | Unified interface, tools ecosystem | Complexity, fast-moving target |
| **LiteLLM** | Lightweight, multi-provider | Less features than LangChain |
| **Custom Gateway** | Full control, caching, logging | Build & maintain overhead |

**Recommendation:** LiteLLM for provider abstraction + custom caching layer.

**Key requirements:**
- Provider switching (OpenAI ↔ Anthropic ↔ local)
- Response caching (same column = same classification)
- Cost tracking
- Rate limiting
- Fallback handling

---

### 1.3 Database Architecture (P0)

| Option | Pros | Cons |
|--------|------|------|
| **Same DB, same schema** | Simple, transactional consistency | Table pollution, migrations |
| **Same DB, separate schema** | Isolation, cleaner | Still coupled |
| **Separate DB** | Full isolation, independent scaling | Complexity, cross-DB queries |

**Recommendation:** Same DB, separate schema (`schema_matching.*` tables).

**Tables needed:**
```
schema_matching.pipeline_runs
schema_matching.column_profiles
schema_matching.classifications
schema_matching.mappings
schema_matching.value_bank_entries
schema_matching.review_queue
schema_matching.audit_log
```

---

### 1.4 Caching Strategy (P1)

| Layer | What to Cache | TTL | Storage |
|-------|---------------|-----|---------|
| **LLM responses** | Classification results | 7 days | Redis |
| **Column profiles** | Extracted metadata | Until schema change | DB |
| **Value bank lookups** | Frequent queries | 1 hour | In-memory |
| **Similarity scores** | Name comparisons | Session | In-memory |

**Cache invalidation triggers:**
- Schema change detected → Clear column profiles
- Value bank updated → Clear value bank cache
- Manual override → Clear specific classification

---

### 1.5 Notification System (P2)

| Channel | Use Case | Priority |
|---------|----------|----------|
| **In-app** | Review queue alerts | P1 |
| **Email** | Pipeline completion, errors | P1 |
| **Slack/Teams** | Real-time alerts | P2 |
| **Webhook** | Integration with external systems | P2 |

**Notification events:**
- Pipeline started / completed / failed
- Review items added to queue
- High-priority items needing attention
- Trust threshold violations
- Adaptive trust changes

---

## 2. Algorithm Improvements

### 2.1 Confidence Calibration (P1)

**Problem:** LLM confidence scores may not reflect actual accuracy.

**Improvement:** Calibrate confidence based on historical accuracy.

```python
# Current: Raw LLM confidence
confidence = llm_response.confidence  # 0.85

# Improved: Calibrated confidence
calibrated = calibrate(
    raw_confidence=0.85,
    entity_type="insurance_name",
    historical_accuracy=0.78  # From feedback loop
)
# Result: 0.78 (adjusted down based on history)
```

**Implementation:**
1. Track prediction vs actual (after human review)
2. Build calibration curves per entity type
3. Apply Platt scaling or isotonic regression
4. Update calibration weekly

---

### 2.2 Active Learning (P2)

**Problem:** Human reviewers waste time on obvious cases.

**Improvement:** Prioritize review items that maximize learning.

```
┌─────────────────────────────────────────────────────────────┐
│                    ACTIVE LEARNING LOOP                      │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Uncertain │───►│  Human   │───►│  Retrain │              │
│  │  Cases    │    │  Review  │    │  Model   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       ▲                                  │                   │
│       └──────────────────────────────────┘                   │
│                                                              │
│  Priority = uncertainty × impact × diversity                 │
└─────────────────────────────────────────────────────────────┘
```

**Prioritization formula:**
```python
priority = (
    uncertainty_score *      # How unsure is the model?
    entity_importance *      # How critical is this entity?
    diversity_bonus          # Is this a new pattern?
)
```

---

### 2.3 Ensemble Classification (P2)

**Problem:** Single LLM may have blind spots.

**Improvement:** Combine multiple classification signals.

| Signal | Weight | Source |
|--------|--------|--------|
| LLM classification | 40% | GPT-4 / Claude |
| Name similarity | 25% | Levenshtein, Jaro-Winkler |
| Value pattern matching | 20% | Regex, value bank |
| Table context | 15% | FK relationships, co-occurrence |

**Ensemble decision:**
```python
final_confidence = weighted_average([
    (llm_confidence, 0.40),
    (name_similarity, 0.25),
    (value_match, 0.20),
    (context_score, 0.15)
])
```

---

### 2.4 Incremental Profiling (P1)

**Problem:** Full re-profiling is expensive for large schemas.

**Improvement:** Only profile changed columns.

```python
# Detect changes
changes = detect_schema_changes(
    previous_hash=last_profile.schema_hash,
    current_hash=current_schema_hash()
)

# Profile only changes
if changes.new_columns:
    profile_columns(changes.new_columns)
if changes.modified_columns:
    reprofile_columns(changes.modified_columns)
if changes.deleted_columns:
    mark_deleted(changes.deleted_columns)
```

**Change detection:**
- Column added → Full profile
- Column type changed → Re-profile
- Data changed significantly → Re-sample values
- Column deleted → Mark inactive

---

## 3. User Experience Improvements

### 3.1 Review Workflow Enhancements (P1)

**Current:** Simple approve/reject actions.

**Improved:**

| Action | Description | Keyboard |
|--------|-------------|----------|
| Approve | Accept mapping | `A` |
| Reject | Reject mapping | `R` |
| Skip | Review later | `S` |
| Bulk approve | Approve similar | `Shift+A` |
| Split | One column → multiple entities | `P` |
| Merge | Multiple columns → one entity | `M` |
| Add note | Attach explanation | `N` |

**Smart grouping:**
```
┌─────────────────────────────────────────────────────────────┐
│ Review Queue - Grouped by Similarity                         │
├─────────────────────────────────────────────────────────────┤
│ ▼ Patient ID variants (5 items)                    [Bulk ✓] │
│   ├─ PATNR → patient_id (95%)                              │
│   ├─ PATIENT_NR → patient_id (92%)                         │
│   ├─ PAT_ID → patient_id (90%)                             │
│   ├─ PATIENTENNUMMER → patient_id (88%)                    │
│   └─ P_NR → patient_id (75%)                               │
│                                                              │
│ ▼ Insurance name variants (3 items)                [Bulk ✓] │
│   ├─ KASSEN_NAME → insurance_name (91%)                    │
│   ├─ VERSICHERUNG → insurance_name (85%)                   │
│   └─ KK_BEZEICHNUNG → insurance_name (82%)                 │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.2 Dashboard & Analytics (P2)

**Metrics to display:**

| Metric | Description | Visualization |
|--------|-------------|---------------|
| Auto-match rate | % mapped without review | Gauge |
| Review backlog | Items pending review | Count + trend |
| Value bank growth | New entries over time | Line chart |
| Accuracy trend | Correct predictions over time | Line chart |
| Time to onboard | Days from start to production | Bar chart |
| Cost per client | LLM + human review costs | Table |

**Dashboard sections:**
1. **Overview:** Key metrics at a glance
2. **Pipeline status:** Running / completed / failed pipelines
3. **Review queue:** Pending items by priority
4. **Learning progress:** Value bank growth, accuracy improvement
5. **Cost tracking:** LLM calls, review time

---

### 3.3 Comparison View (P2)

**Problem:** Hard to see differences across databases.

**Improvement:** Side-by-side comparison view.

```
┌─────────────────────────────────────────────────────────────┐
│ Column Comparison: patient_id                                │
├─────────────────────────────────────────────────────────────┤
│ Center      │ Column Name  │ Type    │ Samples              │
├─────────────────────────────────────────────────────────────┤
│ Munich      │ PATNR        │ INT     │ 1001, 1002, 1003     │
│ Hamburg     │ PATIENT_NR   │ INT     │ 5001, 5002, 5003     │
│ Frankfurt   │ patient_id   │ BIGINT  │ 10001, 10002, 10003  │
│ Vienna      │ PAT_ID       │ VARCHAR │ "P-001", "P-002"     │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                     [Standardize All]
```

---

## 4. Architecture Improvements

### 4.1 Event-Driven Architecture (P2)

**Current:** Synchronous pipeline execution.

**Improved:** Event-driven with message queue.

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN PIPELINE                     │
│                                                              │
│  Pipeline    ──►  Message   ──►  Workers                    │
│  Trigger          Queue          (Consumers)                │
│                                                              │
│  Events:                                                     │
│  • pipeline.started                                         │
│  • phase.profiling.completed                                │
│  • phase.classification.completed                           │
│  • review.item.created                                      │
│  • review.item.resolved                                     │
│  • pipeline.completed                                       │
│  • pipeline.failed                                          │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Decoupled components
- Easy to add new consumers (logging, notifications, analytics)
- Better error handling and retry logic
- Horizontal scaling

---

### 4.2 Plugin Architecture for Validators (P2)

**Current:** Hardcoded validation rules.

**Improved:** Pluggable validators.

```python
# validators/base.py
class Validator(ABC):
    @abstractmethod
    def validate(self, column_profile, mapping) -> ValidationResult:
        pass

# validators/insurance_validator.py
class InsuranceValidator(Validator):
    def validate(self, column_profile, mapping):
        if mapping.entity == "insurance_name":
            return self.check_known_insurances(column_profile.sample_values)
        return ValidationResult.not_applicable()

# Registration
validator_registry.register("insurance", InsuranceValidator())
validator_registry.register("date_format", DateFormatValidator())
validator_registry.register("phone_format", PhoneValidator())
```

**Benefits:**
- Easy to add domain-specific validators
- Customers can add custom validators
- A/B testing of validation strategies

---

### 4.3 Multi-Tenant Isolation (P1)

**Current:** Single-tenant design.

**Improved:** Multi-tenant with isolation options.

| Isolation Level | Description | Use Case |
|-----------------|-------------|----------|
| **Shared** | Same DB, tenant_id column | SaaS, cost-effective |
| **Schema** | Separate schema per tenant | Moderate isolation |
| **Database** | Separate DB per tenant | Enterprise, compliance |

**Implementation:**
```python
class TenantContext:
    tenant_id: str
    isolation_level: IsolationLevel

    def get_value_bank(self):
        if self.isolation_level == IsolationLevel.SHARED:
            return shared_value_bank.filter(tenant_id=self.tenant_id)
        else:
            return tenant_specific_value_bank(self.tenant_id)
```

---

## 5. Performance Improvements

### 5.1 Parallel Profiling (P1)

**Current:** Sequential column profiling.

**Improved:** Parallel profiling with connection pooling.

```python
async def profile_schema_parallel(schema: str, max_workers: int = 10):
    columns = get_all_columns(schema)

    async with asyncio.Semaphore(max_workers):
        tasks = [profile_column(col) for col in columns]
        results = await asyncio.gather(*tasks)

    return results
```

**Expected improvement:** 5-10x faster for large schemas.

---

### 5.2 Batch LLM Requests (P1)

**Current:** One LLM call per column.

**Improved:** Batch multiple columns per request.

```python
# Current: N calls for N columns
for column in columns:
    result = llm.classify(column)  # 1 API call each

# Improved: 1 call for batch
batch_prompt = format_batch(columns[:20])  # Up to 20 columns
results = llm.classify_batch(batch_prompt)  # 1 API call
```

**Expected improvement:** 10-20x fewer API calls, lower latency.

---

### 5.3 Smart Sampling (P1)

**Current:** Random sample of N values.

**Improved:** Stratified sampling for better representation.

```python
def smart_sample(column_values, n=100):
    # Get distribution
    value_counts = Counter(column_values)

    # Sample strategy
    samples = []
    samples += get_most_common(value_counts, n=20)      # Common patterns
    samples += get_least_common(value_counts, n=10)    # Edge cases
    samples += get_random(column_values, n=50)          # Random diversity
    samples += get_boundary_values(column_values, n=20) # Min/max/nulls

    return deduplicate(samples)[:n]
```

**Benefits:**
- Better pattern detection
- Catches edge cases
- More representative for LLM classification

---

## 6. Security Improvements

### 6.1 Data Masking (P1)

**Problem:** Sample values may contain PII.

**Improvement:** Automatic PII detection and masking.

```python
def mask_pii(sample_values):
    masked = []
    for value in sample_values:
        if is_email(value):
            masked.append("****@****.***")
        elif is_phone(value):
            masked.append("+** *** ****")
        elif is_name(value):
            masked.append("[NAME]")
        else:
            masked.append(value)
    return masked
```

**PII types to detect:**
- Email addresses
- Phone numbers
- Names (using NER)
- Addresses
- National IDs (SSN, etc.)
- Credit card numbers

---

### 6.2 Audit Trail Enhancement (P2)

**Current:** Basic action logging.

**Improved:** Comprehensive audit with diff tracking.

```python
@dataclass
class AuditEntry:
    timestamp: datetime
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    previous_value: dict
    new_value: dict
    reason: str
    ip_address: str
    session_id: str
```

**Audit queries:**
- "Who approved this mapping?"
- "What changed in the last 24 hours?"
- "Show all actions by user X"
- "What was the state before this change?"

---

## 7. Integration Improvements

### 7.1 API Versioning (P1)

**Improvement:** Versioned API for backwards compatibility.

```
/api/v1/schema-matching/...  # Current
/api/v2/schema-matching/...  # Future
```

**Versioning strategy:**
- Major version in URL (`/v1/`, `/v2/`)
- Minor versions via headers
- Deprecation warnings 6 months before removal
- Changelog per version

---

### 7.2 Webhook Integration (P2)

**Improvement:** Outbound webhooks for integration.

```python
# Webhook configuration
webhooks = [
    {
        "url": "https://customer.com/webhook",
        "events": ["pipeline.completed", "review.needed"],
        "secret": "hmac_secret_123"
    }
]

# Webhook payload
{
    "event": "pipeline.completed",
    "timestamp": "2024-01-14T12:00:00Z",
    "data": {
        "pipeline_id": "run_123",
        "client_id": "client_456",
        "auto_match_rate": 0.85,
        "review_items": 45
    },
    "signature": "sha256=..."
}
```

---

### 7.3 Export Formats (P2)

**Current:** JSON only.

**Improved:** Multiple export formats.

| Format | Use Case |
|--------|----------|
| JSON | API responses, programmatic access |
| CSV | Excel analysis, data teams |
| SQL | Direct database import |
| YAML | Configuration, documentation |
| PDF | Reports, management review |

---

## 8. Future Considerations

### 8.1 Self-Hosted LLM (P3)

**When to consider:**
- Data sovereignty requirements
- High volume (cost savings)
- Offline operation needed

**Options:**
- Llama 2/3 (Meta)
- Mistral
- Fine-tuned smaller models

---

### 8.2 Cross-Language Support (P3)

**Current:** German/English focus.

**Future:** Multi-language column names.

| Language | Example Columns |
|----------|-----------------|
| French | `NOM_PATIENT`, `DATE_NAISSANCE` |
| Spanish | `NOMBRE_PACIENTE`, `FECHA_NACIMIENTO` |
| Italian | `NOME_PAZIENTE`, `DATA_NASCITA` |

**Implementation:** Language detection + translated value banks.

---

### 8.3 Schema Evolution Tracking (P3)

**Improvement:** Track schema changes over time.

```
Timeline:
├─ 2024-01-01: Initial schema (v1)
├─ 2024-03-15: Added PATIENT.EMAIL column (v2)
├─ 2024-06-01: Renamed DELKZ → IS_DELETED (v3)
└─ 2024-09-01: Dropped KARTEI.FAX column (v4)
```

**Benefits:**
- Migration planning
- Impact analysis
- Rollback capability

---

## Summary: Priority Roadmap

### Before Production (P0)
1. Background job framework decision
2. LLM integration approach
3. Database schema design
4. Basic caching

### After Initial Rollout (P1)
5. Confidence calibration
6. Incremental profiling
7. Review workflow enhancements
8. Parallel profiling
9. Batch LLM requests
10. Data masking (PII)
11. Multi-tenant isolation
12. API versioning

### Based on User Feedback (P2)
13. Active learning
14. Ensemble classification
15. Dashboard & analytics
16. Event-driven architecture
17. Plugin validators
18. Webhook integration
19. Export formats

### Nice to Have (P3)
20. Self-hosted LLM
21. Cross-language support
22. Schema evolution tracking

---

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) - Backend architecture
- [ACCEPTANCE.md](ACCEPTANCE.md) - Feature acceptance criteria
- [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) - Test database design
- [DISCUSSION_LOG.md](DISCUSSION_LOG.md) - Design decision history

---

*Created: 2024-01-14*
*Status: Backlog*
