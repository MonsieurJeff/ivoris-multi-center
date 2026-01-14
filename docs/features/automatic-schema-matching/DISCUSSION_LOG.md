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

## Open Questions

*None currently - add future questions here*

---

*Last updated: 2024-01-14*
