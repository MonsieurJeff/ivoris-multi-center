# Implementation Roadmap: Automatic Schema Matching

**Type:** Delivery Plan
**Scope:** From scratch to production
**Approach:** Incremental delivery with validation gates

---

## Overview

This roadmap defines the ordered implementation tasks for the Automatic Schema Matching system. Each phase builds on the previous, with validation checkpoints before proceeding.

### Principles

1. **Incremental Value** - Each phase delivers usable functionality
2. **Validate Early** - Test against real data before adding complexity
3. **ML is Enhancement** - System works without ML; ML improves accuracy
4. **Human-in-the-Loop First** - Start conservative, loosen as trust builds

### Document Map

| Document | Role in Implementation |
|----------|------------------------|
| This document | **Sequence** - What to build, in what order |
| [TECHNICAL_SOLUTION.md](TECHNICAL_SOLUTION.md) | **Specification** - How to build each component |
| [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) | **Validation** - How to verify it works |
| [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) | **Test Data** - What to test against |

---

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IMPLEMENTATION PHASES                                │
│                                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐       │
│  │ Phase 1 │──▶│ Phase 2 │──▶│ Phase 3 │──▶│ Phase 4 │──▶│ Phase 5 │       │
│  │Foundation│   │  Core   │   │  Human  │   │Learning │   │Production│      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘       │
│                                                                              │
│  Database      Matching      Review        ML            Monitoring         │
│  Schema        Engine        Queue         Enhancement   Security           │
│  Basic API     Value Bank    Trust         Calibration   Deployment         │
│                Similarity    Profiles      Active Learn  Operations         │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Week 1-2      Week 3-4      Week 5-6      Week 7-8      Week 9-10         │
│  (estimate)    (estimate)    (estimate)    (estimate)    (estimate)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation

**Goal:** Infrastructure and data layer ready for development

### 1.1 Project Setup

| Task | Description | Depends On |
|------|-------------|------------|
| 1.1.1 | Create repository structure | - |
| 1.1.2 | Set up development environment | 1.1.1 |
| 1.1.3 | Configure CI/CD pipeline | 1.1.1 |
| 1.1.4 | Set up test database connections | 1.1.2 |
| 1.1.5 | Configure secrets management | 1.1.2 |

### 1.2 Database Schema

| Task | Description | Depends On |
|------|-------------|------------|
| 1.2.1 | Design canonical_entities table | - |
| 1.2.2 | Design column_variants table | 1.2.1 |
| 1.2.3 | Design value_patterns table | 1.2.1 |
| 1.2.4 | Design client_mappings table | 1.2.1, 1.2.2 |
| 1.2.5 | Design review_items table | 1.2.4 |
| 1.2.6 | Design mapping_audit_log table | 1.2.4 |
| 1.2.7 | Create database migrations | 1.2.1-1.2.6 |
| 1.2.8 | Seed canonical entities | 1.2.7 |

### 1.3 Basic API Layer

| Task | Description | Depends On |
|------|-------------|------------|
| 1.3.1 | Set up API framework (Flask/FastAPI) | 1.1.2 |
| 1.3.2 | Implement health check endpoint | 1.3.1 |
| 1.3.3 | Implement authentication middleware | 1.3.1 |
| 1.3.4 | Set up request logging | 1.3.1 |
| 1.3.5 | Configure error handling | 1.3.1 |

### 1.4 Test Infrastructure

| Task | Description | Depends On |
|------|-------------|------------|
| 1.4.1 | Set up test database (Zone D - clean) | 1.1.4 |
| 1.4.2 | Create ground truth manifest for test DB | 1.4.1 |
| 1.4.3 | Set up test framework | 1.1.2 |
| 1.4.4 | Create integration test harness | 1.4.3 |

