# Project Methodology

**How I Built the Ivoris Multi-Center Pipeline**

This document explains the systematic approach used to build this project, following enterprise patterns from OutrePilot even for an interview coding challenge.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Project Initialization](#project-initialization)
3. [Challenge → Acceptance → Implementation Flow](#challenge--acceptance--implementation-flow)
4. [Architecture Decisions](#architecture-decisions)
5. [Pattern Alignment with OutrePilot](#pattern-alignment-with-outrepilot)
6. [Best Practices Applied](#best-practices-applied)
7. [What I Would Do Differently](#what-i-would-do-differently)
8. [Lessons Learned](#lessons-learned)

---

## Philosophy

### Why Follow Enterprise Patterns for an Interview Project?

1. **Demonstrate how I actually work** - Not just solving the problem, but solving it professionally
2. **Show scalability thinking** - The same approach works for 10 or 1000 centers
3. **Prove maintainability** - Code that others can read, modify, and extend
4. **Build muscle memory** - Practicing good patterns makes them automatic

### Core Principles

| Principle | Application |
|-----------|-------------|
| **Start with requirements** | CHALLENGE.md before any code |
| **Define "done" first** | ACCEPTANCE.md with Gherkin criteria |
| **Separate concerns** | core/, services/, adapters/, models/ |
| **Human-in-the-loop** | `reviewed: false` flag on mappings |
| **Fail gracefully** | Error handling at every layer |

---

## Project Initialization

### Step 1: Create from Template

```bash
# From OutrePilot repo root
cp -r sandbox/_template sandbox/ivoris-multi-center
cd sandbox/ivoris-multi-center
```

### Step 2: Register in Sandbox Registry

```yaml
# sandbox/registry.yml
projects:
  - id: ivoris-multi-center
    name: Ivoris Multi-Center Extraction Pipeline
    description: Extract from 30 dental centers with automatic schema discovery
    status: active
    owner: Jean-Francois Desjardins
    created: "2026-01-13"
    target: Standalone tool (interview project)
    tech_stack:
      - python
      - sql-server
      - docker
    tags:
      - interview
      - data-extraction
      - multi-tenant
      - schema-discovery
```

### Step 3: Define the Challenge

Before writing any code, I documented the challenge requirements:

```markdown
# CHALLENGE.md

## The Problem
- 30 dental centers with random schemas
- Same logical data, different physical names
- Need unified extraction

## Requirements
1. Schema auto-discovery
2. Canonical model
3. Unified extraction
4. Performance target: <5 seconds
```

### Step 4: Write Acceptance Criteria

Using Gherkin format to define exactly what "done" means:

```gherkin
# ACCEPTANCE.md

Feature: Schema Auto-Discovery
  Scenario: Discover tables from database
    Given a database "DentalDB_A1" with tables suffixed "_A1"
    When I run schema introspection
    Then I should discover table "KARTEI_A1" as canonical "KARTEI"
```

### Step 5: Set Up Infrastructure

```bash
# docker-compose.yml for SQL Server
docker-compose up -d

# requirements.txt for Python
pip install -r requirements.txt
```

### Step 6: Implement in Layers

Following the template structure:
1. `src/models/` - Define data structures first
2. `src/core/` - Core algorithms (discovery, mapping)
3. `src/adapters/` - Database connections
4. `src/services/` - Orchestration (extraction, parallel)
5. `src/cli/` - User interface
6. `src/web/` - Bonus: Web UI

---

## Challenge → Acceptance → Implementation Flow

### The Flow

```
CHALLENGE.md          →  What problem are we solving?
       ↓
ACCEPTANCE.md         →  How do we know it's solved?
       ↓
Architecture Design   →  How will we structure the solution?
       ↓
Implementation        →  Build it layer by layer
       ↓
Validation            →  Check against acceptance criteria
```

### Example: Schema Discovery Feature

**1. Challenge (from CHALLENGE.md):**
> Each center has tables like KARTEI_A1, KARTEI_B2... need to discover them automatically.

**2. Acceptance Criteria (from ACCEPTANCE.md):**
```gherkin
Scenario: Discover tables from database
  Given a database "DentalDB_A1" with tables suffixed "_A1"
  When I run schema introspection
  Then I should discover table "KARTEI_A1" as canonical "KARTEI"
```

**3. Architecture Decision:**
- Query INFORMATION_SCHEMA (standard, portable)
- Pattern matching on table names
- JSON mapping files for persistence

**4. Implementation:**
```python
# src/core/discovery.py
class SchemaDiscovery:
    def discover(self, schema_filter: str = "ck") -> DiscoveredSchema:
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ?
        """, (schema_filter,))
        ...
```

**5. Validation:**
```bash
python -m src.cli discover-raw -c center_01
# Verify output matches acceptance criteria
```

---

## Architecture Decisions

### Decision 1: Raw Discovery vs Smart Interpretation

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| Smart auto-mapping | No human review needed | Could make errors silently |
| Raw discovery + manual mapping | Human verification | More work |
| **Raw discovery + generated proposals** | Best of both | Slight complexity |

**Chosen:** Raw discovery with generated proposals + `reviewed` flag

**Why:** Production safety. Pattern matching could be wrong. Human reviews before extraction runs.

### Decision 2: JSON Mapping Files vs Database

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| Store in database | Query-able, centralized | Harder to diff, review |
| **JSON files** | Git-trackable, human-readable | Need to sync |
| YAML files | Same as JSON | More complex parsing |

**Chosen:** JSON files in `data/mappings/`

**Why:**
- Can be version-controlled
- Easy to review in code review
- Can diff between versions
- Human-readable

### Decision 3: Parallel Execution Strategy

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| Sequential | Simple | Slow (30 × RTT) |
| **ThreadPoolExecutor** | Simple, effective | Not truly async |
| asyncio + aioodbc | Maximum performance | More complex |
| multiprocessing | True parallelism | Overhead for I/O |

**Chosen:** ThreadPoolExecutor with 5 workers (default)

**Why:**
- Simple to implement and debug
- Database I/O is the bottleneck, not CPU
- Good enough: 380ms vs 5000ms target
- Can increase workers if needed

### Decision 4: Web UI Framework

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| Flask + Jinja2 | Familiar | Older patterns |
| **FastAPI + Jinja2** | Modern, async-ready, auto-docs | Learning curve |
| React SPA | Rich UI | Overkill for demo |
| Streamlit | Quick prototyping | Less control |

**Chosen:** FastAPI + Jinja2 + Tailwind CSS

**Why:**
- FastAPI is modern, has great docs
- Jinja2 templates for server-rendered HTML
- Tailwind for quick styling without custom CSS
- Chart.js for visualizations

---

## Pattern Alignment with OutrePilot

### Directory Structure (from Template)

```
OutrePilot Template              This Project
─────────────────────            ─────────────────────
src/                             src/
├── core/                        ├── core/
│   └── business logic           │   ├── config.py
│                                │   ├── discovery.py
│                                │   ├── introspector.py
│                                │   └── schema_mapping.py
├── services/                    ├── services/
│   └── orchestration            │   ├── extraction.py
│                                │   └── mapping_generator.py
├── adapters/                    ├── adapters/
│   └── external systems         │   └── center_adapter.py
├── models/                      ├── models/
│   └── data structures          │   └── chart_entry.py
└── main.py                      └── cli/main.py
```

### Naming Conventions

| OutrePilot Pattern | This Project |
|--------------------|--------------|
| `snake_case` for files | `chart_entry.py`, `schema_mapping.py` |
| `PascalCase` for classes | `ChartEntry`, `SchemaMapping` |
| `snake_case` for functions | `extract_chart_entries()`, `discover_schema()` |
| Descriptive names | `mapping_generator.py` not `gen.py` |

### Error Handling

```python
# OutrePilot pattern: catch specific, log, re-raise or return error
try:
    result = adapter.extract_chart_entries(date)
except pyodbc.Error as e:
    logger.error(f"Database error for {center.id}: {e}")
    return CenterResult(center_id=center.id, error=str(e))
```

### Configuration Pattern

```python
# OutrePilot pattern: YAML config loaded into dataclass
@dataclass
class Config:
    database: DatabaseConfig
    centers: list[CenterConfig]

def load_config() -> Config:
    with open("config/centers.yml") as f:
        data = yaml.safe_load(f)
    return Config(...)
```

### Service Layer Pattern

```python
# OutrePilot pattern: services orchestrate, don't contain business logic
class ExtractionService:
    def __init__(self, config: Config):
        self.config = config

    def extract_all(self, date: date) -> ExtractionResult:
        # Orchestration logic here
        # Delegates to adapters for actual work
```

---

## Best Practices Applied

### 1. Single Responsibility

Each file/class does ONE thing:

| File | Single Responsibility |
|------|----------------------|
| `discovery.py` | Query INFORMATION_SCHEMA |
| `mapping_generator.py` | Generate mapping JSON from discovery |
| `introspector.py` | Load and cache mapping files |
| `center_adapter.py` | Generate SQL and execute queries |
| `extraction.py` | Parallel orchestration |

### 2. Dependency Injection

```python
# Services receive dependencies, don't create them
class ExtractionService:
    def __init__(self, config: Config):  # Injected
        self.config = config

# Not this:
class ExtractionService:
    def __init__(self):
        self.config = load_config()  # Hidden dependency
```

### 3. Type Hints Everywhere

```python
def extract_chart_entries(
    self,
    target_date: date,
    center_ids: list[str] | None = None,
    max_workers: int = 5,
) -> ExtractionResult:
```

### 4. Dataclasses for Models

```python
@dataclass
class ChartEntry:
    date: int
    patient_id: int
    insurance_status: str
    chart_entry: str

    def to_dict(self) -> dict:
        return asdict(self)
```

### 5. Guard Clauses

```python
def extract(self, center_id: str) -> list[ChartEntry]:
    # Guard clause - fail fast
    if center_id not in self.available_centers:
        raise ValueError(f"Unknown center: {center_id}")

    # Happy path continues...
```

### 6. Logging, Not Print

```python
import logging
logger = logging.getLogger(__name__)

# Not print(), which can't be controlled
logger.info(f"Extracting from {center.name}")
logger.error(f"Failed: {e}")
```

### 7. Context Managers

```python
# Database connections properly closed
with self._get_connection() as conn:
    cursor = conn.cursor()
    # ...
# Connection automatically closed
```

### 8. Configuration Over Hardcoding

```yaml
# config/centers.yml - can add centers without code changes
centers:
  - id: center_01
    name: Zahnarztpraxis München
    database: DentalDB_01
```

---

## What I Would Do Differently

### With More Time

1. **Async extraction** - Use `asyncio` + `aioodbc` for true concurrent I/O
2. **Proper test suite** - Unit tests for each module, integration tests
3. **Streaming exports** - For large datasets, stream to file instead of memory
4. **Incremental extraction** - Track last extracted timestamp, only get new
5. **Monitoring** - Prometheus metrics, health checks

### Architecture Improvements

1. **Repository pattern** - Abstract database access behind interface
2. **Event sourcing** - Log all extractions for audit trail
3. **Config validation** - Pydantic models for config with validation
4. **CLI framework** - Use `click` or `typer` for richer CLI

### Production Hardening

1. **Connection pooling** - Reuse connections across requests
2. **Retry logic** - Automatic retry with exponential backoff
3. **Circuit breaker** - Stop hitting failing centers
4. **Rate limiting** - Don't overwhelm databases

---

## Lessons Learned

### What Worked Well

| Decision | Why It Worked |
|----------|---------------|
| JSON mapping files | Easy to debug, version control, review |
| `reviewed` flag | Clear production safety checkpoint |
| ThreadPoolExecutor | Simple enough, fast enough |
| FastAPI + Jinja2 | Quick to build, looks professional |
| Gherkin acceptance criteria | Clear definition of "done" |

### What Was Challenging

| Challenge | How I Solved It |
|-----------|-----------------|
| Random suffixes per column (not just table) | More granular pattern matching |
| Joining across randomly-named tables | Dynamic SQL generation |
| Validating discovery accuracy | Ground truth comparison |
| Making web UI look good quickly | Tailwind CSS + Chart.js |

### Key Insights

1. **Pattern-based discovery scales** - Same code works for 10 or 1000 centers
2. **Human checkpoints matter** - Automation is great, but humans catch edge cases
3. **Good enough beats perfect** - 380ms is fine when target is 5000ms
4. **Documentation pays off** - CHALLENGE.md and ACCEPTANCE.md saved debugging time

### For Future Projects

1. **Start with acceptance criteria** - Knowing "done" prevents scope creep
2. **Use templates** - Consistent structure across projects
3. **Separate discovery from interpretation** - Raw data first, then mapping
4. **Build CLI before UI** - Faster iteration, UI is just a wrapper

---

## Summary

This project demonstrates:

1. **Systematic approach** - Challenge → Acceptance → Implementation
2. **Enterprise patterns** - Even for interview projects
3. **Production thinking** - Human review, error handling, logging
4. **Scalable architecture** - Works for N centers without code changes
5. **Professional documentation** - Not just code, but methodology

The same approach used for this interview project is how I would approach any production system - start with requirements, define success criteria, design for maintainability, and build incrementally.
