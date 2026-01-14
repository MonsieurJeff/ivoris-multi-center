# Automatic Schema Matching

**Best Practice Guide** | Schema Discovery & Mapping Methodology

---

## Overview

**Automatic Schema Matching** is a methodology for discovering and mapping unknown database schemas to business requirements. It combines token-based search, similarity scoring, LLM semantic classification, value banks (matching clusters), and cross-database learning to find candidate table/column mappings.

### When to Use

- Receiving a customer database with no documentation
- Data integration between systems
- Legacy system migration
- Reverse engineering database schemas
- **Multi-center deployments** with varying schemas per location

### The Challenge

Given requirements in business language, find the actual database columns:

| Requirement (German) | Business Meaning | We Need to Find... |
|---------------------|------------------|-------------------|
| Datum | Date | Date column in chart entries |
| Pat-ID | Patient ID | Patient identifier |
| Versicherungsstatus | Insurance Status | GKV/PKV classification |
| Karteikarteneintrag | Chart Entry | Medical notes |
| Leistungen (Ziffern) | Services | Treatment codes |

---

## Quick Start

| Your Situation | Start Here |
|----------------|------------|
| Single database, manual mapping | [Basic Methodology](01-basic-methodology.md) |
| Multi-database, need automation | [Advanced Methodology](02-advanced-methodology.md) |
| Want to learn from past mappings | [Value Banks](03-value-banks.md) |
| Need validation and confidence scoring | [Validation](04-validation.md) |
| Ready to add ML | [ML Enhancement](06-ml-enhancement.md) |

---

## Table of Contents

### Core Methodology

1. **[Basic Methodology](01-basic-methodology.md)** - Single Database
   - 3-Phase Approach (Token Search → Similarity → Ranking)
   - SQL queries for schema exploration
   - String similarity algorithms (Levenshtein, Jaro-Winkler, Jaccard)

2. **[Advanced Methodology](02-advanced-methodology.md)** - Multi-Database with LLM
   - 4-Phase Pipeline (Profile → Classify → Match → Validate)
   - Schema Profiler with data sampling
   - LLM Semantic Classification
   - Cross-Database Matching with canonical schema

3. **[Value Banks](03-value-banks.md)** - Matching Clusters
   - Learning from verified values
   - Canonical schema with value banks
   - Database schema for Clinero
   - Growth strategy over time

### Operations

4. **[Validation](04-validation.md)** - Quality Assurance
   - Auto-validation tests (FK joins, date validity, etc.)
   - Confidence scoring model
   - Human-in-the-loop workflow

5. **[Implementation](05-implementation.md)** - Code Architecture
   - Project structure
   - Pipeline orchestration
   - LLM considerations and cost optimization

### Enhancement

6. **[ML Enhancement](06-ml-enhancement.md)** - Machine Learning
   - Embedding-based value matching
   - Few-shot LLM prompting
   - Feature logging for future ML
   - Traditional ML (Phase 2+)
   - ML integration roadmap

### Reference

7. **[Reference](07-reference.md)** - Quick Reference
   - Case study: Ivoris Multi-Center
   - Checklists for schema discovery
   - SQL query templates
   - Bibliography

---

## Methodology Comparison

| Approach | Best For | Automation Level | Documentation |
|----------|----------|------------------|---------------|
| **Basic (3-Phase)** | Single database, manual review | Low | [01-basic-methodology.md](01-basic-methodology.md) |
| **Advanced (4-Phase)** | Multiple databases, repeated mapping | High | [02-advanced-methodology.md](02-advanced-methodology.md) |
| **With Value Banks** | Learning from previous clients | Higher | [03-value-banks.md](03-value-banks.md) |
| **With ML** | 50+ databases, maximum automation | Highest | [06-ml-enhancement.md](06-ml-enhancement.md) |

---

## Key Concepts

| Concept | Description | Details |
|---------|-------------|---------|
| **Canonical Schema** | Golden reference of expected fields and their known column name variants | [02-advanced-methodology.md](02-advanced-methodology.md#canonical-schema-definition) |
| **Value Bank** | Learned collection of verified values per canonical entity | [03-value-banks.md](03-value-banks.md) |
| **Confidence Threshold** | ≥0.85 auto-accept, 0.60-0.84 review, <0.60 investigate | [04-validation.md](04-validation.md#confidence-thresholds) |
| **Human-in-the-Loop** | All mappings verified by human before storing | [04-validation.md](04-validation.md#human-in-the-loop-workflow) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE MATCHING PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CLIENT ONBOARDING                                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                                                                    │ │
│  │  Profile  →  Value Bank  →  Embeddings  →  ML  →  LLM  →  Human   │ │
│  │  Schema      Match          Match          (opt)  Fallback  Review │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│       │                                                                  │
│       ▼                                                                  │
│  VERIFIED MAPPINGS STORED                                               │
│       │                                                                  │
│       ▼                                                                  │
│  DAILY OPERATIONS (No LLM, uses stored mappings)                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*This methodology was developed through real-world schema discovery on the Ivoris dental practice management system (487+ tables, German column names, no documentation) and extended for multi-center deployments.*