### Phase 1 Validation Gate

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: Phase 1 Complete                                     │
├─────────────────────────────────────────────────────────────────┤
│ □ Database migrations run successfully                          │
│ □ API health check returns 200                                  │
│ □ Can connect to test database                                  │
│ □ Canonical entities seeded (patient_id, insurance_name, etc.)  │
│ □ CI pipeline passes                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 2: Core Matching Engine

**Goal:** Can analyze a database and propose mappings (no learning yet)

### 2.1 Schema Profiler

| Task | Description | Depends On |
|------|-------------|------------|
| 2.1.1 | Implement table listing | Phase 1 |
| 2.1.2 | Implement column metadata extraction | 2.1.1 |
| 2.1.3 | Implement column statistics (null %, cardinality) | 2.1.2 |
| 2.1.4 | Implement value sampling | 2.1.2 |
| 2.1.5 | Implement problem column detection (empty, abandoned) | 2.1.3 |
| 2.1.6 | Add connection pooling | 2.1.1 |

### 2.2 Similarity Scoring

| Task | Description | Depends On |
|------|-------------|------------|
| 2.2.1 | Integrate similarity library (rapidfuzz) | Phase 1 |
| 2.2.2 | Implement column name normalization | 2.2.1 |
| 2.2.3 | Implement tokenization for compound names | 2.2.2 |
| 2.2.4 | Implement combined similarity scoring | 2.2.1-2.2.3 |
| 2.2.5 | Tune similarity weights for German column names | 2.2.4 |

### 2.3 Value Bank (Basic)

| Task | Description | Depends On |
|------|-------------|------------|
| 2.3.1 | Implement exact match lookup | 1.2.2 |
| 2.3.2 | Implement fuzzy match lookup | 2.2.4 |
| 2.3.3 | Implement value pattern matching | 1.2.3 |
| 2.3.4 | Seed value bank with known patterns | 2.3.1 |
| 2.3.5 | Implement value bank caching | 2.3.1-2.3.3 |

### 2.4 Matching Engine

| Task | Description | Depends On |
|------|-------------|------------|
| 2.4.1 | Implement single column matching | 2.2.4, 2.3.2 |
| 2.4.2 | Implement multi-signal confidence aggregation | 2.4.1 |
| 2.4.3 | Implement table-level matching orchestration | 2.4.2 |
| 2.4.4 | Implement database-level matching orchestration | 2.4.3 |
| 2.4.5 | Add parallel column processing | 2.4.4 |

### 2.5 API Endpoints (Matching)

| Task | Description | Depends On |
|------|-------------|------------|
| 2.5.1 | Implement POST /map (start mapping) | 2.4.4 |
| 2.5.2 | Implement GET /status (check progress) | 2.5.1 |
| 2.5.3 | Implement GET /mappings (retrieve results) | 2.5.1 |
| 2.5.4 | Add async job processing | 2.5.1 |

### Phase 2 Validation Gate

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: Phase 2 Complete                                     │
├─────────────────────────────────────────────────────────────────┤
│ □ Can profile a test database (list tables, columns, stats)    │
│ □ Similarity scoring returns expected values for test cases     │
│ □ Value bank lookups work (exact and fuzzy)                     │
│ □ Can run full mapping on Zone D test database                  │
│ □ Mapping produces results with confidence scores               │
│ □ API endpoints respond correctly                               │
│                                                                  │
│ METRIC: Zone D auto-match rate ≥ 60% (without human input)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 3: Human-in-the-Loop

**Goal:** Humans can review, approve, and reject mappings

### 3.1 Review Queue

| Task | Description | Depends On |
|------|-------------|------------|
| 3.1.1 | Implement review item creation | Phase 2 |
| 3.1.2 | Implement review queue retrieval | 3.1.1 |
| 3.1.3 | Implement review prioritization | 3.1.2 |
| 3.1.4 | Implement review resolution (approve/reject/remap) | 3.1.1 |
| 3.1.5 | Implement bulk review actions | 3.1.4 |

### 3.2 Trust Profiles

