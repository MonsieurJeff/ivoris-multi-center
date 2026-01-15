# Technical Solution: Schema Matching Service

**Purpose:** Production-ready technical design for multi-center schema matching
**Context:** Interview preparation - demonstrating scalable architecture
**Status:** Proposal

---

## The Problem

Multi-center dental practice system with 15+ databases. Each center has schema variations—same business entities, different column names, data types, structures. Manual mapping doesn't scale. Previous systems are often rigid and require code changes per client.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY                                    │
│                        /api/schema-matching/*                           │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────┐
│                      MATCHING SERVICE                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Schema    │  │    Value    │  │  Matching   │  │   Review    │    │
│  │  Profiler   │  │    Bank     │  │   Engine    │  │   Queue     │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │
┌─────────▼────────────────▼────────────────▼────────────────▼────────────┐
│                         DATA LAYER                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Client    │  │  Canonical  │  │   Value     │  │   Review    │    │
│  │  Databases  │  │   Schema    │  │    Bank     │  │   Items     │    │
│  │   (15+)     │  │  (target)   │  │  (learned)  │  │  (pending)  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **Schema Profiler** | Query client databases, extract metadata, sample values |
| **Value Bank** | Store learned patterns (column names, value patterns) |
| **Matching Engine** | Multi-signal similarity scoring |
| **Review Queue** | Human-in-the-loop for uncertain mappings |

---

## Database Schema

### Core Tables

```sql
-- What we're mapping TO (your business model)
CREATE TABLE canonical_entities (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE,        -- 'patient_id', 'insurance_name'
    category VARCHAR(50),            -- 'patient', 'insurance', 'chart'
    data_type VARCHAR(50),           -- 'integer', 'string', 'date'
    description TEXT,
    is_critical BOOLEAN DEFAULT false -- patient_id = critical
);

-- Learned column name patterns
CREATE TABLE column_variants (
    id UUID PRIMARY KEY,
    entity_id UUID REFERENCES canonical_entities(id),
    column_name VARCHAR(255),        -- 'PATNR', 'PAT_NR', 'PATIENTENNR'
    source_client_id UUID,           -- where we learned this
    occurrence_count INT DEFAULT 1,  -- seen in N databases
    confidence DECIMAL(3,2),         -- 0.00-1.00
    status VARCHAR(20) DEFAULT 'verified', -- verified/rejected/pending
    created_at TIMESTAMP,
    verified_by UUID,                -- who approved
    UNIQUE(entity_id, column_name)
);

-- Learned data value patterns
CREATE TABLE value_patterns (
    id UUID PRIMARY KEY,
    entity_id UUID REFERENCES canonical_entities(id),
    pattern_type VARCHAR(50),        -- 'regex', 'enum', 'range'
    pattern_value TEXT,              -- '[A-Z]{2}\d{6}' or '["AOK","DAK","BARMER"]'
    occurrence_count INT DEFAULT 1,
    confidence DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'verified'
);

-- Client-specific mappings (the output)
CREATE TABLE client_mappings (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    entity_id UUID REFERENCES canonical_entities(id),
    source_table VARCHAR(255),       -- 'PATIENT'
    source_column VARCHAR(255),      -- 'PATNR'
    confidence DECIMAL(3,2),
    status VARCHAR(20),              -- 'auto_accepted', 'human_verified', 'rejected'
    reasoning TEXT,                  -- why this mapping
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by UUID,
    UNIQUE(client_id, source_table, source_column)
);

-- Human review queue
CREATE TABLE review_items (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    source_table VARCHAR(255),
    source_column VARCHAR(255),
    proposed_entity_id UUID REFERENCES canonical_entities(id),
    confidence DECIMAL(3,2),
    reasoning TEXT,
    sample_values JSONB,             -- ['value1', 'value2', ...]
    status VARCHAR(20) DEFAULT 'pending', -- pending/approved/rejected
    priority INT DEFAULT 0,          -- higher = review first
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by UUID,
    resolution_notes TEXT
);

-- Audit trail
CREATE TABLE mapping_audit_log (
    id UUID PRIMARY KEY,
    client_id UUID,
    action VARCHAR(50),              -- 'proposed', 'auto_accepted', 'human_approved'
    entity_id UUID,
    source_column VARCHAR(255),
    old_value JSONB,
    new_value JSONB,
    actor_type VARCHAR(20),          -- 'system', 'agent', 'human'
    actor_id VARCHAR(255),           -- user_id or 'matching_engine'
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_variants_column ON column_variants(column_name);
CREATE INDEX idx_variants_entity ON column_variants(entity_id);
CREATE INDEX idx_mappings_client ON client_mappings(client_id);
CREATE INDEX idx_review_pending ON review_items(status) WHERE status = 'pending';
```

---

## Core Algorithm: Multi-Signal Matching

### MatchingEngine Class

```python
from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class MatchCandidate:
    entity_id: str
    entity_name: str
    confidence: float
    match_type: str  # 'exact', 'fuzzy', 'pattern', 'semantic'
    evidence: dict

class MatchingEngine:
    def __init__(self, value_bank: ValueBank, llm_client: Optional[LLMClient] = None):
        self.value_bank = value_bank
        self.llm = llm_client

    def match_column(
        self,
        column_name: str,
        data_type: str,
        sample_values: List[str],
        null_percentage: float
    ) -> List[MatchCandidate]:
        """Multi-signal matching with confidence scoring."""

        candidates = []

        # Signal 1: Exact column name match (highest confidence)
        exact = self.value_bank.exact_match(column_name)
        if exact:
            candidates.append(MatchCandidate(
                entity_id=exact.entity_id,
                entity_name=exact.entity_name,
                confidence=0.95 * exact.occurrence_weight,  # more occurrences = higher
                match_type='exact',
                evidence={'source': 'value_bank', 'occurrences': exact.count}
            ))

        # Signal 2: Fuzzy column name match
        fuzzy_matches = self.fuzzy_match(column_name)
        for match in fuzzy_matches:
            candidates.append(MatchCandidate(
                entity_id=match.entity_id,
                entity_name=match.entity_name,
                confidence=match.similarity * 0.85,  # cap fuzzy at 85%
                match_type='fuzzy',
                evidence={'similarity': match.similarity, 'matched_to': match.variant}
            ))

        # Signal 3: Value pattern match
        if sample_values:
            pattern_match = self.match_by_values(sample_values)
            if pattern_match:
                candidates.append(MatchCandidate(
                    entity_id=pattern_match.entity_id,
                    entity_name=pattern_match.entity_name,
                    confidence=pattern_match.confidence * 0.80,
                    match_type='pattern',
                    evidence={'pattern': pattern_match.pattern, 'matched_values': pattern_match.matched}
                ))

        # Signal 4: LLM semantic match (if no strong candidates)
        if self.llm and (not candidates or max(c.confidence for c in candidates) < 0.7):
            semantic = self.semantic_match(column_name, data_type, sample_values)
            if semantic:
                candidates.append(semantic)

        # Combine signals for same entity
        return self.merge_candidates(candidates)
```

### Fuzzy Matching (Multi-Algorithm)

```python
def fuzzy_match(self, column_name: str) -> List[FuzzyMatch]:
    """Multi-algorithm fuzzy matching."""

    normalized = self.normalize(column_name)  # PATNR -> patnr
    results = []

    for variant in self.value_bank.get_all_variants():
        # Levenshtein (edit distance)
        lev_score = 1 - (levenshtein(normalized, variant.normalized) /
                       max(len(normalized), len(variant.normalized)))

        # Jaro-Winkler (prefix-weighted)
        jw_score = jaro_winkler(normalized, variant.normalized)

        # Token overlap (for compound names)
        tokens_a = set(self.tokenize(column_name))  # PATIENT_NR -> {patient, nr}
        tokens_b = set(self.tokenize(variant.column_name))
        jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b) if tokens_a | tokens_b else 0

        # Weighted combination
        combined = (lev_score * 0.3) + (jw_score * 0.4) + (jaccard * 0.3)

        if combined > 0.75:  # threshold
            results.append(FuzzyMatch(
                entity_id=variant.entity_id,
                entity_name=variant.entity_name,
                variant=variant.column_name,
                similarity=combined
            ))

    return sorted(results, key=lambda x: x.similarity, reverse=True)[:5]
```

### Utility Methods

```python
def normalize(self, name: str) -> str:
    """Normalize column name for comparison."""
    # PATIENT_NR -> patientnr
    # PatientNumber -> patientnumber
    return re.sub(r'[^a-z0-9]', '', name.lower())

def tokenize(self, name: str) -> List[str]:
    """Split column name into tokens."""
    # PATIENT_NR -> ['patient', 'nr']
    # PatientNumber -> ['patient', 'number']
    # Split on underscore, camelCase, numbers
    tokens = re.split(r'[_\s]', name)
    tokens = [t for token in tokens for t in re.split(r'(?<=[a-z])(?=[A-Z])', token)]
    tokens = [t.lower() for t in tokens if t]
    return tokens

def merge_candidates(self, candidates: List[MatchCandidate]) -> List[MatchCandidate]:
    """Merge multiple signals for same entity."""
    by_entity = {}
    for c in candidates:
        if c.entity_id not in by_entity:
            by_entity[c.entity_id] = []
        by_entity[c.entity_id].append(c)

    merged = []
    for entity_id, group in by_entity.items():
        # Multiple signals increase confidence
        base_confidence = max(c.confidence for c in group)
        signal_boost = min(0.10, 0.03 * (len(group) - 1))  # +3% per additional signal

        merged.append(MatchCandidate(
            entity_id=entity_id,
            entity_name=group[0].entity_name,
            confidence=min(0.99, base_confidence + signal_boost),
            match_type='combined' if len(group) > 1 else group[0].match_type,
            evidence={'signals': [c.match_type for c in group], 'details': [c.evidence for c in group]}
        ))

    return sorted(merged, key=lambda x: x.confidence, reverse=True)
```

---

## API Design

### Endpoints

```python
from flask import Blueprint, request, jsonify
from dataclasses import asdict

bp = Blueprint('schema_matching', __name__, url_prefix='/api/schema-matching')

@bp.route('/map', methods=['POST'])
def start_mapping():
    """Start mapping a client database."""
    data = request.json
    # {
    #   "client_id": "uuid",
    #   "connection_string": "...",  # or connection_id reference
    #   "trust_profile": "standard",  # conservative/standard/permissive
    #   "tables": ["PATIENT", "KARTEI"]  # optional filter
    # }

    run_id = matching_service.start_run(
        client_id=data['client_id'],
        connection=data['connection_string'],
        trust_profile=data.get('trust_profile', 'standard'),
        tables=data.get('tables')
    )

    return jsonify({
        'run_id': run_id,
        'status': 'running',
        'status_url': f'/api/schema-matching/status/{run_id}'
    }), 202

@bp.route('/status/<run_id>', methods=['GET'])
def get_status(run_id: str):
    """Get mapping run status."""
    status = matching_service.get_status(run_id)

    return jsonify({
        'run_id': run_id,
        'status': status.state,  # running/pending_review/completed/failed
        'progress': {
            'tables_total': status.tables_total,
            'tables_complete': status.tables_complete,
            'columns_mapped': status.columns_mapped,
            'columns_pending': status.columns_pending,
            'auto_accepted': status.auto_accepted,
            'pending_review': status.pending_review
        },
        'current_table': status.current_table
    })

@bp.route('/mappings/<client_id>', methods=['GET'])
def get_mappings(client_id: str):
    """Get all mappings for a client."""
    mappings = mapping_repo.get_by_client(client_id)

    return jsonify({
        'client_id': client_id,
        'mappings': [
            {
                'entity': m.entity_name,
                'source_table': m.source_table,
                'source_column': m.source_column,
                'confidence': m.confidence,
                'status': m.status
            }
            for m in mappings
        ],
        'coverage': {
            'mapped': len([m for m in mappings if m.status != 'unmapped']),
            'total_columns': mapping_repo.get_column_count(client_id)
        }
    })

@bp.route('/review', methods=['GET'])
def get_review_queue():
    """Get pending reviews."""
    items = review_repo.get_pending(
        client_id=request.args.get('client_id'),
        limit=request.args.get('limit', 20)
    )

    return jsonify({
        'items': [asdict(item) for item in items],
        'total_pending': review_repo.count_pending()
    })

@bp.route('/review/<item_id>', methods=['POST'])
def submit_review(item_id: str):
    """Submit human review decision."""
    data = request.json
    # {
    #   "decision": "approve" | "reject" | "remap",
    #   "entity_id": "uuid",  # if remap
    #   "notes": "..."
    # }

    result = review_service.resolve(
        item_id=item_id,
        decision=data['decision'],
        entity_id=data.get('entity_id'),
        notes=data.get('notes'),
        reviewer_id=current_user.id
    )

    # If approved, add to value bank for future databases
    if data['decision'] == 'approve':
        value_bank.add_variant(
            entity_id=result.entity_id,
            column_name=result.source_column,
            source_client=result.client_id
        )

    return jsonify({'status': 'resolved', 'mapping': asdict(result)})

@bp.route('/value-bank/stats', methods=['GET'])
def value_bank_stats():
    """Get value bank statistics."""
    return jsonify({
        'total_variants': value_bank.count_variants(),
        'total_patterns': value_bank.count_patterns(),
        'entities_covered': value_bank.count_entities(),
        'top_entities': value_bank.get_most_common(10)
    })
```

---

## Trust Profiles

### Configuration

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class TrustProfile:
    name: str
    auto_accept_threshold: float  # >= this = no human review
    review_threshold: float       # >= this = quick review, < this = reject
    critical_always_review: bool  # always review patient_id, etc.

PROFILES: Dict[str, TrustProfile] = {
    'conservative': TrustProfile(
        name='conservative',
        auto_accept_threshold=0.99,  # almost nothing auto-accepts
        review_threshold=0.80,
        critical_always_review=True
    ),
    'standard': TrustProfile(
        name='standard',
        auto_accept_threshold=0.90,
        review_threshold=0.70,
        critical_always_review=True
    ),
    'permissive': TrustProfile(
        name='permissive',
        auto_accept_threshold=0.80,
        review_threshold=0.50,
        critical_always_review=False  # trust high-confidence critical too
    )
}
```

### Decision Logic

```python
def should_auto_accept(confidence: float, entity: Entity, profile: TrustProfile) -> bool:
    """Determine if mapping should auto-accept."""
    if profile.critical_always_review and entity.is_critical:
        return False
    return confidence >= profile.auto_accept_threshold

def should_review(confidence: float, profile: TrustProfile) -> bool:
    """Determine if mapping should go to review queue."""
    return confidence >= profile.review_threshold

def get_decision(confidence: float, entity: Entity, profile: TrustProfile) -> str:
    """Get the decision for a mapping."""
    if should_auto_accept(confidence, entity, profile):
        return 'auto_accept'
    elif should_review(confidence, profile):
        return 'pending_review'
    else:
        return 'rejected'
```

---

## Scalability Patterns

### How It Handles Growth (15 → 150 → 1500 Databases)

| Scale | Challenge | Solution |
|-------|-----------|----------|
| **15** | Manual is slow | Automation saves time per client |
| **150** | Value bank grows large | Index on normalized column names, fuzzy matching with cutoff |
| **1500** | Processing time | Async workers, parallel column analysis |

### Async Processing with Worker Queue

```python
from celery import Celery

celery = Celery('schema_matching')

@celery.task
def process_table(run_id: str, client_id: str, table_name: str):
    """Process single table - parallelizable."""
    profiler = SchemaProfiler(get_connection(client_id))
    columns = profiler.get_columns(table_name)

    for column in columns:
        process_column.delay(run_id, client_id, table_name, column.name)

@celery.task
def process_column(run_id: str, client_id: str, table: str, column: str):
    """Process single column - parallelizable."""
    profiler = SchemaProfiler(get_connection(client_id))
    stats = profiler.get_column_stats(table, column)
    samples = profiler.sample_column(table, column, limit=100)

    engine = MatchingEngine(value_bank)
    candidates = engine.match_column(
        column_name=column,
        data_type=stats.data_type,
        sample_values=samples,
        null_percentage=stats.null_pct
    )

    if candidates:
        best = candidates[0]
        decision = get_decision(best.confidence, best.entity, profile)
        save_mapping(client_id, table, column, best, decision)
```

### Horizontal Scaling Architecture

```
                    ┌─────────────┐
                    │  API Server │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Worker 1 │ │ Worker 2 │ │ Worker N │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┴────────────┘
                          │
                    ┌─────▼─────┐
                    │   Redis   │  (job queue)
                    └───────────┘
                    ┌───────────┐
                    │ PostgreSQL│  (value bank, mappings)
                    └───────────┘
```

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Database** | PostgreSQL | ACID for audit trail, JSONB for flexible evidence storage |
| **Job Queue** | Redis + Celery | Proven, horizontally scalable |
| **API** | Flask/FastAPI | Simple, well-understood |
| **Matching** | Python | Rich ecosystem (jellyfish, fuzzywuzzy, scikit-learn) |
| **LLM** | Claude API | Optional semantic matching for low-confidence cases |

---

## Interview Talking Points

### "How does it scale?"

> "Three levels: First, the value bank compounds—each new database adds knowledge. Second, async workers process tables and columns in parallel. Third, confidence thresholds reduce human review load—by database #10, most columns auto-match."

### "What if the algorithm is wrong?"

> "Trust profiles. Conservative mode auto-accepts almost nothing. Standard balances speed and safety. Plus, critical entities like patient_id always require human review regardless of confidence. Every decision is logged for audit."

### "How is this different from traditional approaches?"

> "Traditional approach: build rules for every pattern. This approach: learn patterns from data. The value bank starts empty and grows. Client #15 benefits from everything learned in clients #1-14. It's a learning system, not a rule system."

### "What about tech stack?"

> "PostgreSQL for the value bank and mappings—need ACID for audit trail. Redis for job queue. Python backend with Celery workers. The matching engine is CPU-bound, not IO-bound, so it scales horizontally with more workers."

---

## Key Differentiators

| Aspect | Traditional | This Solution |
|--------|-------------|---------------|
| **Knowledge** | Static rules | Learning value bank |
| **Human involvement** | All or nothing | Confidence-based trust profiles |
| **Scalability** | Linear (more rules) | Logarithmic (value bank converges) |
| **New client** | Custom code | Benefits from previous clients |
| **Audit** | Manual tracking | Built-in audit log |

---

## References

- [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) - Agent-based alternative approach
- [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) - Test scenarios
- [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) - Test infrastructure
- [DISCUSSION_LOG.md](DISCUSSION_LOG.md) - Design decision history

---

*Created: 2025-01-15*
*Purpose: Interview preparation - technical solution for schema matching at scale*
