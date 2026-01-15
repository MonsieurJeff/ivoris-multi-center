# MCP Architecture: Automatic Schema Matching

**Purpose:** Map source database columns to canonical entities using an MCP-native agent architecture.
**Approach:** LLM agent with tools instead of rigid pipeline stages.
**Status:** Design

---

## Overview

### The Core Insight

Instead of building a 5-stage pipeline that codifies what an intelligent agent would naturally do, we let the agent decide how to explore and map the schema.

```
┌─────────────────────────────────────────────────────────────┐
│                 SCHEMA MATCHING AGENT                        │
│                                                              │
│  "You are a database schema expert. Map source columns      │
│   to canonical entities. Use tools to explore. Ask          │
│   humans when uncertain."                                    │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ Database │  │  Value   │  │  Human   │
      │  Server  │  │   Bank   │  │  Review  │
      │          │  │  Server  │  │  Server  │
      └──────────┘  └──────────┘  └──────────┘
            │              │              │
            └──────────────┴──────────────┘
                          │
                    MCP SERVERS
```

### Why MCP-Native?

| Aspect | Pipeline Approach | MCP-Native |
|--------|-------------------|------------|
| **Code volume** | ~50 files, ~5000 LOC | ~10 files, ~1000 LOC |
| **Flexibility** | Rigid stages | Agent decides |
| **Explainability** | Logs per stage | Agent reasoning |
| **Human-in-loop** | End of pipeline | Any time |
| **Maintenance** | 5 services | 3 MCP servers |

---

## Architecture

### Directory Structure

```
backend/
├── mcp_servers/
│   ├── __init__.py
│   ├── database_server.py      # Query schemas, sample data
│   ├── value_bank_server.py    # Lookup/add known patterns
│   └── review_server.py        # Human-in-the-loop
│
├── agents/
│   ├── __init__.py
│   └── schema_matching.py      # The agent (prompt + config)
│
├── config/
│   ├── canonical_schema.yml    # What we're mapping TO
│   ├── trust_profiles.yml      # Agent behavior config
│   └── prompts/
│       └── schema_matching.md  # Agent system prompt
│
└── models/
    ├── mapping.py              # Proposed/verified mappings
    ├── value_bank.py           # Learned values
    └── audit.py                # Action log
```

---

## MCP Server 1: Database Server

Provides tools to explore the source database.

### Tools

```yaml
tools:
  - name: list_tables
    description: "List all tables in the database"
    parameters:
      schema_pattern:
        type: string
        description: "Optional filter pattern (e.g., 'PAT%')"
        required: false
    returns:
      type: array
      items:
        type: object
        properties:
          schema: string
          table_name: string
          row_count: integer

  - name: describe_table
    description: "Get column metadata for a table"
    parameters:
      table_name:
        type: string
        required: true
    returns:
      type: array
      items:
        type: object
        properties:
          column_name: string
          data_type: string
          nullable: boolean
          is_primary_key: boolean
          is_foreign_key: boolean

  - name: sample_column
    description: "Get sample values from a column"
    parameters:
      table:
        type: string
        required: true
      column:
        type: string
        required: true
      limit:
        type: integer
        default: 100
    returns:
      type: object
      properties:
        values: array
        null_count: integer
        distinct_count: integer

  - name: column_stats
    description: "Get statistics for a column"
    parameters:
      table:
        type: string
        required: true
      column:
        type: string
        required: true
    returns:
      type: object
      properties:
        null_percentage: number
        distinct_count: integer
        min_value: string
        max_value: string
        most_common: array
        last_updated: string  # For abandoned detection
```

### Implementation