| Task | Description | Depends On |
|------|-------------|------------|
| 3.2.1 | Define trust profile schema | - |
| 3.2.2 | Implement conservative profile | 3.2.1 |
| 3.2.3 | Implement standard profile | 3.2.1 |
| 3.2.4 | Implement permissive profile | 3.2.1 |
| 3.2.5 | Implement profile selection per client | 3.2.2-3.2.4 |
| 3.2.6 | Implement critical entity override (always review) | 3.2.5 |

### 3.3 Decision Logic

| Task | Description | Depends On |
|------|-------------|------------|
| 3.3.1 | Implement auto-accept logic | 3.2.5 |
| 3.3.2 | Implement review-required logic | 3.2.5 |
| 3.3.3 | Implement auto-reject logic | 3.2.5 |
| 3.3.4 | Integrate decision logic into matching engine | 3.3.1-3.3.3 |

### 3.4 API Endpoints (Review)

| Task | Description | Depends On |
|------|-------------|------------|
| 3.4.1 | Implement GET /review (queue listing) | 3.1.2 |
| 3.4.2 | Implement POST /review/{id} (submit decision) | 3.1.4 |
| 3.4.3 | Implement GET /review/stats (queue metrics) | 3.1.2 |
| 3.4.4 | Add reviewer authentication/authorization | 3.4.2 |

### 3.5 Audit Trail

| Task | Description | Depends On |
|------|-------------|------------|
| 3.5.1 | Implement audit logging for auto-accept | 3.3.1 |
| 3.5.2 | Implement audit logging for human decisions | 3.1.4 |
| 3.5.3 | Implement audit log retrieval API | 3.5.1, 3.5.2 |
| 3.5.4 | Add audit log retention policy | 3.5.3 |

### Phase 3 Validation Gate

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: Phase 3 Complete                                     │
├─────────────────────────────────────────────────────────────────┤
│ □ Review queue populates with uncertain mappings                │
│ □ Trust profiles affect auto-accept threshold                   │
│ □ Human can approve/reject mappings via API                     │
│ □ Audit log captures all decisions                              │
│ □ Critical entities (patient_id) always require review          │
│                                                                  │
│ METRIC: End-to-end mapping with human review works             │
│ METRIC: Conservative profile = mostly review queue             │
│ METRIC: Permissive profile = mostly auto-accept                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 4: Learning & Machine Learning

**Goal:** System improves with each client; ML enhances accuracy

### 4.1 Value Bank Learning

| Task | Description | Depends On |
|------|-------------|------------|
| 4.1.1 | Implement learning from approved mappings | Phase 3 |
| 4.1.2 | Implement occurrence counting | 4.1.1 |
| 4.1.3 | Implement confidence weighting by occurrences | 4.1.2 |
| 4.1.4 | Implement value pattern extraction | 4.1.1 |
| 4.1.5 | Implement rejected pattern tracking | 4.1.1 |

### 4.2 Confidence Calibration

| Task | Description | Depends On |
|------|-------------|------------|
| 4.2.1 | Track historical accuracy per entity type | 4.1.1 |
| 4.2.2 | Implement accuracy calculation | 4.2.1 |
| 4.2.3 | Implement confidence calibration (Platt scaling) | 4.2.2 |
| 4.2.4 | Adjust thresholds based on calibrated confidence | 4.2.3 |

### 4.3 ML Enhancement: Embedding-Based Matching

| Task | Description | Depends On |
|------|-------------|------------|
| 4.3.1 | Evaluate embedding models for column names | Phase 2 |
| 4.3.2 | Generate embeddings for canonical entities | 4.3.1 |
| 4.3.3 | Generate embeddings for column name variants | 4.3.2 |
| 4.3.4 | Implement embedding similarity as additional signal | 4.3.3 |
| 4.3.5 | Integrate embedding score into confidence aggregation | 4.3.4 |
| 4.3.6 | Evaluate accuracy improvement from embeddings | 4.3.5 |

### 4.4 ML Enhancement: Classification Model

