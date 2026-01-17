# Clinero Roadmap - Master Internal Document

**Status:** INTERNAL - Complete overview for Jean-Francois
**Created:** 2026-01-17
**Trial Day:** ~2026-01-31 (2 weeks)
**Purpose:** Single source of truth for Clinero opportunity

---

## Executive Summary

| Item | Status |
|------|--------|
| **Opportunity** | AI Founding Engineer → CTO at Clinero GmbH |
| **Company** | 6 months old, 15 clients, sole founder (Max Haase) |
| **Your leverage** | No technical co-founder, OutrePilot, Ivoris expertise |
| **Target compensation** | €70-80k + 10-15% equity + OutrePilot license value |
| **Timeline** | 2 weeks to trial day, ~4 weeks to contract |
| **Key risk** | Used for knowledge, left with nothing |
| **Key protection** | Written agreement before starting |

---

## Document Map

| Document | Location | Purpose |
|----------|----------|---------|
| **This Roadmap** | `ROADMAP_INTERNAL.md` | Master overview |
| **Decision Diamond (Personal)** | `DECISION_DIAMOND_PERSONAL.md` | YOUR converged position (use this!) |
| **Decision Diamond (Framework)** | `DECISION_TRIANGLE_INTERNAL.md` | Full theory + extensions |
| **Compensation Models** | `COMPENSATION_MODELS_INTERNAL.md` | Financial scenarios, protections |
| **Questions for Max** | `QUESTIONS_FOR_MAX.md` | What to send/ask |
| **Demo Strategy** | `OUTREPILOT_DEMO_STRATEGY.md` | How to showcase OutrePilot |
| **Interview Prep** | `../INTERVIEW_PREP_2026-01-17.md` | Original call prep |

---

# Current State Analysis (Codebase Assessment)

**Assessment Date:** 2026-01-17
**Overall Production Readiness:** ~92%

---

## OutrePilot Status

| Component | Status | Details |
|-----------|--------|---------|
| **AgentOps Framework** | ✅ WORKING | Full governance + validation model |
| **OutreRalph** | ✅ WORKING | 468 lines, autonomous story execution |
| **Quality Gates** | ✅ WORKING | 43+ npm validation checks (`agent:verify`) |
| **Governance Books** | ✅ WORKING | 9 books (Golden, White, Green, etc.) |
| **CICA Stories** | ✅ WORKING | 70+ story files for agentic development |
| **Human-in-the-Loop** | ✅ WORKING | 3-gate approval workflow |
| **Cost Tracking** | ✅ WORKING | Budget visibility per session |
| **Circuit Breaker** | ✅ WORKING | Stops stuck loops (3 iterations) |
| **CI/CD Integration** | ✅ WORKING | Full pipeline support |
| **Cursor Agents** | ✅ WORKING | 49+ specialized agents |

**OutrePilot Summary:** All major components operational and production-ready.

---

## Outrepreneur Status

| Component | Status | Details |
|-----------|--------|---------|
| **Multi-tenant Architecture** | ✅ WORKING | 65+ database models |
| **User Authentication** | ✅ WORKING | Full auth flow |
| **Frontend Pages** | ✅ WORKING | 34 pages implemented |
| **i18n Support** | ✅ WORKING | 4 languages (EN, DE, FR, ES), 29 namespaces |
| **Capability/Vocabulary System** | ✅ WORKING | Dynamic feature toggling for SME types |
| **Chatbot/RAG** | ✅ WORKING | Role-based access, ChromaDB vector store |
| **Stripe Connect** | ✅ WORKING | Production-ready marketplace payments |
| **Design Token System** | ✅ WORKING | 3-tier (Platform, OutrePilot, Outrepreneur) |
| **Feature Modules** | ✅ WORKING | 20+ modules |

**Outrepreneur Summary:** Full SME platform operational with enterprise features.

---

## Quality Metrics

| Category | Score | Status | Notes |
|----------|-------|--------|-------|
| **TypeScript** | 100% | ✅ PASS | All type checks pass |
| **Accessibility** | 95% | ⚠️ NEAR | 1 P0 fix needed (text-gray-400 contrast) |
| **Security** | 90% | ⚠️ NEAR | 1 HIGH vulnerability (tar package) |
| **Tech Debt** | 12/100 | ✅ LOW | Minimal technical debt |
| **Test Coverage** | Good | ✅ PASS | Unit, integration, E2E in place |
| **Documentation** | Good | ✅ PASS | Registry system, guides, specs |

