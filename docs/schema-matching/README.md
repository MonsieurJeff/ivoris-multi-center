# Automatic Schema Matching

**MCP-Native Agent Architecture** | Schema Discovery & Mapping

---

## Overview

**Automatic Schema Matching** uses an LLM agent with MCP (Model Context Protocol) tools to discover and map unknown database schemas to a canonical business schema. The agent explores databases, identifies patterns, and proposes mappings—asking humans when uncertain.

```
┌─────────────────────────────────────────────────────────────┐
│                 SCHEMA MATCHING AGENT                        │
│                                                              │
│  "Map source columns to canonical entities.                 │
│   Use tools to explore. Ask humans when uncertain."         │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ Database │  │  Value   │  │  Human   │
      │  Server  │  │   Bank   │  │  Review  │
      └──────────┘  └──────────┘  └──────────┘
```

### When to Use

- Receiving a customer database with no documentation
- Data integration between systems
- Legacy system migration
- Multi-center deployments with varying schemas per location

### The Challenge

Given requirements in business language, find the actual database columns:

| Requirement | Business Meaning | Agent Finds... |
|-------------|------------------|----------------|
| Pat-ID | Patient identifier | PATNR, PATIENT_NR, PAT_ID |
| Versicherung | Insurance company | KASSEN, INSURANCE, VERSICHERUNG |
| Karteieintrag | Chart entry | BEMERKUNG, NOTIZ, NOTES |
| Geburtsdatum | Birth date | GEBDAT, GEBURTSDATUM, DOB |

---

## Quick Start

### Core Documentation (`core/`)

| Document | Purpose |
|----------|---------|
| [IMPLEMENTATION_ROADMAP.md](core/IMPLEMENTATION_ROADMAP.md) | **Start here** - Ordered tasks from scratch to production |
| [TECHNICAL_SOLUTION.md](core/TECHNICAL_SOLUTION.md) | Architecture and code patterns |
| [MCP_ARCHITECTURE.md](core/MCP_ARCHITECTURE.md) | Agent-based architecture with MCP servers |
| [CANONICAL_ENTITIES.md](core/CANONICAL_ENTITIES.md) | Target schema definition and known variants |
| [ACCEPTANCE_CRITERIA.md](core/ACCEPTANCE_CRITERIA.md) | Gherkin acceptance criteria |
| [DATABASE_SIMULATOR.md](core/DATABASE_SIMULATOR.md) | Test databases (10 simulated centers) |

### Interview Preparation (`interview/`)

| Document | Purpose |
|----------|---------|
| [INTERVIEW_QUESTIONS.md](interview/INTERVIEW_QUESTIONS.md) | Questions to ask, positioning strategies |
| [TEAM_STRUCTURE.md](interview/TEAM_STRUCTURE.md) | Team roles, task assignment, leadership approach |
| [AGENTIC_TEAM_MANAGEMENT.md](interview/AGENTIC_TEAM_MANAGEMENT.md) | Quality management with AI-assisted development |
| [PRACTICAL_GOVERNANCE.md](interview/PRACTICAL_GOVERNANCE.md) | Real experience from OutrePilot/Outrepreneur |
| [COMPETITIVE_ANALYSIS.md](interview/COMPETITIVE_ANALYSIS.md) | How we compare to Informatica, AWS Glue, Tamr |
| [COST_BENEFIT.md](interview/COST_BENEFIT.md) | ROI analysis, break-even, 3-year projections |
| [DEMO_SCRIPT.md](interview/DEMO_SCRIPT.md) | 15-20 minute walkthrough for stakeholders |
| [CODING_EXERCISES.md](interview/CODING_EXERCISES.md) | Senior-level technical discussion prep |
| [GLOSSARY.md](interview/GLOSSARY.md) | Terminology quick reference |

### Reference (`reference/`)

| Document | Purpose |
|----------|---------|
| [IMPROVEMENTS.md](reference/IMPROVEMENTS.md) | Future enhancements |
| [DISCUSSION_LOG.md](reference/DISCUSSION_LOG.md) | Design decision history |

---

## Architecture