| Task | Description | Depends On |
|------|-------------|------------|
| 4.4.1 | Prepare training data from verified mappings | 4.1.1 |
| 4.4.2 | Feature engineering (name, type, stats, samples) | 4.4.1 |
| 4.4.3 | Train classification model (entity prediction) | 4.4.2 |
| 4.4.4 | Evaluate model accuracy on held-out data | 4.4.3 |
| 4.4.5 | Integrate model prediction as additional signal | 4.4.4 |
| 4.4.6 | Implement model retraining pipeline | 4.4.3 |

### 4.5 Active Learning

| Task | Description | Depends On |
|------|-------------|------------|
| 4.5.1 | Identify high-uncertainty predictions | 4.4.5 |
| 4.5.2 | Prioritize uncertain cases for human review | 4.5.1 |
| 4.5.3 | Feed human decisions back to training data | 4.5.2 |
| 4.5.4 | Trigger retraining when significant new data available | 4.5.3 |

### 4.6 Cross-Database Learning

| Task | Description | Depends On |
|------|-------------|------------|
| 4.6.1 | Track patterns across multiple clients | 4.1.1 |
| 4.6.2 | Identify common vs client-specific patterns | 4.6.1 |
| 4.6.3 | Implement federated value bank queries | 4.6.2 |
| 4.6.4 | Measure learning curve (accuracy vs clients onboarded) | 4.6.1 |

### Phase 4 Validation Gate

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: Phase 4 Complete                                     │
├─────────────────────────────────────────────────────────────────┤
│ □ Value bank grows with each verified mapping                   │
│ □ Second client benefits from first client's mappings          │
│ □ Confidence calibration matches actual accuracy                │
│ □ Embedding similarity improves matching (if implemented)       │
│ □ ML model accuracy exceeds rule-based baseline (if applicable)│
│                                                                  │
│ METRIC: Zone D auto-match rate ≥ 90% (with learning)           │
│ METRIC: Zone C auto-match rate ≥ 75%                           │
│ METRIC: Client N accuracy > Client 1 accuracy                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Production Hardening

**Goal:** System is reliable, secure, and observable in production

### 5.1 Performance Optimization

| Task | Description | Depends On |
|------|-------------|------------|
| 5.1.1 | Implement value bank caching (Redis) | Phase 4 |
| 5.1.2 | Implement schema metadata caching | 5.1.1 |
| 5.1.3 | Implement batch processing for large schemas | Phase 2 |
| 5.1.4 | Optimize database queries (indexes, explain plans) | Phase 1 |
| 5.1.5 | Load test with realistic data volumes | 5.1.1-5.1.4 |

### 5.2 Security

| Task | Description | Depends On |
|------|-------------|------------|
| 5.2.1 | Implement PII detection in samples | Phase 2 |
| 5.2.2 | Implement sample value masking | 5.2.1 |
| 5.2.3 | Implement connection string encryption | Phase 1 |
| 5.2.4 | Implement role-based access control | 3.4.4 |
| 5.2.5 | Security audit and penetration testing | 5.2.1-5.2.4 |

### 5.3 Reliability

| Task | Description | Depends On |
|------|-------------|------------|
| 5.3.1 | Implement retry logic for transient failures | Phase 2 |
| 5.3.2 | Implement circuit breaker for external services | 5.3.1 |
| 5.3.3 | Implement graceful degradation | 5.3.2 |
| 5.3.4 | Implement job recovery (resume interrupted mappings) | 2.5.4 |
| 5.3.5 | Chaos testing (kill workers, disconnect DB) | 5.3.1-5.3.4 |

### 5.4 Observability

| Task | Description | Depends On |
|------|-------------|------------|
| 5.4.1 | Implement structured logging | Phase 1 |
| 5.4.2 | Implement metrics collection (Prometheus) | 5.4.1 |
| 5.4.3 | Create operational dashboards (Grafana) | 5.4.2 |
| 5.4.4 | Implement alerting (error rates, queue depth) | 5.4.3 |
| 5.4.5 | Implement distributed tracing | 5.4.1 |