---

## Identified Gaps (Pre-Trial Day)

### P0 - Must Fix Before Demo

| Gap | Impact | Fix Effort | Task |
|-----|--------|------------|------|
| Accessibility contrast (text-gray-400) | Demo may look unprofessional | Low | Update to text-gray-500 or higher |
| Security vulnerability (tar package) | May raise questions if discovered | Low | Update dependency |

### P1 - Nice to Have Before Demo

| Gap | Impact | Fix Effort | Task |
|-----|--------|------------|------|
| Clinero-specific branding | Demo looks generic | Medium | Apply logo, colors |
| Dental billing demo feature | Missing industry relevance | Medium | Build 1-2 dental workflows |

### P2 - Post-Contract

| Gap | Impact | Fix Effort | Task |
|-----|--------|------------|------|
| Ivoris integration | Requires production access | High | After agreement |
| Full dental workflow suite | Complete product | High | Phase 2-3 work |

---

## Demo-Ready Features (Leverage Points)

These features are ready to demonstrate and provide negotiation leverage:

| Feature | Demo Value | Talking Point |
|---------|------------|---------------|
| **OutreRalph autonomous execution** | HIGH | "AI implements features while I review" |
| **Multi-tenant architecture** | HIGH | "Each client gets isolated data" |
| **i18n (4 languages)** | MEDIUM | "Ready for DACH + international" |
| **Stripe Connect** | HIGH | "Payment processing built-in" |
| **Role-based chatbot** | MEDIUM | "AI assistant for dental staff" |
| **Quality gates (43+ checks)** | HIGH | "Enterprise quality from day 1" |
| **Capability system** | MEDIUM | "Different features per practice size" |

---

## Pre-Trial Day Technical Tasks

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Fix text-gray-400 contrast issue | P0 | 1h | ⬜ |
| Update tar package (security) | P0 | 30m | ⬜ |
| Create Clinero tenant in Outrepreneur | HIGH | 2h | ⬜ |
| Apply Clinero branding (basic) | MEDIUM | 4h | ⬜ |
| Build dental billing demo feature | HIGH | 8h | ⬜ |
| Test demo flow end-to-end | HIGH | 2h | ⬜ |
| Prepare OutreRalph for rapid delivery | HIGH | 2h | ⬜ |

**Total estimated effort:** ~20 hours (fits in Week 1 of Phase 0)

---

# Phase 0: Preparation (Now → Trial Day)

**Duration:** 2 weeks (Jan 17 - Jan 31)
**Goal:** Be fully prepared for trial day with demo ready and negotiation strategy clear

---

## Track A: Negotiation Preparation

### Week 1 Tasks (Jan 17-24)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| A1 | Review and finalize QUESTIONS_FOR_MAX.md | HIGH | | 18 questions ready |
| A2 | Send questions to Max | HIGH | | Wait for responses |
| A3 | Research German equity/vesting law | MEDIUM | | Beteiligungsvertrag standards |
| A4 | Prepare negotiation talking points | HIGH | | Use diplomatic scripts |
| A5 | Define walk-away boundaries | HIGH | | <€70k + <5% = no |
| A6 | Prepare OutrePilot license terms draft | MEDIUM | | Fork license preferred |

### Week 2 Tasks (Jan 24-31)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| A7 | Review Max's responses to questions | HIGH | | Analyze for red/green flags |
| A8 | Adjust compensation expectations based on responses | MEDIUM | | |
| A9 | Prepare counter-offers for likely scenarios | HIGH | | |
| A10 | Rehearse protection conversation | HIGH | | Use diplomatic scripts |
| A11 | Prepare "fair to both sides" framing | HIGH | | |

---

## Track B: Demo Preparation

### Week 1 Tasks (Jan 17-24)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| B0a | **Fix text-gray-400 contrast (P0)** | CRITICAL | ⬜ | Accessibility fix, ~1h |
| B0b | **Update tar package (P0 security)** | CRITICAL | ⬜ | `npm update tar`, ~30m |
| B1 | Create Clinero tenant in Outrepreneur | HIGH | ⬜ | Multi-tenant ready, ~2h |
| B2 | Apply Clinero branding (logo, colors, name) | MEDIUM | ⬜ | Basic customization, ~4h |
| B3 | Define 2-3 demo features for dental | HIGH | ⬜ | Use Ivoris schema knowledge |
| B4 | **Implement: Patient billing overview** | HIGH | ⬜ | Demo feature #1, ~4h |
| B5 | **Implement: Appointment scheduler** | HIGH | ⬜ | Demo feature #2, ~4h |
| B6 | **Implement: Treatment cost calculator** | LOW | ⬜ | Stretch goal if time permits |

