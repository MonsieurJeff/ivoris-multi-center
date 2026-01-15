# Agentic Team Management

**Purpose:** How to lead a team effectively when AI writes most of the code
**Context:** Modern development with Claude Code, Cursor, Copilot, etc.

---

## The Shift

```
TRADITIONAL                          AGENTIC
─────────────────────────────────────────────────────────────────
Developer writes code     →     Developer reviews AI-generated code
Hours to implement        →     Minutes to generate
Quality from experience   →     Quality from validation
Knowledge in heads        →     Knowledge in prompts + reviews
```

**The fundamental change:** Developers become **architects and validators**, not typists.

---

## Quality Management Framework

### The Problem

AI generates code fast. But:
- It doesn't understand your architecture
- It may introduce subtle bugs
- It can create inconsistent patterns
- It might miss security implications

**Speed without quality = technical debt at scale.**

### The Solution: Three Gates

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY GATES                                 │
│                                                                  │
│   GATE 1              GATE 2              GATE 3                │
│   ────────            ────────            ────────              │
│   Pre-Generation      Post-Generation     Pre-Merge             │
│                                                                  │
│   • Clear intent      • Human review      • Automated tests     │
│   • Architecture      • Pattern check     • Security scan       │
│   • Constraints       • Test coverage     • Performance check   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Gate 1: Pre-Generation (Intent)

**Before the AI writes anything, define:**

| Element | Description | Example |
|---------|-------------|---------|
| **Intent** | What problem are we solving? | "Add confidence scoring to matching" |
| **Constraints** | What must it respect? | "Use existing similarity functions" |
| **Patterns** | What patterns to follow? | "Match the service layer structure" |
| **Non-goals** | What should it NOT do? | "Don't refactor unrelated code" |

### CICA Framework

| Letter | Meaning | Purpose |
|--------|---------|---------|
| **C** | Context | Current state, relevant files |
| **I** | Intent | Goal, success criteria |
| **C** | Constraints | Rules, patterns, limits |
| **A** | Acceptance | How we know it's done |

**Example prompt structure:**
```
Context: We have a matching engine in src/matching/
Intent: Add Jaro-Winkler similarity as an option
Constraints: Follow existing algorithm interface, don't modify Levenshtein
Acceptance: Unit tests pass, can select algorithm via config
```

---

## Gate 2: Post-Generation (Review)

### Human Review Checklist

**Every AI-generated PR must be reviewed for:**

| Category | Check | Why |
|----------|-------|-----|
| **Understanding** | Can reviewer explain what the code does? | Prevents "vibe coding" |
| **Architecture** | Does it fit the system design? | AI doesn't know your architecture |
| **Patterns** | Does it match existing conventions? | AI generates inconsistently |
| **Security** | Any injection, auth, or data exposure risks? | AI often misses security |
| **Performance** | Any obvious inefficiencies? | AI optimizes for "works", not "fast" |
| **Tests** | Are tests meaningful, not just present? | AI writes tests that pass, not tests that catch bugs |

### Anti-Patterns to Watch

| Anti-Pattern | Description | Example |
|--------------|-------------|---------|
| **Vibe Coding** | Accepting code you don't understand | "It works, ship it" |
| **Over-Generation** | AI wrote more than needed | Asked for 1 function, got 10 |
| **Pattern Drift** | AI used different patterns than codebase | REST in a GraphQL project |
| **Shallow Tests** | Tests that don't actually validate | `assert True` |
| **Comment Lies** | Comments that don't match code | AI copies comments from training data |

### Review Questions