### 5.5 API Hardening

| Task | Description | Depends On |
|------|-------------|------------|
| 5.5.1 | Implement rate limiting | Phase 1 |
| 5.5.2 | Implement request validation | 5.5.1 |
| 5.5.3 | Implement API versioning | Phase 1 |
| 5.5.4 | Generate API documentation (OpenAPI) | 5.5.3 |
| 5.5.5 | Implement webhook notifications | Phase 3 |

### Phase 5 Validation Gate

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: Phase 5 Complete                                     │
├─────────────────────────────────────────────────────────────────┤
│ □ Response times meet SLA (< 100ms for lookups, < 5min/table)  │
│ □ PII not exposed in logs or API responses                      │
│ □ System recovers from worker failure                           │
│ □ Dashboards show key metrics                                   │
│ □ Alerts fire for error conditions                              │
│ □ Security audit passed                                         │
│                                                                  │
│ METRIC: 99.9% uptime over 1 week test                          │
│ METRIC: No PII in sample responses                             │
│ METRIC: Recovery time < 5 minutes                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 6: Deployment & Operations

**Goal:** System running in production with operational procedures

### 6.1 Deployment

| Task | Description | Depends On |
|------|-------------|------------|
| 6.1.1 | Create production infrastructure (Terraform/K8s) | Phase 5 |
| 6.1.2 | Configure production database | 6.1.1 |
| 6.1.3 | Configure production Redis | 6.1.1 |
| 6.1.4 | Configure production secrets | 6.1.1 |
| 6.1.5 | Deploy to staging environment | 6.1.1-6.1.4 |
| 6.1.6 | Run staging validation suite | 6.1.5 |
| 6.1.7 | Deploy to production | 6.1.6 |

### 6.2 Operational Procedures

| Task | Description | Depends On |
|------|-------------|------------|
| 6.2.1 | Document runbook (common operations) | Phase 5 |
| 6.2.2 | Document incident response procedure | 6.2.1 |
| 6.2.3 | Document rollback procedure | 6.1.7 |
| 6.2.4 | Create on-call rotation | 6.2.2 |
| 6.2.5 | Conduct operational readiness review | 6.2.1-6.2.4 |

### 6.3 First Client Onboarding

| Task | Description | Depends On |
|------|-------------|------------|
| 6.3.1 | Select pilot client | 6.1.7 |
| 6.3.2 | Run mapping with conservative profile | 6.3.1 |
| 6.3.3 | Complete human review of all mappings | 6.3.2 |
| 6.3.4 | Verify accuracy against manual validation | 6.3.3 |
| 6.3.5 | Collect feedback and iterate | 6.3.4 |

### 6.4 Rollout

| Task | Description | Depends On |
|------|-------------|------------|
| 6.4.1 | Onboard second client (standard profile) | 6.3.5 |
| 6.4.2 | Measure learning improvement | 6.4.1 |
| 6.4.3 | Onboard remaining clients incrementally | 6.4.2 |
| 6.4.4 | Monitor and tune as needed | 6.4.3 |

### Phase 6 Validation Gate

