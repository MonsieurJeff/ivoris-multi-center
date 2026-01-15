# Archived: Pipeline-Based Design

**Status:** Superseded
**Archived:** 2024-01-15
**Reason:** Replaced by MCP-native agent architecture

---

## Why Archived?

The original design used a 5-stage pipeline approach:
```
Profile → Quality Detection → Classify → Match → Validate
```

This was essentially codifying what an intelligent agent would naturally do. Since the feature was not yet built, we pivoted to an MCP-native design that:

1. Uses an LLM agent with tools instead of rigid stages
2. Reduces code from ~50 files to ~10 files
3. Provides natural language interface
4. Enables flexible, adaptive behavior

---

## Archived Documents

| File | Original Purpose |
|------|------------------|
| `01-basic-methodology.md` | Token-based schema search |
| `02-advanced-methodology.md` | Similarity scoring algorithms |
| `03-value-banks.md` | Learning from verified mappings |
| `04-validation.md` | Validation rules and checks |
| `05-implementation.md` | Code architecture |
| `06-ml-enhancement.md` | Machine learning improvements |
| `07-reference.md` | Quick reference |
| `ARCHITECTURE.md` | Backend structure (Blueprint + Directory) |
| `ACCEPTANCE.md` | Gherkin acceptance criteria |

---

## What Was Preserved

The following concepts from the pipeline design are preserved in the new architecture:

| Concept | New Location |
|---------|--------------|
| Trust profiles | `MCP_ARCHITECTURE.md` - Agent configuration |
| Value banks | MCP Value Bank Server |
| Quality detection | Agent tool: `flag_column` |
| Human-in-the-loop | MCP Review Server |
| Test databases | `DATABASE_SIMULATOR.md` (unchanged) |

---

## Reference

If you need to understand the original thinking, these documents provide valuable context about:

- Similarity algorithms (Levenshtein, Jaro-Winkler, Jaccard)
- Threshold boundaries for quality detection
- Trust profile configurations
- Validation patterns

The new MCP architecture leverages the same domain knowledge but implements it differently.

---

*Archived: 2024-01-15*
