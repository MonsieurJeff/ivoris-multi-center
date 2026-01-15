# Documentation

This folder contains all documentation for the Ivoris Multi-Center project.

## Structure

```
docs/
├── README.md                    # This file (index)
│
├── # Shared Documentation
├── METHODOLOGY.md               # How I built this (patterns, decisions)
├── TECH_SPEC.md                 # Requirements, specs, scalability
├── SECURITY.md                  # Authentication, secrets, GDPR
├── OPERATIONS.md                # Production runbook
├── TESTING.md                   # Test strategy
│
├── ivoris-pipeline/             # Daily extraction pipeline
│   ├── SCRIPT.md                # Presentation script
│   ├── STORY.md                 # Narrative arc
│   ├── QUICK_REFERENCE.md       # Commands & examples
│   ├── DEMO_CHECKLIST.md        # Pre-demo checklist
│   ├── QUICK_CARD.md            # One-page reference
│   └── coding-session/          # Step-by-step walkthrough
│
└── schema-matching/             # Automatic schema matching
    ├── README.md                # Project overview
    ├── core/                    # Technical documentation
    ├── interview/               # Interview preparation
    └── reference/               # Additional materials
```

---

## Interview Topics

### 1. Ivoris Pipeline (`ivoris-pipeline/`)

Daily extraction pipeline for Ivoris dental software.

| Document | Purpose |
|----------|---------|
| [SCRIPT.md](ivoris-pipeline/SCRIPT.md) | Presentation talking points |
| [STORY.md](ivoris-pipeline/STORY.md) | Narrative structure |
| [QUICK_REFERENCE.md](ivoris-pipeline/QUICK_REFERENCE.md) | Commands & file reference |
| [coding-session/](ivoris-pipeline/coding-session/) | Step-by-step hands-on walkthrough |

### 2. Schema Matching (`schema-matching/`)

Automatic column mapping for unknown databases.

| Document | Purpose |
|----------|---------|
| [README.md](schema-matching/README.md) | **Start here** - Project overview |
| [core/](schema-matching/core/) | Technical documentation |
| [interview/](schema-matching/interview/) | Interview preparation materials |

---

## Shared Documentation

### Architecture & Design

| Document | Purpose |
|----------|---------|
| [Tech Spec](TECH_SPEC.md) | Requirements, specs, scalability to 500+ centers |
| [Methodology](METHODOLOGY.md) | How I built this: templates, patterns, decisions |

### Production Readiness

| Document | Purpose |
|----------|---------|
| [Security](SECURITY.md) | Authentication, secrets management, GDPR compliance |
| [Operations](OPERATIONS.md) | Production runbook, monitoring, troubleshooting |
| [Testing](TESTING.md) | Test strategy, examples, CI/CD integration |

---

## Project Docs (Root Level)

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview |
| [CHALLENGE.md](../CHALLENGE.md) | Challenge requirements |
| [ACCEPTANCE.md](../ACCEPTANCE.md) | Gherkin acceptance criteria |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |

---

## Reading Order

### For Ivoris Pipeline

1. [CHALLENGE.md](../CHALLENGE.md) - The original requirement
2. [ivoris-pipeline/STORY.md](ivoris-pipeline/STORY.md) - The narrative
3. [ivoris-pipeline/SCRIPT.md](ivoris-pipeline/SCRIPT.md) - Presentation script
4. [ivoris-pipeline/coding-session/](ivoris-pipeline/coding-session/) - Hands-on walkthrough

### For Schema Matching

1. [schema-matching/README.md](schema-matching/README.md) - Overview
2. [schema-matching/core/IMPLEMENTATION_ROADMAP.md](schema-matching/core/IMPLEMENTATION_ROADMAP.md) - Implementation plan
3. [schema-matching/interview/](schema-matching/interview/) - Interview prep materials

### For Technical Deep-Dive

1. [TECH_SPEC.md](TECH_SPEC.md) - Requirements, database, Docker, scalability
2. [METHODOLOGY.md](METHODOLOGY.md) - Patterns, decisions, lessons learned
3. [schema-matching/core/TECHNICAL_SOLUTION.md](schema-matching/core/TECHNICAL_SOLUTION.md) - Architecture

### For Production Deployment

1. [SECURITY.md](SECURITY.md) - Auth, secrets, GDPR
2. [OPERATIONS.md](OPERATIONS.md) - Runbook, monitoring, troubleshooting
3. [TESTING.md](TESTING.md) - Test strategy, CI/CD