### Week 2 Tasks (Jan 24-31)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| B7 | Test demo end-to-end | HIGH | ⬜ | All features working |
| B8 | Prepare OutreRalph for rapid delivery | HIGH | ⬜ | CICA stories ready for Clinero |
| B9 | Create demo script/flow | MEDIUM | ⬜ | What to show, in what order |
| B10 | Prepare "what feature would impress you?" | HIGH | ⬜ | The key moment |
| B11 | Test rapid feature delivery (dry run) | HIGH | ⬜ | Simulate request → OutreRalph → delivery |
| B12 | Run full `npm run agent:verify` | HIGH | ⬜ | All 43+ checks pass |

---

## Track C: Personal Preparation

### Week 1 Tasks (Jan 17-24)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| C1 | Review Ivoris schema extraction project | MEDIUM | | Ready to demo if asked |
| C2 | Prepare talking points about eins+null experience | MEDIUM | | QA, MLOps, chatbot |
| C3 | Have reference letter accessible | LOW | | Dominik Flubacher |
| C4 | Research Clinero competitors | LOW | | Market context |

### Week 2 Tasks (Jan 24-31)

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| C5 | Rehearse trial day presentation | HIGH | | |
| C6 | Prepare questions to ask during trial | MEDIUM | | Show curiosity |
| C7 | Plan logistics (travel to Munich if needed) | MEDIUM | | |
| C8 | Rest day before trial | LOW | | Day 13 |

---

## Phase 0 Milestones

| Milestone | Target Date | Criteria |
|-----------|-------------|----------|
| **M0.1** Questions sent to Max | Jan 19 | Email/message sent |
| **M0.2** Demo features defined | Jan 20 | 2-3 features agreed (with self) |
| **M0.3** Demo v1 working | Jan 24 | Basic demo functional |
| **M0.4** Max responds to questions | Jan 24 | Have his answers |
| **M0.5** Demo polished | Jan 29 | Ready to show |
| **M0.6** Fully prepared | Jan 30 | All tracks complete |

---

## Phase 0 Decision Points

| Decision | Trigger | Options |
|----------|---------|---------|
| **D0.1** Max's responses are red flags | Bad answers to Q15-18 | Proceed with caution OR address directly OR withdraw |
| **D0.2** Demo features not ready in time | Behind schedule by Jan 26 | Simplify scope OR postpone trial OR skip demo |
| **D0.3** Max ghosts on questions | No response by Jan 26 | Follow up OR interpret as red flag |

---

# Phase 1: Trial Day & Negotiation

**Duration:** ~1 week (Jan 31 - Feb 7)
**Goal:** Successful trial day, impressive post-trial delivery, contract negotiation progress

---

## Day 14: Trial Day

### Trial Day Agenda (Expected)

| Time | Activity | Your Goal |
|------|----------|-----------|
| Morning | Introduction, office tour | Build rapport |
| Mid-morning | Technical discussion | Show depth of knowledge |
| Lunch | Informal conversation | Assess culture fit |
| Afternoon | Demo / hands-on | Show OutrePilot value |
| Late afternoon | Q&A, next steps | Get feature request |

### Trial Day Checklist

| # | Item | Status |
|---|------|--------|
| T1 | Laptop ready with demo | |
| T2 | Demo script rehearsed | |
| T3 | Questions for Max prepared | |
| T4 | Negotiation points in mind (not paper) | |
| T5 | "What feature would impress you?" ready | |
| T6 | Exit gracefully if red flags | |

### Trial Day Success Criteria

| Criteria | Indicator |
|----------|-----------|
| **Rapport built** | Comfortable conversation, mutual respect |
| **Technical credibility** | Max acknowledges your expertise |
| **Demo impressed** | Positive reaction to Outrepreneur/Clinero Plugin |
| **Feature request obtained** | Clear request for post-trial delivery |
| **Next steps clear** | Date for follow-up agreed |
| **No major red flags** | Consistent with prior conversations |

---

## Days 15-17: Post-Trial Delivery (The Impress Moment)