Ask yourself:
1. "Could I have written this myself?" (If no, you don't understand it)
2. "Would I be comfortable debugging this at 2 AM?"
3. "Does this match how we do things here?"

---

## Gate 3: Pre-Merge (Automation)

### Required Automated Checks

| Check | Tool | Purpose |
|-------|------|---------|
| **Unit Tests** | pytest, jest | Correctness |
| **Integration Tests** | Custom harness | System behavior |
| **Type Checking** | mypy, TypeScript | Type safety |
| **Linting** | ruff, eslint | Code style |
| **Security Scan** | bandit, semgrep | Vulnerability detection |
| **Coverage** | coverage.py | Test completeness |

### CI Pipeline for Agentic Code

```yaml
# .github/workflows/pr-check.yml
name: PR Quality Gate

on: [pull_request]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Type Check
        run: mypy src/

      - name: Lint
        run: ruff check src/

      - name: Security Scan
        run: bandit -r src/

      - name: Unit Tests
        run: pytest tests/ --cov=src --cov-fail-under=80

      - name: Integration Tests
        run: pytest tests/integration/
```

---

## Team Roles in Agentic Development

### Role Evolution

| Traditional Role | Agentic Role | Key Shift |
|------------------|--------------|-----------|
| **Junior Dev** | AI Operator + Learner | Learns by reviewing AI output, not writing |
| **Mid Dev** | Validator + Integrator | Reviews AI code, ensures patterns |
| **Senior Dev** | Architect + Quality Lead | Designs systems AI implements, final review |
| **Tech Lead** | Orchestrator + Guardrail | Sets standards, defines quality gates |

### New Responsibilities

#### Tech Lead (You)
```
OLD: Write the hardest code
NEW:
- Define architecture AI must follow
- Set quality standards
- Review critical AI-generated code
- Train team on effective AI usage
- Build guardrails (linting rules, templates)
```

#### Senior Developer
```
OLD: Implement complex features
NEW:
- Design component interfaces
- Review all AI-generated PRs
- Maintain pattern consistency
- Mentor on AI prompt engineering
- Own critical algorithm implementations (don't trust AI)
```

#### Mid Developer
```
OLD: Implement features independently
NEW:
- Generate code with AI assistance
- Validate AI output against patterns
- Write meaningful tests
- Document AI decisions
- Flag pattern violations
```

#### Junior Developer
```
OLD: Learn by writing code
NEW:
- Learn by reviewing AI code
- Understand WHY code works
- Run and validate AI output
- Ask "what does this do?"
- Build mental models through review
```

---

## Quality Metrics for Agentic Teams

### Track These

| Metric | What It Shows | Target |
|--------|---------------|--------|
| **PR Review Time** | How long to validate AI code | < 30 min |
| **Rework Rate** | How often AI code needs fixing | < 20% |
| **Test Coverage** | AI-generated test quality | > 80% |
| **Pattern Violations** | AI following conventions | < 5% |
| **Security Issues Found** | Catching AI security mistakes | 0 in prod |
| **Understanding Score** | Can team explain the code? | 100% |

### Understanding Score

**Weekly check:** Pick random AI-generated function, ask author to explain it.

| Score | Meaning | Action |
|-------|---------|--------|
| 5 | Can explain every line | Ship it |
| 4 | Understands intent and approach | Ship it |
| 3 | Knows what it does, not how | Review needed |
| 2 | Vague understanding | Rewrite |
| 1 | No idea | Reject, train developer |

---

## Process Adaptations

### Daily Standup Addition

Add to standup:
> "Any AI-generated code you're unsure about?"

This normalizes asking for help and catches vibe coding early.

### Code Review Protocol

```
1. AUTHOR explains the AI prompt used
2. AUTHOR explains what the code does (not reads it)
3. REVIEWER checks against patterns
4. REVIEWER runs the code locally
5. BOTH discuss edge cases
6. MERGE only if both understand it
```

### Documentation Requirements

For AI-generated code, document:
```python
# AI-GENERATED: 2024-01-15
# Prompt: "Add Jaro-Winkler similarity function matching existing interface"
# Reviewed by: @senior_dev
# Modifications: Fixed edge case for empty strings (line 23-25)
def jaro_winkler_similarity(s1: str, s2: str) -> float:
    ...
```

---

## Knowledge Management

### The Knowledge Problem

Traditional: Developers learn by writing code
Agentic: Developers might not understand code they "wrote"

### Solutions

| Problem | Solution |
|---------|----------|
| **Shallow understanding** | Mandatory explanation in PR |
| **Lost context** | Document AI prompts |
| **Pattern inconsistency** | Linting rules + templates |
| **Debugging difficulty** | Require local testing before PR |

### Team Learning Sessions

Weekly 30-min session:
1. Pick an AI-generated component
2. One person explains it line-by-line
3. Team asks questions
4. Document learnings

---

## Interview Talking Points

### On Quality Management

> "When AI writes code, quality management becomes the primary job. We shift from 'did you write it correctly' to 'did you validate it correctly.' I implement three gates: clear intent before generation, human review after, and automated checks before merge."

### On Team Roles

> "In agentic development, the senior developer's job isn't to write the hardest code—it's to ensure the AI-generated code fits our architecture. They become the pattern guardian. The tech lead's job is to build guardrails: linting rules, templates, and quality gates that catch problems automatically."

### On The Risks

> "The biggest risk is 'vibe coding'—accepting AI output because it works without understanding it. I combat this by requiring developers to explain code in PR reviews. If you can't explain it, you can't merge it."

### On Junior Developers

> "Junior developers in an agentic team learn differently. Instead of learning by writing, they learn by reviewing. Every PR review is a teaching moment. The AI shows one way to solve the problem; the review teaches why it's right or wrong."

---

## Quick Reference: Quality Checklist

### Before AI Generation
- [ ] Clear intent documented
- [ ] Constraints specified
- [ ] Target patterns identified
- [ ] Acceptance criteria defined

### After AI Generation
- [ ] Developer can explain the code
- [ ] Matches existing patterns
- [ ] No security red flags
- [ ] Tests are meaningful
- [ ] No over-generation

### Before Merge
- [ ] All automated checks pass
- [ ] Code reviewed by human
- [ ] Reviewer also understands it
- [ ] Documentation updated
- [ ] AI prompt documented (if significant)

---

## Summary: The Golden Rule

**"AI writes code, humans ensure quality."**

The faster AI generates code, the more important quality gates become. Your job as a leader is to:

1. **Define clear intent** before AI generates
2. **Build strong review culture** to catch issues
3. **Automate everything automatable** in CI
4. **Ensure understanding** through explanation
5. **Guard patterns** through linting and templates

---

*Speed is meaningless without quality. In agentic development, quality management IS the job.*