```
┌─────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: Phase 6 Complete (Production Ready)                  │
├─────────────────────────────────────────────────────────────────┤
│ □ Production deployment successful                              │
│ □ Runbook and incident procedures documented                    │
│ □ On-call rotation established                                  │
│ □ Pilot client onboarded and satisfied                          │
│ □ Learning demonstrated (client 2 easier than client 1)         │
│                                                                  │
│ METRIC: Pilot client accuracy ≥ 95%                            │
│ METRIC: Client 2 review queue smaller than client 1            │
│ METRIC: No production incidents in first week                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CRITICAL PATH                                        │
│                                                                              │
│  DB Schema ──▶ Schema Profiler ──▶ Similarity ──▶ Matching ──▶ Review       │
│     │              │                   │             │           │          │
│     │              │                   │             │           │          │
│     ▼              ▼                   ▼             ▼           ▼          │
│  Canonical     Value Bank         Confidence     Decision    Learning       │
│  Entities      (Basic)            Aggregation    Logic       From Review    │
│     │              │                   │             │           │          │
│     └──────────────┴───────────────────┴─────────────┴───────────┘          │
│                              │                                               │
│                              ▼                                               │
│                    ML Enhancement (Optional)                                │
│                              │                                               │
│                              ▼                                               │
│                    Production Hardening                                     │
│                              │                                               │
│                              ▼                                               │
│                         Deployment                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Parallelizable Work

| Can Run In Parallel | Because |
|---------------------|---------|
| Schema Profiler + Similarity Scoring | Independent modules |
| Trust Profiles + Review Queue | Both depend on Phase 2 |
| Value Bank Learning + Confidence Calibration | Both depend on Phase 3 |
| ML Embeddings + ML Classification | Independent approaches |
| Security + Performance + Observability | Independent concerns |

---

## Risk Mitigation

### Technical Risks

| Risk | Mitigation | Phase |
|------|------------|-------|
| Poor similarity accuracy | Test with real data early; tune weights | 2 |
| ML doesn't improve accuracy | System works without ML; ML is optional | 4 |
| Performance issues at scale | Load test in Phase 5; optimize critical path | 5 |
| Data quality in client DBs | Detect and flag problem columns | 2 |

### Process Risks

| Risk | Mitigation | Phase |
|------|------------|-------|
| Scope creep | Strict phase gates; defer enhancements | All |
| Integration issues | Test with real data from Phase 2 | 2+ |
| Human review bottleneck | Prioritize queue; bulk actions | 3 |
| Learning not working | Track metrics; validate assumptions | 4 |

---

## Success Metrics

### Per Phase

| Phase | Key Metric | Target |
|-------|------------|--------|
| 1 | Infrastructure ready | All checks pass |
| 2 | Zone D auto-match (no learning) | ≥ 60% |
| 3 | Human review workflow | End-to-end works |
| 4 | Zone D auto-match (with learning) | ≥ 90% |
| 5 | Production readiness | All gates pass |
| 6 | Pilot client satisfaction | ≥ 95% accuracy |

### Overall

| Metric | Target | Measured |
|--------|--------|----------|
| Auto-match rate (Zone D) | ≥ 90% | After Phase 4 |
| Auto-match rate (Zone C) | ≥ 75% | After Phase 4 |
| Auto-match rate (Zone B) | ≥ 50% | After Phase 4 |
| False positive rate | < 1% | Ongoing |
| Time to map new client | < 1 day | After Phase 6 |
| Learning curve | Measurable improvement | Client N vs Client 1 |

---

## ML Decision Points

### When to Invest in ML

| Signal | Action |
|--------|--------|
| Rule-based accuracy plateaus at < 85% | Consider ML classification |
| German compound names not matching well | Consider embedding similarity |
| Many similar columns with different names | Consider clustering/embedding |
| Value bank growing but accuracy not improving | Consider ML to generalize |

### When NOT to Invest in ML

| Signal | Action |
|--------|--------|
| Rule-based accuracy ≥ 90% | ML overhead not justified |
| Small dataset (< 1000 verified mappings) | Not enough training data |
| High accuracy variance between entities | Fix feature engineering first |
| Performance requirements strict | ML adds latency |

---

## References

- [TECHNICAL_SOLUTION.md](TECHNICAL_SOLUTION.md) - Architecture and code patterns
- [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) - Validation scenarios
- [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) - Test database design
- [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) - Alternative agent-based approach
- [CODING_EXERCISES.md](CODING_EXERCISES.md) - Algorithm trade-offs

---

*This roadmap provides the sequence. See TECHNICAL_SOLUTION.md for implementation details.*