| Day | Task | Status |
|-----|------|--------|
| Day 15 | Receive/clarify feature request from Max | |
| Day 15-16 | OutrePilot implements feature | |
| Day 16-17 | Review, polish, test | |
| Day 17 | Deliver feature to Max | |
| Day 17 | Send message: "This would normally take 2-3 weeks..." | |

### Delivery Message Script

| DE | EN |
|----|-----|
| "Hi Max, hier ist das Feature, das du erwähnt hast. Das hätte normalerweise 2-3 Wochen gedauert - mit meiner Plattform konnte ich es in 2 Tagen liefern. Das ist der Vorteil, den OutrePilot bringt. Lass uns über die nächsten Schritte sprechen." | "Hi Max, here's the feature you mentioned. This would normally take 2-3 weeks - with my platform I could deliver it in 2 days. That's the advantage OutrePilot brings. Let's discuss next steps." |

---

## Days 18-21: Contract Negotiation

### Negotiation Agenda

| Topic | Your Position | Acceptable Range |
|-------|---------------|------------------|
| **Base salary** | €80k | €70-90k |
| **Equity (work)** | 12% | 8-15% |
| **Equity (OutrePilot)** | 5-8% | 3-10% |
| **Total equity** | 15-20% | 10-20% |
| **Vesting** | 4 years, 6-month cliff | 4 years, 12-month cliff max |
| **Acceleration** | 12 months if terminated without cause | 6-12 months |
| **Good Leaver** | Keep all vested | Must be explicit |
| **Bad Leaver** | Fraud/gross misconduct only | Not "performance" |
| **Start date** | Feb 15 or March 1 | Flexible |

### Negotiation Sequence

| Step | Action | Notes |
|------|--------|-------|
| 1 | Let Max make first offer | Don't anchor first on numbers |
| 2 | Respond with your expectations | Use ranges, not single numbers |
| 3 | Discuss equity structure | Introduce OutrePilot value |
| 4 | Address protection terms | Use diplomatic scripts |
| 5 | Request written agreement | Non-negotiable |
| 6 | Review draft contract | Take time, don't rush |
| 7 | Final negotiation | Minor adjustments |
| 8 | Sign | Only when satisfied |

---

## Phase 1 Milestones

| Milestone | Target Date | Criteria |
|-----------|-------------|----------|
| **M1.1** Trial day complete | Jan 31 | Positive experience |
| **M1.2** Feature delivered | Feb 2 | Max impressed |
| **M1.3** Compensation discussed | Feb 4 | Numbers on table |
| **M1.4** Protection terms agreed | Feb 5 | Clear leaver terms |
| **M1.5** Contract draft received | Feb 7 | Written document |

---

## Phase 1 Decision Points

| Decision | Trigger | Options |
|----------|---------|---------|
| **D1.1** Trial day red flags | Bad behavior, misalignment | Address directly OR withdraw |
| **D1.2** Max not impressed by delivery | No reaction to speed | Explain value OR accept lower leverage |
| **D1.3** Compensation too low | Below walk-away (<€70k + <5%) | Counter OR walk away |
| **D1.4** No written agreement | "We'll figure it out later" | Insist OR walk away |
| **D1.5** Bad Leaver includes "performance" | Vague termination clause | Negotiate specific terms OR walk away |

---

## Phase 1 Exit Criteria (Walk Away If...)

| Condition | Why It's a Deal-Breaker |
|-----------|------------------------|
| Below €65k salary AND below 8% equity | Not fair for your value |
| No written equity agreement before start | Too risky |
| "Performance" as Bad Leaver trigger | Can lose everything arbitrarily |
| No transparency on cap table | Hidden information = hidden problems |
| Max becomes evasive about terms | Trust issue |
| CTO path is vague or non-committal | Not the opportunity you want |

---

# Phase 2: First 30 Days (If You Join)

**Duration:** Days 1-30 at Clinero
**Goal:** Establish credibility, quick wins, understand the landscape

---

## Week 1: Onboarding & Assessment

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | Onboarding, access setup | All accounts, repos access |
| 2-3 | Codebase review | Architecture assessment notes |
| 3-4 | Meet team (if any) | Understand strengths/gaps |
| 4-5 | Understand current state | Technical debt inventory |

### Week 1 Questions to Answer

| Question | Why It Matters |
|----------|----------------|
| What's the current tech stack? | Plan improvements |
| Where's the technical debt? | Prioritize fixes |
| What's blocking progress? | Quick wins |
| Who built what? | Understand history |
| What do clients complain about? | Prioritize fixes |

