# The Story

**Narrative Arc for Presentation**

This document helps you tell a compelling story, not just show a demo.

---

## The Three-Act Structure

```
ACT 1: THE PROBLEM          →  "Here's the chaos"
ACT 2: THE SOLUTION         →  "Here's how I tamed it"
ACT 3: THE PROOF            →  "Here's the evidence it works"
```

---

## Act 1: The Problem (Setup)

### The Hook (First 10 seconds)

Start with the **pain point**, not the solution:

> "Imagine you need to extract patient data from 30 dental clinics. Same software, same data structure - should be easy, right? Except... every single database has different table and column names."

### The Villain: Chaos

The "villain" of your story is **schema chaos**:

| What They Expect | What They Got |
|------------------|---------------|
| `KARTEI` | `KARTEI_MN`, `KARTEI_8Y`, `KARTEI_XQ4`... |
| `PATNR` | `PATNR_NAN6`, `PATNR_DZ`, `PATNR_R2Z5`... |
| One query fits all | 30 different queries needed |

### Why This Matters

Connect to real stakes:

> "In the real world, this happens when dental practices migrate software, merge with other practices, or just have... creative IT departments. You can't ask 30 clinics to rename their databases. You have to adapt."

### The Stakes

What happens if you fail:

- Manual work for each center (doesn't scale)
- Hardcoded mappings (breaks when schemas change)
- Errors in patient data (dangerous)

---

## Act 2: The Solution (Confrontation)

### The Hero: Pattern-Based Discovery

Your solution is the "hero" that conquers the chaos:

> "Instead of fighting the randomness, I embraced it. The key insight: even random names follow a pattern. `KARTEI_MN` still has `KARTEI` in it. `PATNR_NAN6` still starts with `PATNR`."

### The Journey (4 Steps)

Tell it as a sequence:

**Step 1: See the Truth**
> "First, I had to see what's actually there. Raw discovery - query the database's `INFORMATION_SCHEMA`, no assumptions, just facts."

**Step 2: Find the Pattern**
> "Then, pattern matching. Strip the random suffix, find the canonical name. `KARTEI_XYZ` becomes `KARTEI`."

**Step 3: Human Checkpoint**
> "Here's the key architectural decision - I don't trust the pattern matching blindly. Every mapping file has a `reviewed: false` flag. In production, a human verifies before extraction runs."

**Step 4: Scale It**
> "Finally, parallel execution. All 30 centers at once, using ThreadPoolExecutor. Each center uses its own mapping, outputs to a unified format."

### The Architectural Choices (Why These Matter)

| Choice | Why It Matters |
|--------|----------------|
| JSON mapping files | Human-readable, git-trackable, debuggable |
| `reviewed` flag | Production safety - catch mapping errors before they corrupt data |
| Ground truth separation | Can validate discovery accuracy |
| Parallel extraction | Scales linearly - 30 centers in <500ms |

### The Turning Point

> "The moment it clicked: this isn't about solving one extraction. It's about building a system that handles ANY schema variation, for ANY number of centers."

---

## Act 3: The Proof (Resolution)

### Show, Don't Tell

This is where the demo does the talking:

| Claim | Proof |
|-------|-------|
| "Handles random schemas" | `discover-raw` shows chaos, `show-mapping` shows order |
| "Works for all 30" | `benchmark` runs all 30 successfully |
| "Fast enough" | <500ms vs 5000ms target |
| "Human-verifiable" | Web UI shows mappings, Schema Diff validates |

### The Numbers

End with concrete results:

```
30 dental centers
30 unique schemas
<500ms total extraction
100% pattern match accuracy
0 hardcoded mappings
```

### The Transformation

Before → After story:

> "Before: 30 different queries, manual mapping, error-prone.
> After: One command, automatic discovery, verified mappings, unified output."

---

## Emotional Beats

### Where to Pause

1. **After showing the chaos** - Let them feel the problem
2. **After the `reviewed: false` explanation** - This shows you think about production
3. **After benchmark results** - Let the numbers sink in

### Where to Add Energy

1. **The hook** - Start with confidence
2. **The turning point** - Show enthusiasm for the solution
3. **The results** - Pride in what you built

### Where to Stay Calm

1. **Technical explanations** - Clear and steady
2. **Demo commands** - Deliberate, not rushed
3. **Error recovery** - If something breaks, stay composed

---

## Key Messages (What They Should Remember)

If they remember only THREE things:

1. **The problem is real** - Random schemas happen in production
2. **The solution is systematic** - Pattern-based discovery, not hardcoding
3. **The safety is built-in** - Human review before extraction

---

## Transitions

### Problem → Solution

> "So how do you handle this? You don't fight the randomness - you find the pattern within it."

### Solution → Demo

> "Let me show you what this looks like in practice..."

### Demo → Results

> "Now let's see if it actually works at scale..."

### Results → Wrap Up

> "So there you have it - 30 databases, 30 random schemas, one unified pipeline."

---

## The One-Sentence Summary

If you had to summarize in one sentence:

> "I built a pattern-based schema discovery system that extracts dental patient data from 30 centers with randomly-named tables, using auto-generated mappings with human review checkpoints."

---

## Anti-Patterns (What to Avoid)

### Don't:

- Start with "So I built this thing..." (boring)
- List features without context (no story)
- Rush through the demo (anxiety shows)
- Apologize for the code (confidence matters)
- End with "I guess that's it" (weak close)

### Do:

- Start with the problem (creates tension)
- Explain WHY before HOW (motivation)
- Pause after key moments (let it land)
- Own your decisions (confidence)
- End with clear results (strong close)

---

## Practice Prompts

Before recording, answer these out loud:

1. "What's the hardest part of this problem?"
2. "Why did I choose JSON files over a database?"
3. "What would break if I removed the `reviewed` flag?"
4. "What would I do differently with more time?"

Being able to answer these smoothly shows you understand your own system.