```python
# mcp_servers/database_server.py

from mcp import Server, Tool
from sqlalchemy import create_engine, inspect, text

class DatabaseServer(Server):
    def __init__(self, connection_string: str):
        super().__init__(name="database")
        self.engine = create_engine(connection_string)
        self.inspector = inspect(self.engine)

    @Tool
    def list_tables(self, schema_pattern: str = None) -> list:
        """List all tables, optionally filtered."""
        tables = self.inspector.get_table_names()
        if schema_pattern:
            tables = [t for t in tables if fnmatch(t, schema_pattern)]
        return [
            {
                "table_name": t,
                "row_count": self._get_row_count(t)
            }
            for t in tables
        ]

    @Tool
    def describe_table(self, table_name: str) -> list:
        """Get column metadata."""
        columns = self.inspector.get_columns(table_name)
        pk_cols = self.inspector.get_pk_constraint(table_name)['constrained_columns']
        fk_cols = [fk['constrained_columns'][0]
                   for fk in self.inspector.get_foreign_keys(table_name)]

        return [
            {
                "column_name": col['name'],
                "data_type": str(col['type']),
                "nullable": col['nullable'],
                "is_primary_key": col['name'] in pk_cols,
                "is_foreign_key": col['name'] in fk_cols
            }
            for col in columns
        ]

    @Tool
    def sample_column(self, table: str, column: str, limit: int = 100) -> dict:
        """Get sample values."""
        query = text(f"""
            SELECT [{column}], COUNT(*) as cnt
            FROM [{table}]
            WHERE [{column}] IS NOT NULL
            GROUP BY [{column}]
            ORDER BY cnt DESC
            OFFSET 0 ROWS FETCH NEXT :limit ROWS ONLY
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {"limit": limit})
            values = [row[0] for row in result]

        return {
            "values": values,
            "null_count": self._count_nulls(table, column),
            "distinct_count": len(values)
        }

    @Tool
    def column_stats(self, table: str, column: str) -> dict:
        """Get column statistics."""
        query = text(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN [{column}] IS NULL THEN 1 ELSE 0 END) as nulls,
                COUNT(DISTINCT [{column}]) as distinct_count,
                MIN([{column}]) as min_val,
                MAX([{column}]) as max_val
            FROM [{table}]
        """)

        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()

        return {
            "null_percentage": (row.nulls / row.total * 100) if row.total > 0 else 0,
            "distinct_count": row.distinct_count,
            "min_value": str(row.min_val),
            "max_value": str(row.max_val)
        }
```

---

## MCP Server 2: Value Bank Server

Manages learned patterns from previous mappings.

### Resources

```yaml
resources:
  - uri: "valuebank://entities"
    name: "Canonical Entities"
    description: "List of all canonical entity types"
    mimeType: "application/json"

  - uri: "valuebank://entity/{entity_type}/names"
    name: "Known Column Names"
    description: "Column names that map to this entity"
    mimeType: "application/json"

  - uri: "valuebank://entity/{entity_type}/values"
    name: "Known Values"
    description: "Sample values typical for this entity"
    mimeType: "application/json"

  - uri: "valuebank://entity/{entity_type}/patterns"
    name: "Value Patterns"
    description: "Regex patterns for this entity"
    mimeType: "application/json"
```

### Tools

```yaml
tools:
  - name: check_column_name
    description: "Check if a column name matches known patterns"
    parameters:
      column_name:
        type: string
        required: true
    returns:
      type: object
      properties:
        matches:
          type: array
          items:
            type: object
            properties:
              entity: string
              confidence: number
              source: string  # "exact", "fuzzy", "pattern"

  - name: check_values
    description: "Check if sample values match known entity patterns"
    parameters:
      values:
        type: array
        required: true
      entity_hint:
        type: string
        description: "Optional entity to check against"
        required: false
    returns:
      type: object
      properties:
        matches:
          type: array
          items:
            type: object
            properties:
              entity: string
              confidence: number
              matched_values: array

  - name: add_column_name
    description: "Learn a new column name for an entity (after human verification)"
    parameters:
      entity:
        type: string
        required: true
      column_name:
        type: string
        required: true
      source_client:
        type: string
        required: true
    returns:
      type: object
      properties:
        success: boolean
        message: string

  - name: add_values
    description: "Learn new values for an entity"
    parameters:
      entity:
        type: string
        required: true
      values:
        type: array
        required: true
    returns:
      type: object
      properties:
        added: integer
        duplicates: integer
```

### Implementation

