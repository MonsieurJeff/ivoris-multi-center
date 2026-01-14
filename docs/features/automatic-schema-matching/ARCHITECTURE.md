# Backend Architecture: Automatic Schema Matching

**Purpose:** Define the backend structure for the Automatic Schema Matching feature.
**Decision:** Use both a **Blueprint** (route organization) and a **Feature Directory** (code organization).

---

## Why Both?

| Mechanism | What It Provides | Why We Need It |
|-----------|------------------|----------------|
| **Blueprint** | URL namespacing, route grouping, feature toggle | Multiple API endpoints (`/api/schema-matching/*`) |
| **Directory** | Code boundaries, discoverability, ownership | 5+ phases, 10+ services, complex orchestration |

### Decision Criteria Met

- [x] Has 3+ API endpoints (profile, classify, match, validate, pipeline, review, config)
- [x] Has 3+ services/modules (profiler, classifier, matcher, validator, value_bank, trust)
- [x] Could be disabled/enabled independently (feature flag)
- [x] Complex enough for its own documentation (you're reading it)
- [x] Multiple phases with distinct responsibilities

---

## Proposed Directory Structure

```
backend/
├── features/
│   └── schema_matching/
│       ├── __init__.py              # Package exports + blueprint registration
│       ├── blueprint.py             # API routes
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── profiler.py          # Phase 1: Schema profiling
│       │   ├── quality_detector.py  # Phase 1b: Column quality detection
│       │   ├── classifier.py        # Phase 2: LLM classification
│       │   ├── matcher.py           # Phase 3: Cross-database matching
│       │   ├── validator.py         # Phase 4: Auto-validation
│       │   └── value_bank.py        # Value bank management
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── orchestrator.py      # Full pipeline runner
│       │   ├── jobs.py              # Background/async tasks
│       │   └── state.py             # Pipeline state machine
│       │
│       ├── trust/
│       │   ├── __init__.py
│       │   ├── profiles.py          # Trust profile definitions
│       │   ├── risk_classes.py      # Entity risk classification
│       │   ├── thresholds.py        # Effective threshold calculation
│       │   └── adaptive.py          # Adaptive trust tracking
│       │
│       ├── review/
│       │   ├── __init__.py
│       │   ├── queue.py             # Review queue management
│       │   ├── actions.py           # Approve/reject/override logic
│       │   └── notifications.py     # Review notifications
│       │
│       ├── config.py                # Feature configuration loader
│       ├── exceptions.py            # Feature-specific exceptions
│       └── constants.py             # Enums, constants
│
├── models/                          # Shared models (for DB migrations)
│   └── schema_matching/
│       ├── __init__.py
│       ├── profile.py               # ColumnProfile, TableProfile
│       ├── classification.py        # Classification, ClassificationCache
│       ├── mapping.py               # ColumnMapping, VerifiedMapping
│       ├── value_bank.py            # ValueBankEntry, ColumnVariant
│       ├── column_quality.py        # ColumnQualityLabel
│       ├── review.py                # ReviewQueueItem, ReviewAction
│       ├── audit.py                 # AuditLogEntry
│       └── pipeline.py              # PipelineRun, PipelineState
│
└── app.py                           # Blueprint registration
```

---

## Component Responsibilities

### Services

| Service | Phase | Responsibility |
|---------|-------|----------------|
| `profiler.py` | 1 | Extract column metadata, sample values, statistics |
| `quality_detector.py` | 1b | Detect empty, abandoned, misused, test-only columns |
| `classifier.py` | 2 | LLM-based semantic classification |
| `matcher.py` | 3 | Match against canonical schema, composite scoring |
| `validator.py` | 4 | Run validation tests (FK, dates, insurance, etc.) |
| `value_bank.py` | — | Manage learned values, column variants |

### Pipeline

| Module | Responsibility |
|--------|----------------|
| `orchestrator.py` | Run full pipeline, manage phase transitions |
| `jobs.py` | Background task definitions (Celery/RQ/etc.) |
| `state.py` | Pipeline state machine (PROFILING → CLASSIFYING → ...) |

### Trust

| Module | Responsibility |
|--------|----------------|
| `profiles.py` | Load trust profiles (conservative, standard, permissive) |
| `risk_classes.py` | Map entities to risk classes (critical, important, optional) |
| `thresholds.py` | Calculate effective threshold: `max(profile, entity_min)` |
| `adaptive.py` | Track accuracy, auto-tighten, suggest relaxation |

### Review

| Module | Responsibility |
|--------|----------------|
| `queue.py` | Add/remove items from review queue, filtering |
| `actions.py` | Process approve/reject/override actions |
| `notifications.py` | Send review notifications (email, Slack) |

---

## API Endpoints (Blueprint)

```python
# backend/features/schema_matching/blueprint.py

from flask import Blueprint

bp = Blueprint('schema_matching', __name__)

# ─────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────

@bp.route('/pipeline/start', methods=['POST'])
def start_pipeline():
    """Start onboarding pipeline for a client."""
    pass

@bp.route('/pipeline/<run_id>/status', methods=['GET'])
def get_pipeline_status(run_id):
    """Get current pipeline status."""
    pass

@bp.route('/pipeline/<run_id>/resume', methods=['POST'])
def resume_pipeline(run_id):
    """Resume paused pipeline."""
    pass

# ─────────────────────────────────────────────────────────────────────
# PHASES (Manual/Debug)
# ─────────────────────────────────────────────────────────────────────

@bp.route('/profile', methods=['POST'])
def run_profiling():
    """Run Phase 1 profiling only."""
    pass

@bp.route('/classify', methods=['POST'])
def run_classification():
    """Run Phase 2 classification only."""
    pass

@bp.route('/match', methods=['POST'])
def run_matching():
    """Run Phase 3 matching only."""
    pass

@bp.route('/validate', methods=['POST'])
def run_validation():
    """Run Phase 4 validation only."""
    pass

# ─────────────────────────────────────────────────────────────────────
# REVIEW QUEUE
# ─────────────────────────────────────────────────────────────────────

@bp.route('/review/queue', methods=['GET'])
def get_review_queue():
    """Get pending review items."""
    pass

@bp.route('/review/<item_id>/approve', methods=['POST'])
def approve_item(item_id):
    """Approve a review item."""
    pass

@bp.route('/review/<item_id>/reject', methods=['POST'])
def reject_item(item_id):
    """Reject a review item."""
    pass

@bp.route('/review/bulk', methods=['POST'])
def bulk_review():
    """Bulk approve/reject items."""
    pass

# ─────────────────────────────────────────────────────────────────────
# VALUE BANKS
# ─────────────────────────────────────────────────────────────────────

@bp.route('/value-bank/<entity>', methods=['GET'])
def get_value_bank(entity):
    """Get values for an entity."""
    pass

@bp.route('/value-bank/<entity>/pending', methods=['GET'])
def get_pending_values(entity):
    """Get pending values for review."""
    pass

@bp.route('/value-bank/value/<value_id>/verify', methods=['POST'])
def verify_value(value_id):
    """Verify a pending value."""
    pass

@bp.route('/value-bank/value/<value_id>/reject', methods=['POST'])
def reject_value(value_id):
    """Reject a pending value."""
    pass

# ─────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

@bp.route('/config', methods=['GET'])
def get_config():
    """Get current feature configuration."""
    pass

@bp.route('/config/trust-profile', methods=['PUT'])
def set_trust_profile():
    """Set trust profile for a client."""
    pass

# ─────────────────────────────────────────────────────────────────────
# AUDIT
# ─────────────────────────────────────────────────────────────────────

@bp.route('/audit', methods=['GET'])
def get_audit_log():
    """Query audit log."""
    pass

# ─────────────────────────────────────────────────────────────────────
# FINAL APPROVAL
# ─────────────────────────────────────────────────────────────────────

@bp.route('/approve/<run_id>', methods=['POST'])
def approve_for_production(run_id):
    """Final approval for production deployment."""
    pass
```

---

## Blueprint Registration

```python
# backend/features/schema_matching/__init__.py

from .blueprint import bp

__all__ = ['bp']
```

```python
# backend/app.py

from flask import Flask
from backend.features.schema_matching import bp as schema_matching_bp

def create_app():
    app = Flask(__name__)

    # ... other setup ...

    # Register schema matching feature
    app.register_blueprint(
        schema_matching_bp,
        url_prefix='/api/schema-matching'
    )

    return app
```

---

## Models Location Decision

**Decision:** Models go in shared `models/` directory, not in feature directory.

**Rationale:**
1. Database migrations need access to all models
2. Other features might reference these models (e.g., extraction uses mappings)
3. Consistent with existing codebase patterns
4. SQLAlchemy model discovery works better with centralized models

**Trade-off:** Slightly less isolation, but better for DB operations.

---

## Configuration Loading

```python
# backend/features/schema_matching/config.py

from dataclasses import dataclass
from typing import Dict, List
import yaml

@dataclass
class TrustProfile:
    name: str
    auto_accept_threshold: float
    review_required_before_production: bool
    auto_exclude_flagged_columns: bool
    auto_verify_high_occurrence_values: bool

@dataclass
class RiskClass:
    name: str
    entities: List[str]
    minimum_confidence: float
    validation_required: bool

@dataclass
class SchemaMatchingConfig:
    trust_profiles: Dict[str, TrustProfile]
    default_trust_profile: str
    risk_classes: Dict[str, RiskClass]
    # ... other config sections

def load_config(path: str = 'config/schema-matching.yml') -> SchemaMatchingConfig:
    """Load feature configuration from YAML."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return SchemaMatchingConfig(**data)

# Singleton for app-wide access
_config: SchemaMatchingConfig = None

def get_config() -> SchemaMatchingConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config
```

---

## Service Pattern

Each service follows a consistent pattern:

```python
# backend/features/schema_matching/services/profiler.py

from typing import List, Optional
from dataclasses import dataclass
import logging

from backend.models.schema_matching import ColumnProfile
from ..config import get_config

logger = logging.getLogger(__name__)

@dataclass
class ProfilingResult:
    profiles: List[ColumnProfile]
    tables_profiled: int
    columns_profiled: int
    duration_seconds: float
    estimated_columns: int  # Columns where stats were estimated

class SchemaProfiler:
    """Phase 1: Extract rich metadata from database columns."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.config = get_config()

    def profile_schema(self, schema_name: str) -> ProfilingResult:
        """Profile all columns in a schema."""
        logger.info(f"Starting profiling for schema: {schema_name}")
        # ... implementation ...

    def profile_table(self, schema: str, table: str) -> List[ColumnProfile]:
        """Profile a single table."""
        # ... implementation ...

    def _extract_sample_values(self, schema: str, table: str, column: str) -> List[str]:
        """Extract representative sample values."""
        # ... implementation ...

    def _detect_patterns(self, sample_values: List[str]) -> dict:
        """Detect data patterns in samples."""
        # ... implementation ...
```

---

## Pipeline Orchestrator Pattern

```python
# backend/features/schema_matching/pipeline/orchestrator.py

from enum import Enum
from typing import Optional
import logging

from ..services import SchemaProfiler, QualityDetector, Classifier, Matcher, Validator
from ..trust import get_effective_threshold
from ..review import ReviewQueue
from ..config import get_config
from backend.models.schema_matching import PipelineRun, PipelineState

logger = logging.getLogger(__name__)

class PipelinePhase(Enum):
    PENDING = "pending"
    PROFILING = "profiling"
    QUALITY_CHECK = "quality_check"
    CLASSIFYING = "classifying"
    MATCHING = "matching"
    VALIDATING = "validating"
    AWAITING_REVIEW = "awaiting_review"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

class SchemaMappingPipeline:
    """Orchestrate the full schema matching pipeline."""

    def __init__(self, client_id: str, db_connection, trust_profile: str = None):
        self.client_id = client_id
        self.db = db_connection
        self.config = get_config()
        self.trust_profile = trust_profile or self.config.default_trust_profile

        # Initialize services
        self.profiler = SchemaProfiler(db_connection)
        self.quality_detector = QualityDetector(db_connection)
        self.classifier = Classifier(self.config)
        self.matcher = Matcher(self.config)
        self.validator = Validator(db_connection)
        self.review_queue = ReviewQueue()

    def run(self, schema_name: str) -> PipelineRun:
        """Run the full pipeline."""
        run = PipelineRun.create(
            client_id=self.client_id,
            schema_name=schema_name,
            trust_profile=self.trust_profile
        )

        try:
            # Phase 1: Profile
            run.set_phase(PipelinePhase.PROFILING)
            profiles = self.profiler.profile_schema(schema_name)

            # Phase 1b: Quality Detection
            run.set_phase(PipelinePhase.QUALITY_CHECK)
            quality_results = self.quality_detector.analyze(profiles)
            self._handle_flagged_columns(quality_results, run)

            # Phase 2: Classification
            run.set_phase(PipelinePhase.CLASSIFYING)
            classifications = self.classifier.classify_batch(
                profiles.good_columns,
                effective_threshold=get_effective_threshold(self.trust_profile)
            )
            self._handle_low_confidence(classifications, run)

            # Phase 3: Matching
            run.set_phase(PipelinePhase.MATCHING)
            mappings = self.matcher.match_all(classifications)
            self._handle_medium_confidence(mappings, run)

            # Phase 4: Validation
            run.set_phase(PipelinePhase.VALIDATING)
            validation_results = self.validator.validate_all(mappings)
            self._handle_validation_issues(validation_results, run)

            # Check if review needed
            if self.review_queue.has_pending_items(run.id):
                run.set_phase(PipelinePhase.AWAITING_REVIEW)
            else:
                run.set_phase(PipelinePhase.AWAITING_APPROVAL)

            return run

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            run.set_phase(PipelinePhase.FAILED, error=str(e))
            raise

    def resume(self, run_id: str) -> PipelineRun:
        """Resume a paused pipeline."""
        # ... implementation ...

    def _handle_flagged_columns(self, quality_results, run):
        """Add flagged columns to review queue based on trust profile."""
        # ... implementation based on trust profile ...
```

---

## Testing Strategy

```
tests/
└── features/
    └── schema_matching/
        ├── __init__.py
        ├── conftest.py              # Fixtures (test DB, mock LLM, etc.)
        │
        ├── unit/
        │   ├── test_profiler.py
        │   ├── test_classifier.py
        │   ├── test_matcher.py
        │   ├── test_validator.py
        │   ├── test_trust_profiles.py
        │   └── test_thresholds.py
        │
        ├── integration/
        │   ├── test_pipeline.py
        │   ├── test_review_flow.py
        │   └── test_value_bank.py
        │
        └── e2e/
            ├── test_first_client.py
            ├── test_second_client.py
            └── test_trust_profiles.py
```

---

## Implementation Order

Recommended order for building this feature:

| Phase | Components | Dependencies |
|-------|------------|--------------|
| 1 | Models, Config loader | None |
| 2 | Profiler service | Models |
| 3 | Quality detector | Profiler |
| 4 | Value bank service | Models |
| 5 | Classifier service | Config, Value bank |
| 6 | Matcher service | Classifier, Value bank |
| 7 | Validator service | Matcher |
| 8 | Trust module | Config |
| 9 | Review queue | Trust, Models |
| 10 | Pipeline orchestrator | All services |
| 11 | Blueprint (API) | Pipeline, Review |
| 12 | Background jobs | Pipeline |

---

## Open Questions for Implementation

1. **Background job framework:** Celery? RQ? Built-in threading?
2. **LLM integration:** Direct API? Langchain? Custom gateway?
3. **Database:** Same DB as app? Separate schema? Separate DB?
4. **Caching:** Redis for classification cache? In-memory?
5. **Notifications:** Email service? Slack webhook? Both?

---

## References

- [ACCEPTANCE.md](ACCEPTANCE.md) - Gherkin acceptance criteria
- [05-implementation.md](05-implementation.md) - Code architecture details
- [DISCUSSION_LOG.md](DISCUSSION_LOG.md) - Design decision history

---

*Created: 2024-01-14*
*Status: Planning*