---

## Week 2: Quick Wins

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 6-7 | Identify quick wins | List of 3-5 improvements |
| 8-10 | Implement quick win #1 | Visible improvement |

### Quick Win Criteria

| Criteria | Why |
|----------|-----|
| High visibility | Max sees immediate value |
| Low risk | Won't break anything |
| Fast to implement | Shows your speed |
| Client-facing impact | Business value |

---

## Week 3: Foundation

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 11-12 | Set up CI/CD (if missing) | Automated pipeline |
| 13-14 | Implement basic testing | Test coverage baseline |
| 15 | Documentation structure | README, architecture docs |

---

## Week 4: Strategy

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 16-17 | Draft 90-day roadmap | Share with Max |
| 18-19 | Identify hiring needs (if any) | Team plan |
| 20-21 | First month retrospective | What worked, what didn't |

---

## Phase 2 Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M2.1** Full access | Day 2 | All systems accessible |
| **M2.2** Assessment complete | Day 5 | Know the landscape |
| **M2.3** First quick win delivered | Day 10 | Visible improvement |
| **M2.4** CI/CD operational | Day 15 | Automated deployments |
| **M2.5** 90-day roadmap shared | Day 20 | Max approves direction |

---

## Phase 2 Red Flags (After Joining)

| Red Flag | Response |
|----------|----------|
| No real access to systems | Escalate immediately |
| Hidden technical debt worse than disclosed | Document and discuss |
| Max micromanages technical decisions | Address early |
| Promises not kept (equity paperwork delayed) | Demand timeline |
| Team resistance | Build relationships |

---

# Phase 3: Days 31-90

**Duration:** Months 2-3 at Clinero
**Goal:** Major milestone delivered, team established (if applicable), CTO path progressing

---

## Month 2: Core Development

| Week | Focus |
|------|-------|
| 5-6 | Core feature development |
| 7-8 | Integration with existing systems |

### Month 2 Goals

| Goal | Success Criteria |
|------|------------------|
| Core feature delivered | Working in production |
| Quality standards established | Tests, reviews in place |
| Documentation current | New team member could onboard |

---

## Month 3: Scale & Team

| Week | Focus |
|------|-------|
| 9-10 | Scale/performance optimization |
| 11-12 | Team expansion (if applicable) |

### Month 3 Goals

| Goal | Success Criteria |
|------|------------------|
| System handles 2x load | Performance tested |
| First hire identified (if applicable) | Interview process started |
| 90-day review with Max | Alignment on progress |

---

## Phase 3 Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M3.1** Core feature live | Day 45 | In production |
| **M3.2** First client using new feature | Day 60 | Real usage |
| **M3.3** Team expansion plan | Day 75 | Budget approved |
| **M3.4** 90-day review | Day 90 | Positive feedback |
| **M3.5** CTO discussion | Day 90 | Timeline confirmed |

---

## 90-Day Success Criteria

| Criteria | Indicator |
|----------|-----------|
| **Trust established** | Max delegates technical decisions |
| **Value demonstrated** | Measurable improvements |
| **Foundation solid** | CI/CD, tests, docs in place |
| **CTO path confirmed** | Written confirmation or title change |
| **Equity on track** | Paperwork signed, vesting started |

---

# Decision Framework

## At Each Phase Gate

| Question | If Yes | If No |
|----------|--------|-------|
| Am I treated fairly? | Continue | Address or exit |
| Are agreements being honored? | Continue | Escalate |
| Is the opportunity still what was promised? | Continue | Renegotiate or exit |
| Am I learning/growing? | Continue | Evaluate |
| Do I trust Max? | Continue | Exit |

---

## Walk-Away Triggers (Any Phase)

| Trigger | Action |
|---------|--------|
| Written agreements not honored | Exit |
| Equity paperwork indefinitely delayed | Exit |
| Role changed without discussion | Renegotiate or exit |
| Toxic environment | Exit |
| Company clearly failing (no clients, no revenue) | Evaluate honestly |

---

## Success Triggers (You're in the Right Place)

| Trigger | Indicator |
|---------|-----------|
| Equity paperwork signed and filed | Protected |
| CTO title or clear timeline | Path confirmed |
| Technical autonomy | Trusted |
| Revenue growing | Company healthy |
| Enjoying the work | Right fit |

---

# Master Checklist

## Before Trial Day (Phase 0)