```python
# mcp_servers/value_bank_server.py

from mcp import Server, Tool, Resource
from rapidfuzz import fuzz
import re

class ValueBankServer(Server):
    def __init__(self, db_session):
        super().__init__(name="value_bank")
        self.db = db_session

    @Resource("valuebank://entities")
    def get_entities(self) -> list:
        """List all canonical entities."""
        return [
            {"name": "patient_id", "description": "Patient identifier"},
            {"name": "patient_name", "description": "Patient full name"},
            {"name": "birth_date", "description": "Date of birth"},
            {"name": "insurance_id", "description": "Insurance company ID"},
            {"name": "insurance_name", "description": "Insurance company name"},
            {"name": "insurance_type", "description": "Insurance type code"},
            {"name": "chart_note", "description": "Clinical chart entry"},
            {"name": "appointment_date", "description": "Appointment timestamp"},
            {"name": "procedure_code", "description": "Dental procedure code"},
            {"name": "soft_delete", "description": "Deletion flag"},
            # ... more entities
        ]

    @Tool
    def check_column_name(self, column_name: str) -> dict:
        """Check if column name matches known patterns."""
        matches = []

        # Exact match
        exact = self.db.query(ColumnNameVariant).filter_by(
            name=column_name.upper()
        ).first()
        if exact:
            matches.append({
                "entity": exact.entity,
                "confidence": 1.0,
                "source": "exact"
            })

        # Fuzzy match
        all_variants = self.db.query(ColumnNameVariant).all()
        for variant in all_variants:
            score = fuzz.ratio(column_name.upper(), variant.name) / 100
            if score > 0.8 and variant.entity not in [m['entity'] for m in matches]:
                matches.append({
                    "entity": variant.entity,
                    "confidence": score,
                    "source": "fuzzy"
                })

        return {"matches": sorted(matches, key=lambda x: -x['confidence'])}

    @Tool
    def check_values(self, values: list, entity_hint: str = None) -> dict:
        """Check if values match known patterns."""
        matches = []

        entities_to_check = [entity_hint] if entity_hint else self._get_all_entities()

        for entity in entities_to_check:
            known_values = self._get_known_values(entity)
            patterns = self._get_patterns(entity)

            # Check value overlap
            overlap = set(values) & set(known_values)
            if overlap:
                confidence = len(overlap) / len(values)
                matches.append({
                    "entity": entity,
                    "confidence": confidence,
                    "matched_values": list(overlap)[:10]
                })

            # Check pattern match
            for pattern in patterns:
                matched = [v for v in values if re.match(pattern, str(v))]
                if len(matched) > len(values) * 0.5:
                    matches.append({
                        "entity": entity,
                        "confidence": len(matched) / len(values),
                        "matched_values": matched[:10]
                    })

        return {"matches": sorted(matches, key=lambda x: -x['confidence'])}

    @Tool
    def add_column_name(self, entity: str, column_name: str, source_client: str) -> dict:
        """Add a verified column name variant."""
        variant = ColumnNameVariant(
            entity=entity,
            name=column_name.upper(),
            source_client=source_client,
            verified=True
        )
        self.db.add(variant)
        self.db.commit()
        return {"success": True, "message": f"Added {column_name} → {entity}"}
```

---

## MCP Server 3: Review Server

Handles human-in-the-loop interactions.

### Tools

```yaml
tools:
  - name: propose_mapping
    description: "Propose a column-to-entity mapping"
    parameters:
      table:
        type: string
        required: true
      column:
        type: string
        required: true
      entity:
        type: string
        required: true
      confidence:
        type: number
        required: true
      reasoning:
        type: string
        required: true
    returns:
      type: object
      properties:
        mapping_id: string
        status: string  # "auto_accepted", "pending_review", "rejected"

  - name: ask_human
    description: "Request human decision on an uncertain mapping"
    parameters:
      question:
        type: string
        required: true
      options:
        type: array
        required: true
      context:
        type: object
        description: "Relevant information for decision"
    returns:
      type: object
      properties:
        decision: string
        reasoning: string
        decided_by: string

  - name: flag_column
    description: "Flag a column as problematic"
    parameters:
      table:
        type: string
        required: true
      column:
        type: string
        required: true
      issue:
        type: string
        enum: ["empty", "mostly_empty", "abandoned", "misused", "test_data"]
      evidence:
        type: string
        required: true
    returns:
      type: object
      properties:
        flag_id: string
        requires_review: boolean
```

### Implementation

