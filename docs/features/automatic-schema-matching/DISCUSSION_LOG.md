# Discussion Log: Automatic Schema Matching

This file traces the history of design decisions and user requests for the Automatic Schema Matching feature.

---

## Session 1: Initial Document Split & Value Banks (2024-01-14)

### Request 1: Value Bank Rejection
**User Input:**
> "in values-banks, some values will be marginal, it is important that we can reject them in the Matching clusters for learning."

**Outcome:** Added Value Quality Control section with:
- Three-state lifecycle: pending → verified / rejected
- Rejection reasons enum
- ValueQualityAnalyzer class for auto-detection
- Human review workflow

---

### Request 2: Clarify What Gets Quality-Controlled
**User Input:**
> "Value Quality Control: what what values? Table Name, Column Name, combination Table & Column Name, data type, format? This needs to be properly defined."

**Outcome:** Added detailed section defining three component types:
1. **Column Name Variants** - Alternative column names mapping to canonical entities
2. **Data Values** - Actual data content found in columns
3. **Value Patterns** - Regex format patterns for structured data

Each with explicit accept/reject examples.

---

### Request 3: Empty & Abandoned Column Detection
**User Input:**
> "Sometimes, there will be columns that are empty or simply wrongly used (a developer abandoned that column and left it with its values) This needs also to be detected and ignored (labeled). Please create the acceptance criteria for that feature."

**Outcome:** Added Column Quality Detection section with:
- Column states: empty, mostly_empty, abandoned, misused, test_only
- Gherkin acceptance criteria for detection, labeling, exclusion
- Database schema for `column_quality` table

---

### Request 4: Create Acceptance Criteria File
**User Input:**
> "Please create the acceptance criteria for automatic-schema-matching. Should it be in one file?"

**Outcome:** Created `ACCEPTANCE.md` with comprehensive Gherkin scenarios covering all 10 components.

---

## Session 2: Structure & Human-in-the-Loop (2024-01-14)

### Request 5: Reorder Column Quality Detection
**User Input:**
> "Column Quality Detection seems to be at the wrong place. At which rank should it be?"

**Outcome:** Moved Column Quality Detection from position 6 to position 2 (Phase 1b), right after Schema Profiling and before LLM Classification.

**Rationale:** Detect and filter bad columns BEFORE wasting LLM calls on them.

---

### Request 6: Confirm Reordering
**User Input:**
> "yes."

**Outcome:** Implemented the reordering in ACCEPTANCE.md.

---

### Request 7: Human-in-the-Loop for Flagged Columns
**User Input:**
> "Column Quality Detection - When it is flagged, we need a human in the loop."

**Outcome:** Enhanced Column Quality Detection section with:
- Flagged columns require human review before Phase 2
- Human review queue with column metrics
- Pipeline blocking option (`review_required_before_phase2`)
- Auto-exclude only for 100% empty columns (low risk)

---

### Request 8: HITL Everywhere?
**User Input:**
> "Human-in-the-Loop Workflow should be everywhere right? Every steps needs to be confirmed by human? best practices, how should we do it?"

**Outcome:** Clarified that NOT every step needs human confirmation. Proposed tiered confidence-based approach:
- ≥85% confidence → Auto-accept
- 60-84% confidence → Quick review
- <60% confidence → Full investigation

---

### Request 9: HITL as Trust Configuration
**User Input:**
> "Basically the Human-in-the-Loop Workflow should be the configuration of the level of trust. What do you think? best practices? criticize my ideas and improve them"

**Outcome:** Validated the core insight, but improved with multi-dimensional model:

1. **Trust Profiles** (organizational): Conservative / Standard / Permissive
2. **Risk Classes** (per-entity): Critical / Important / Optional
3. **Adaptive Trust**: Earned over time based on accuracy tracking
4. **Effective Threshold**: `max(profile_threshold, entity_min_threshold)`

Key insight: Trust is multi-dimensional (profile × risk × adaptation), not a single slider.

---

### Request 10: Rewrite & Create Log
**User Input:**
> "yes, rewrite it. Plus create a log of all my 'claude discussion input' so that i can trace back the history of my requests."

**Outcome:**
- Created this `DISCUSSION_LOG.md` file
- Rewrote `ACCEPTANCE.md` with Trust & Review Configuration model

---

## Design Decisions Summary

| Decision | Rationale |
|----------|-----------|
| Column Quality at Phase 1b | Filter bad columns before LLM calls |
| HITL = Trust Configuration | Cross-cutting concern, not separate workflow |
| Multi-dimensional trust | Profile × Risk × Adaptation |
| Adaptive trust | Trust is earned, not just configured |
| Final approval always logged | Audit trail regardless of trust level |