- [ ] Questions for Max sent
- [ ] Max's responses reviewed
- [ ] Demo features working
- [ ] Negotiation strategy clear
- [ ] Walk-away boundaries defined
- [ ] Protection scripts rehearsed
- [ ] Logistics arranged

## Before Signing Contract (Phase 1)

- [ ] Trial day successful
- [ ] Post-trial delivery impressed Max
- [ ] Salary agreed (≥€70k)
- [ ] Equity agreed (≥10% total)
- [ ] Vesting terms clear
- [ ] Good/Bad Leaver defined
- [ ] Acceleration clause included
- [ ] Written contract received
- [ ] Contract reviewed (by lawyer if possible)
- [ ] OutrePilot license terms agreed

## Before Day 30 (Phase 2)

- [ ] Full system access
- [ ] Technical assessment complete
- [ ] Quick win delivered
- [ ] CI/CD operational
- [ ] 90-day roadmap shared
- [ ] Equity paperwork signed and filed

## Before Day 90 (Phase 3)

- [ ] Core feature in production
- [ ] Quality standards in place
- [ ] 90-day review positive
- [ ] CTO timeline confirmed
- [ ] Cliff passed (if 3-month cliff) or approaching

---

# Appendix: Key Documents Reference

| Document | Key Sections |
|----------|--------------|
| **COMPENSATION_MODELS_INTERNAL.md** | Models A-D, Protection Mechanisms, Diplomatic Scripts |
| **QUESTIONS_FOR_MAX.md** | 18 questions, OutrePilot section |
| **OUTREPILOT_DEMO_STRATEGY.md** | Demo flow, what to show/hide, scripts |

---

# Appendix: Quick Reference Card

## Your Value Proposition (Elevator Pitch)

| DE | EN |
|----|-----|
| "Ich bringe 7+ Jahre Erfahrung in AI/MLOps, eine fertige Enterprise-Plattform (OutrePilot), und tiefes Verständnis von Dental-PVS (Ivoris-Projekt). Ich kann schneller liefern als ein normales Team, mit Enterprise-Qualität von Anfang an." | "I bring 7+ years of AI/MLOps experience, a ready enterprise platform (OutrePilot), and deep understanding of dental PVS (Ivoris project). I can deliver faster than a normal team, with enterprise quality from the start." |

## Your Non-Negotiables

| Item | Minimum |
|------|---------|
| Salary | €65,000 |
| Equity | 8% total |
| Written agreement | Before starting |
| Bad Leaver | Fraud/misconduct only |
| Transparency | Cap table visible |

## Your Ideal

| Item | Target |
|------|--------|
| Salary | €80,000 |
| Equity | 15% total (work + OutrePilot) |
| Cliff | 6 months |
| Acceleration | 12 months if terminated without cause |
| CTO title | Within 12 months |

---

## Negotiation Leverage Summary (Based on Codebase Analysis)

### What You Bring (Quantified)

| Asset | Metric | Value for Clinero |
|-------|--------|-------------------|
| **OutrePilot** | 92% production-ready | Months of development saved |
| **OutreRalph** | 468 lines autonomous execution | 10x faster feature delivery |
| **Quality Gates** | 43+ automated checks | Enterprise quality from day 1 |
| **Cursor Agents** | 49+ specialized agents | Entire development team equivalent |
| **Outrepreneur** | 34 pages, 65+ models | Full SME platform ready |
| **Multi-tenant** | Production-ready | Each Clinero client isolated |
| **i18n** | 4 languages, 29 namespaces | DACH + international ready |
| **Stripe Connect** | Production-ready | Payments built-in |
| **Chatbot/RAG** | Working with role-based access | AI assistant for dental staff |

### Time-to-Market Advantage

| Without You | With You (OutrePilot) |
|-------------|----------------------|
| 6-12 months to MVP | 2-4 weeks to MVP |
| Hire 3-5 developers | Just you |
| Build quality systems | Quality already built |
| Design architecture | Architecture proven |

### Talking Points for Negotiation

| When Max Says... | You Can Say... |
|------------------|----------------|
| "We're a startup, budget is tight" | "I'm bringing €100k+ worth of ready platform" |
| "Standard equity is 1-3%" | "First tech hire at 6-month startup building the product deserves more" |
| "Let's start lower and see" | "My systems are already at 92% production-ready" |
| "We need to move fast" | "OutreRalph can deliver features in days, not weeks" |

---

*Last updated: 2026-01-17 (Codebase analysis integrated)*