### Three MCP Servers

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| **Database Server** | Query source database | `list_tables`, `describe_table`, `sample_column`, `column_stats` |
| **Value Bank Server** | Lookup learned patterns | `check_column_name`, `check_values`, `add_column_name` |
| **Review Server** | Human-in-the-loop | `propose_mapping`, `ask_human`, `flag_column` |

### Agent Behavior

The agent:
1. **Explores** the database schema
2. **Checks** the value bank for known patterns
3. **Proposes** mappings with confidence scores
4. **Asks humans** when confidence is below threshold
5. **Learns** new patterns for future databases

### Trust Profiles

| Profile | Auto-Accept | Review | Use Case |
|---------|-------------|--------|----------|
| **Conservative** | ≥99% | ≥80% | First client, critical data |
| **Standard** | ≥90% | ≥70% | Normal operations |
| **Permissive** | ≥80% | ≥50% | Trusted schemas, demos |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Canonical Schema** | Target entities we're mapping to (patient_id, insurance_name, etc.) |
| **Value Bank** | Learned column names and values from verified mappings |
| **Trust Profile** | Configuration for auto-accept vs human-review thresholds |
| **MCP Server** | Standardized tool/resource provider for the agent |

---

## Test Infrastructure

10 simulated dental center databases organized by zone:

| Zone | Centers | Purpose | Expected Match Rate |
|------|---------|---------|---------------------|
| **A** | 1-2 | Synthetic extremes (break the system) | 0-40% |
| **B** | 3-4 | Realistic chaos (handle gracefully) | 50-65% |
| **C** | 5-7 | Moderate variations (test learning) | 75-85% |
| **D** | 8-10 | Clean baselines (verify accuracy) | 90-98% |

See [DATABASE_SIMULATOR.md](core/DATABASE_SIMULATOR.md) for details.

---

## Why MCP-Native?

The original design used a 5-stage pipeline:
```
Profile → Quality Detection → Classify → Match → Validate
```

This was essentially codifying what an intelligent agent would naturally do. With MCP:

| Aspect | Pipeline | MCP-Native |
|--------|----------|------------|
| **Code** | ~50 files | ~10 files |
| **Flexibility** | Rigid stages | Agent decides |
| **Human-in-loop** | End of pipeline | Any time |
| **Explainability** | Stage logs | Agent reasoning |

The original pipeline design is archived at [archive/pipeline-design/](archive/pipeline-design/).

---

## File Structure

```
automatic-schema-matching/
├── README.md                    # This file (index)
│
├── core/                        # Core technical documentation
│   ├── IMPLEMENTATION_ROADMAP.md    # Ordered tasks: scratch → production
│   ├── TECHNICAL_SOLUTION.md        # Architecture and code patterns
│   ├── MCP_ARCHITECTURE.md          # Agent-based architecture
│   ├── CANONICAL_ENTITIES.md        # Target schema and known variants
│   ├── ACCEPTANCE_CRITERIA.md       # Test scenarios
│   └── DATABASE_SIMULATOR.md        # Test database design
│
├── interview/                   # Interview preparation materials
│   ├── INTERVIEW_QUESTIONS.md       # Questions to ask, positioning
│   ├── TEAM_STRUCTURE.md            # Team roles and task assignment
│   ├── AGENTIC_TEAM_MANAGEMENT.md   # AI-assisted development quality
│   ├── PRACTICAL_GOVERNANCE.md      # Real OutrePilot/Outrepreneur experience
│   ├── COMPETITIVE_ANALYSIS.md      # Market comparison
│   ├── COST_BENEFIT.md              # ROI and business case
│   ├── DEMO_SCRIPT.md               # Stakeholder presentation
│   ├── CODING_EXERCISES.md          # Senior-level technical prep
│   └── GLOSSARY.md                  # Terminology reference
│
├── reference/                   # Additional reference materials
│   ├── IMPROVEMENTS.md              # Future enhancements
│   └── DISCUSSION_LOG.md            # Decision history
│
└── archive/
    └── pipeline-design/         # Original pipeline approach (superseded)
```

---

## Status

| Component | Status |
|-----------|--------|
| Architecture design | Complete |
| Acceptance criteria | Complete |
| Test infrastructure | Complete |
| Implementation | Not started |

---

*This methodology was developed through real-world schema discovery on the Ivoris dental practice management system (487+ tables, German column names, no documentation) and evolved to an MCP-native agent architecture.*