```python
# mcp_servers/review_server.py

from mcp import Server, Tool
from models import Mapping, ReviewItem, ColumnFlag

class ReviewServer(Server):
    def __init__(self, db_session, trust_profile: dict):
        super().__init__(name="review")
        self.db = db_session
        self.trust = trust_profile

    @Tool
    def propose_mapping(self, table: str, column: str, entity: str,
                        confidence: float, reasoning: str) -> dict:
        """Propose a mapping, auto-accept if above threshold."""

        mapping = Mapping(
            table=table,
            column=column,
            entity=entity,
            confidence=confidence,
            reasoning=reasoning
        )

        # Apply trust profile
        if confidence >= self.trust['auto_accept_threshold']:
            mapping.status = "auto_accepted"
            mapping.verified = True
        elif confidence >= self.trust['review_threshold']:
            mapping.status = "pending_review"
            self._create_review_item(mapping)
        else:
            mapping.status = "rejected"
            mapping.rejection_reason = "Below confidence threshold"

        self.db.add(mapping)
        self.db.commit()

        return {
            "mapping_id": str(mapping.id),
            "status": mapping.status
        }

    @Tool
    def ask_human(self, question: str, options: list, context: dict) -> dict:
        """Create a review item and wait for human decision."""

        review_item = ReviewItem(
            question=question,
            options=options,
            context=context,
            status="pending"
        )
        self.db.add(review_item)
        self.db.commit()

        # In real implementation, this would wait for human response
        # For now, return pending status
        return {
            "review_id": str(review_item.id),
            "status": "pending",
            "message": "Waiting for human review"
        }

    @Tool
    def flag_column(self, table: str, column: str, issue: str,
                    evidence: str) -> dict:
        """Flag a column as problematic."""

        flag = ColumnFlag(
            table=table,
            column=column,
            issue=issue,
            evidence=evidence
        )

        # Auto-exclude 100% empty columns
        if issue == "empty":
            flag.requires_review = False
            flag.auto_excluded = True
        else:
            flag.requires_review = True

        self.db.add(flag)
        self.db.commit()

        return {
            "flag_id": str(flag.id),
            "requires_review": flag.requires_review
        }
```

---

## The Agent

### System Prompt

```markdown
# config/prompts/schema_matching.md

You are a database schema expert helping map source database
columns to a canonical dental practice schema.

## Your Goal

Map each column in the source database to one of these canonical entities:
{canonical_entities}

Or flag it as problematic if it's:
- Empty (100% NULL)
- Mostly empty (>95% NULL)
- Abandoned (no updates in 24+ months)
- Misused (wrong data type for content)
- Test data (debug/test values)

## Your Approach

1. **Explore**: Start by listing tables to understand the schema structure
2. **Investigate**: For each relevant table, examine columns and sample values
3. **Check patterns**: Use the value bank to find known column names and value patterns
4. **Propose**: Make mapping proposals with confidence scores
5. **Ask for help**: When confidence is below {review_threshold}, ask a human

## Trust Profile: {trust_profile_name}

- Auto-accept mappings with confidence >= {auto_accept_threshold}
- Request review for confidence between {review_threshold} and {auto_accept_threshold}
- Reject mappings with confidence < {review_threshold}

## Guidelines

- Explain your reasoning for each mapping
- Look for patterns across similar columns
- Consider table context (FK relationships, table names)
- Flag suspicious columns rather than forcing bad mappings
- Learn from the value bank - it contains verified patterns

## Available Tools

### Database Server
- `list_tables(schema_pattern?)` - List all tables
- `describe_table(table_name)` - Get column metadata
- `sample_column(table, column, limit?)` - Get sample values
- `column_stats(table, column)` - Get NULL%, distinct count, etc.

### Value Bank Server
- `check_column_name(column_name)` - Check for known name patterns
- `check_values(values, entity_hint?)` - Check for known value patterns
- `add_column_name(entity, column_name, source_client)` - Learn new name
- `add_values(entity, values)` - Learn new values

### Review Server
- `propose_mapping(table, column, entity, confidence, reasoning)` - Propose a mapping
- `ask_human(question, options, context)` - Request human decision
- `flag_column(table, column, issue, evidence)` - Flag problematic column
```

### Agent Implementation

```python
# agents/schema_matching.py

from mcp import Agent
from mcp_servers import DatabaseServer, ValueBankServer, ReviewServer

class SchemaMatchingAgent:
    def __init__(self,
                 db_connection: str,
                 trust_profile: str = "standard"):

        # Load configuration
        self.trust = self._load_trust_profile(trust_profile)
        self.canonical_schema = self._load_canonical_schema()
        self.prompt = self._build_prompt()

        # Initialize MCP servers
        self.db_server = DatabaseServer(db_connection)
        self.value_bank = ValueBankServer(get_db_session())
        self.review_server = ReviewServer(get_db_session(), self.trust)

        # Create agent
        self.agent = Agent(
            system_prompt=self.prompt,
            servers=[self.db_server, self.value_bank, self.review_server],
            model="claude-3-sonnet"  # or configured model
        )

    def _build_prompt(self) -> str:
        """Build system prompt with configuration."""
        template = load_prompt_template("schema_matching.md")
        return template.format(
            canonical_entities=self._format_entities(),
            trust_profile_name=self.trust['name'],
            auto_accept_threshold=self.trust['auto_accept_threshold'],
            review_threshold=self.trust['review_threshold']
        )

    async def map_database(self, client_id: str) -> MappingResult:
        """Map the entire database."""
        result = await self.agent.run(
            f"Map the database for client {client_id}. "
            f"Start by exploring the schema, then systematically "
            f"map each column to canonical entities."
        )
        return self._parse_result(result)

    async def map_table(self, client_id: str, table: str) -> MappingResult:
        """Map a single table."""
        result = await self.agent.run(
            f"Map table {table} for client {client_id}."
        )
        return self._parse_result(result)

    async def resume_review(self, mapping_id: str, decision: str) -> MappingResult:
        """Resume after human review decision."""
        result = await self.agent.run(
            f"The human decided: {decision} for mapping {mapping_id}. "
            f"Continue with the remaining mappings."
        )
        return self._parse_result(result)
```