---

### Request 11: Backend Architecture Decision
**User Input:**
> "Now i have an architectural question: when we develop such a complex and elaborate feature, on the backend, should it have its own directory AND/OR blueprint? What are your insight on this?"

**Discussion:**
- User asked about best practices for organizing complex features in Flask backend
- Analyzed trade-offs between: Blueprint only, Directory only, Both

**Outcome:** Decision to use **both** Blueprint and Feature Directory:
- **Blueprint:** For route organization and URL namespacing (`/api/schema-matching/*`)
- **Directory:** For code organization (services, pipeline, trust, review modules)
- **Models:** Stay in shared `models/` directory (for DB migrations, cross-feature access)

**Document Created:** `ARCHITECTURE.md` - Full backend structure specification

---

### Request 12: Document Architecture Decision
**User Input:**
> "please write a document in docs/features/automatic-schema-matching/ about it so that we remember this when it will be time to build."

**Outcome:** Created `ARCHITECTURE.md` containing:
- Directory structure specification
- Component responsibilities
- API endpoint definitions
- Blueprint registration code
- Service patterns
- Pipeline orchestrator pattern
- Testing strategy
- Implementation order
- Open questions for implementation

---

## Design Decisions Summary

| Decision | Rationale |
|----------|-----------|
| Column Quality at Phase 1b | Filter bad columns before LLM calls |
| HITL = Trust Configuration | Cross-cutting concern, not separate workflow |
| Multi-dimensional trust | Profile × Risk × Adaptation |
| Adaptive trust | Trust is earned, not just configured |
| Final approval always logged | Audit trail regardless of trust level |
| **Both Blueprint + Directory** | Complex feature needs both route and code organization |
| **Models in shared location** | DB migrations, cross-feature access |

---

### Request 13: Database Simulator Design
**User Input:**
> "in docs/features/automatic-schema-matching/ we need to create a document 'database_simulator'. This needs to be based on quality management detection limits AND/OR realistic situations. please criticize my ideas and improve them"

**Discussion:**
- Critiqued initial concept: missing ground truth, unclear purpose, conflating test types
- Proposed three-layer strategy: Unit fixtures, Integration DB, Multi-center simulation
- Key addition: Ground Truth Manifest (YAML files defining expected results)

**User Decisions:**
1. Primary use case: Demo database for both testing AND presentations
2. Output format: Docker SQL Server (realistic)
3. Schema structure: Both realistic Ivoris + simplified
4. Multi-center: Yes, 10 databases

**Outcome:** Created `DATABASE_SIMULATOR.md` with:

**10 Centers Design:**
| Centers | Purpose | Quality |
|---------|---------|---------|
| 1-2 | Baseline/Seed | Clean |
| 3-4 | Naming variations | Moderate |
| 5-6 | Data quality issues | Poor |
| 7-8 | Threshold edge cases | Synthetic |
| 9-10 | Realistic messy | Messy |

**Key Features:**
- Ground truth manifest format (YAML)
- Docker Compose for 10 SQL Server instances (ports 1433-1442)
- Exact threshold tests (94% vs 95% vs 96% NULL)
- German/Swiss/Austrian insurance variations
- Column naming variations across centers
- Data generation scripts structure
- Demo flow script

---

### Request 14: Simulation Ordering (Extreme → Normal)
**User Input:**
> "Simulations needs to be from extreme to normal. What are the best practices knowing that we have to represent possibilities (potential DB) and realities (actual DB)"

**Discussion:**
- User requested reversing the simulation order from Normal→Extreme to Extreme→Normal
- This is the "stress-first" or "boundary testing" approach

**Analysis Provided:**

| Principle | Rationale |
|-----------|-----------|
| **Fail Fast** | Discover breaking points before investing in "easy" cases |
| **Defensive Design** | If it handles chaos, normal is trivial |
| **Confidence Building** | Passing edge cases = high confidence in robustness |
| **Regression Priority** | Edge cases break first during refactoring |

**Possibilities vs Realities Framework:**

| Type | Definition | Purpose |
|------|------------|---------|
| **Possibilities (Synthetic)** | Constructed worst-case scenarios that *could* exist | Test detection limits, boundary conditions |
| **Realities (Observed)** | Patterns from actual Ivoris databases | Validate real-world handling |

**Outcome:** Complete restructure of DATABASE_SIMULATOR.md with 4 zones:

| Zone | Centers | Type | Purpose | Expected Auto-Match |
|------|---------|------|---------|---------------------|
| **A** | 1-2 | Synthetic Extremes | Break the system | 0-40% |
| **B** | 3-4 | Realistic Extremes | Handle chaos gracefully | 50-65% |
| **C** | 5-7 | Moderate Variations | Test adaptability | 75-85% |
| **D** | 8-10 | Clean Baselines | Verify accuracy | 90-98% |

**Key Insight:**
- **Possibilities** test the **boundaries** of detection (Zone A)
- **Realities** test the **accuracy** of matching (Zones B, C, D)

---

### Request 15: Zone Distribution Best Practices
**User Input:**
> "Ha great, how many do we need from each zones? best practices?"

**Discussion:**
- Analyzed what drives the count per zone
- Provided sizing rules based on boundary testing and equivalence partitioning

**Outcome:** Added "Zone Distribution Best Practices" section to DATABASE_SIMULATOR.md with:

**The Sizing Rules:**

| Zone | Rule | Rationale |
|------|------|-----------|
| **A** | Fixed at 2 | Synthetic = deterministic, one covers all thresholds |
| **B** | 1 per disaster pattern | Don't duplicate, enumerate |
| **C** | Scales with variation space | Feeds value banks, diminishing returns after 5 |
| **D** | Minimum 1, maximum 3 | Quality > quantity |

**Distribution Options:**

| Scale | A | B | C | D | Total |
|-------|---|---|---|---|-------|
| Minimum Viable | 2 | 2 | 2 | 1 | 7 |
| Standard | 2 | 2 | 3 | 3 | 10 |
| Comprehensive | 2 | 3-4 | 5-6 | 2-3 | 12-15 |

**Key insight:** Zone C is where learning happens. Add centers there first.

---

### Request 16: Possible Improvements Document
**User Input:**
> "Write a new file about about possible improvements."

**Outcome:** Created `IMPROVEMENTS.md` documenting potential enhancements organized by:

1. **Open Technical Decisions (P0):**
   - Background job framework (Celery vs RQ vs Dramatiq)
   - LLM integration (Direct vs LangChain vs LiteLLM)
   - Database architecture (same DB vs separate schema vs separate DB)
   - Caching strategy (LLM responses, profiles, value bank)
   - Notification system (in-app, email, Slack, webhook)

2. **Algorithm Improvements (P1-P2):**
   - Confidence calibration (historical accuracy adjustment)
   - Active learning (prioritize uncertain cases)
   - Ensemble classification (combine multiple signals)
   - Incremental profiling (only profile changes)

3. **UX Improvements (P1-P2):**
   - Review workflow (bulk actions, keyboard shortcuts, grouping)
   - Dashboard & analytics
   - Comparison view (cross-database)

4. **Architecture Improvements (P2):**
   - Event-driven pipeline
   - Plugin architecture for validators
   - Multi-tenant isolation

5. **Performance Improvements (P1):**
   - Parallel profiling
   - Batch LLM requests
   - Smart sampling

6. **Security Improvements (P1-P2):**
   - PII masking
   - Enhanced audit trail

7. **Integration Improvements (P1-P2):**
   - API versioning
   - Webhook integration
   - Export formats

8. **Future Considerations (P3):**
   - Self-hosted LLM
   - Cross-language support
   - Schema evolution tracking

---

## Design Decisions Summary

| Decision | Rationale |
|----------|-----------|
| Column Quality at Phase 1b | Filter bad columns before LLM calls |
| HITL = Trust Configuration | Cross-cutting concern, not separate workflow |
| Multi-dimensional trust | Profile × Risk × Adaptation |
| Adaptive trust | Trust is earned, not just configured |
| Final approval always logged | Audit trail regardless of trust level |
| Both Blueprint + Directory | Complex feature needs both route and code organization |
| Models in shared location | DB migrations, cross-feature access |
| 10 Docker SQL Server centers | Realistic simulation with progression |
| Ground truth manifests | Enable automated validation |
| Threshold edge cases in Center 8 | Regression testing for detection limits |
| **Extreme → Normal ordering** | Stress-first approach: prove robustness before accuracy |
| **Possibilities vs Realities** | Synthetic extremes test limits, observed patterns test accuracy |
| **Zone A fixed at 2** | Synthetic tests are deterministic, one covers all thresholds |
| **Zone C scales with variance** | Learning zone - add centers here first for more value bank coverage |
| **Standard = 10 centers (2-2-3-3)** | Balanced coverage for testing and demos |

---

## Open Questions

1. **Background job framework:** Celery? RQ? Built-in threading?
2. **LLM integration:** Direct API? Langchain? Custom gateway?
3. **Database:** Same DB as app? Separate schema? Separate DB?
4. **Caching:** Redis for classification cache? In-memory?
5. **Notifications:** Email service? Slack webhook? Both?

---

*Last updated: 2024-01-14*