---

## Configuration

### Trust Profiles

```yaml
# config/trust_profiles.yml

profiles:
  conservative:
    name: "Conservative"
    description: "Maximum human oversight, minimum auto-acceptance"
    auto_accept_threshold: 0.99
    review_threshold: 0.80
    require_human_for:
      - critical_entities  # patient_id, insurance_id
      - first_occurrence   # New column names

  standard:
    name: "Standard"
    description: "Balanced automation and oversight"
    auto_accept_threshold: 0.90
    review_threshold: 0.70
    require_human_for:
      - critical_entities

  permissive:
    name: "Permissive"
    description: "Maximum automation, minimal oversight"
    auto_accept_threshold: 0.80
    review_threshold: 0.50
    require_human_for: []

default: standard
```

### Canonical Schema

```yaml
# config/canonical_schema.yml

entities:
  # Patient Domain
  patient_id:
    description: "Unique patient identifier"
    category: "patient"
    risk_class: "critical"
    expected_types: ["INT", "BIGINT", "VARCHAR"]
    patterns:
      - "^\\d+$"
      - "^PAT-\\d+$"
    known_names:
      - "PATNR"
      - "PATIENT_ID"
      - "PAT_ID"
      - "PATIENTENNUMMER"

  patient_name:
    description: "Patient full name or name parts"
    category: "patient"
    risk_class: "important"
    expected_types: ["VARCHAR", "NVARCHAR"]
    known_names:
      - "NAME"
      - "NACHNAME"
      - "VORNAME"
      - "PATIENT_NAME"

  birth_date:
    description: "Patient date of birth"
    category: "patient"
    risk_class: "important"
    expected_types: ["DATE", "DATETIME", "VARCHAR"]
    patterns:
      - "^\\d{8}$"           # YYYYMMDD
      - "^\\d{2}\\.\\d{2}\\.\\d{4}$"  # DD.MM.YYYY
    known_names:
      - "GEBDAT"
      - "GEBURTSDATUM"
      - "BIRTH_DATE"
      - "DOB"

  # Insurance Domain
  insurance_id:
    description: "Insurance company identifier"
    category: "insurance"
    risk_class: "critical"
    known_names:
      - "KASESSION"
      - "KASSEN_ID"
      - "INSURANCE_ID"

  insurance_name:
    description: "Insurance company name"
    category: "insurance"
    risk_class: "important"
    known_values:
      - "DAK Gesundheit"
      - "AOK Bayern"
      - "BARMER"
      - "Techniker Krankenkasse"
      - "CSS Versicherung"
      - "Helsana"
    known_names:
      - "BEZEICHNUNG"
      - "KASSEN_NAME"
      - "INSURANCE_NAME"

  # Chart Domain
  chart_note:
    description: "Clinical chart entry text"
    category: "clinical"
    risk_class: "optional"
    expected_types: ["VARCHAR", "NVARCHAR", "TEXT"]
    known_names:
      - "BEMERKUNG"
      - "NOTIZ"
      - "NOTES"
      - "EINTRAG"

  # ... more entities
```

---

## API Endpoints

Simple REST API to trigger the agent.

```python
# routes/schema_matching.py

from flask import Blueprint, request, jsonify
from agents import SchemaMatchingAgent

bp = Blueprint('schema_matching', __name__)

@bp.route('/api/schema-matching/map', methods=['POST'])
async def map_database():
    """Start mapping a database."""
    data = request.json

    agent = SchemaMatchingAgent(
        db_connection=data['connection_string'],
        trust_profile=data.get('trust_profile', 'standard')
    )

    result = await agent.map_database(data['client_id'])

    return jsonify({
        "run_id": result.run_id,
        "status": result.status,
        "mappings": result.mappings,
        "pending_reviews": result.pending_reviews,
        "flagged_columns": result.flagged_columns
    })

@bp.route('/api/schema-matching/review/<item_id>', methods=['POST'])
async def submit_review():
    """Submit human review decision."""
    data = request.json

    # Update review item
    review = ReviewItem.query.get(item_id)
    review.decision = data['decision']
    review.reasoning = data.get('reasoning')
    review.decided_by = current_user.id
    db.session.commit()

    # Resume agent if needed
    if data.get('resume_agent'):
        agent = SchemaMatchingAgent.resume(review.run_id)
        result = await agent.resume_review(item_id, data['decision'])
        return jsonify(result)

    return jsonify({"status": "recorded"})

@bp.route('/api/schema-matching/status/<run_id>', methods=['GET'])
def get_status():
    """Get mapping run status."""
    run = MappingRun.query.get(run_id)
    return jsonify({
        "status": run.status,
        "progress": run.progress,
        "mappings_complete": run.mappings_complete,
        "pending_reviews": run.pending_reviews
    })
```

---

## Database Models

Minimal models for persistence.

```python
# models/mapping.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from database import Base

class MappingRun(Base):
    __tablename__ = 'schema_matching_runs'

    id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    trust_profile = Column(String, default='standard')
    status = Column(String, default='running')  # running, paused, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    agent_log = Column(JSON)  # Full agent reasoning

class Mapping(Base):
    __tablename__ = 'schema_matching_mappings'

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey('schema_matching_runs.id'))
    table = Column(String, nullable=False)
    column = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    confidence = Column(Float)
    reasoning = Column(String)
    status = Column(String)  # auto_accepted, pending_review, verified, rejected
    verified_by = Column(String)
    verified_at = Column(DateTime)

class ColumnFlag(Base):
    __tablename__ = 'schema_matching_flags'

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey('schema_matching_runs.id'))
    table = Column(String, nullable=False)
    column = Column(String, nullable=False)
    issue = Column(String)  # empty, mostly_empty, abandoned, misused, test_data
    evidence = Column(String)
    auto_excluded = Column(Boolean, default=False)
    reviewed_by = Column(String)

class ReviewItem(Base):
    __tablename__ = 'schema_matching_reviews'

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey('schema_matching_runs.id'))
    mapping_id = Column(String, ForeignKey('schema_matching_mappings.id'))
    question = Column(String)
    options = Column(JSON)
    context = Column(JSON)
    decision = Column(String)
    reasoning = Column(String)
    decided_by = Column(String)
    decided_at = Column(DateTime)
```

---

## Testing

The `DATABASE_SIMULATOR.md` test infrastructure remains valid.

### Agent Testing

```python
# tests/test_schema_matching_agent.py

import pytest
from agents import SchemaMatchingAgent

@pytest.fixture
def agent():
    return SchemaMatchingAgent(
        db_connection="mssql://localhost:1433/test_db",
        trust_profile="standard"
    )

async def test_maps_obvious_columns(agent):
    """Agent should auto-accept obvious mappings."""
    result = await agent.map_table("client_test", "PATIENT")

    # PATNR should be auto-accepted as patient_id
    patnr_mapping = find_mapping(result, "PATNR")
    assert patnr_mapping.entity == "patient_id"
    assert patnr_mapping.status == "auto_accepted"
    assert patnr_mapping.confidence >= 0.90

async def test_asks_for_uncertain_columns(agent):
    """Agent should request review for uncertain mappings."""
    result = await agent.map_table("client_test", "KARTEI")

    # BEMERKUNG might be uncertain
    if find_mapping(result, "BEMERKUNG").confidence < 0.90:
        assert find_mapping(result, "BEMERKUNG").status == "pending_review"

async def test_flags_empty_columns(agent):
    """Agent should flag 100% NULL columns."""
    result = await agent.map_table("client_test", "PATIENT")

    # FAX column is 100% NULL in test data
    fax_flag = find_flag(result, "FAX")
    assert fax_flag.issue == "empty"
    assert fax_flag.auto_excluded == True
```

---

## References

- [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) - Test database design
- [DISCUSSION_LOG.md](DISCUSSION_LOG.md) - Design decision history
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Future enhancements
- [archive/pipeline-design/](archive/pipeline-design/) - Original pipeline design (archived)

---

*Created: 2024-01-15*
*Architecture: MCP-Native Agent*
*Status: Design*
