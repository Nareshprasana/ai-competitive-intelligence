# Implementation Plan: ACIS Phase 2B — Competitor Discovery Agent

## Overview
Replace the deterministic mock `competitor_discovery_mock` node with a real Competitor Discovery Agent that identifies and validates direct, indirect, emerging, and substitute competitors for a researched company. The agent reuses existing search, LLM, evidence, and persistence infrastructure. No new dependencies required.

## Architecture

```
Company Profile (from company_researcher)
    ↓
Product and Service Analysis
    ↓
Market and Customer Analysis
    ↓
Competitor Search Query Generation
    ↓
External Search (reuse SearchProvider: mock default / DuckDuckGo)
    ↓
Candidate Company Extraction (LLM structured extraction)
    ↓
Duplicate Removal (by name/domain)
    ↓
Competitor Qualification (transparent scoring model)
    ↓
Evidence Validation (reuse evidence infrastructure)
    ↓
Competitor Ranking
    ↓
Structured Results (CompetitorProfile[])
    ↓
PostgreSQL Persistence (Competitor + CompetitorEvidence tables)
```

## New Modules

| Module | Purpose |
|--------|---------|
| `app/schemas/competitor.py` | `CompetitorProfile`, `CompetitorType`, `QualificationFactor`, `CompetitorCollection` |
| `app/intelligence/competitor.py` | Qualification scoring, deduplication, overlap analysis |
| `app/agents/competitor_researcher.py` | `CompetitorResearcherAgent` (extends `BaseAgent`) |
| `app/models/competitor.py` | `Competitor`, `CompetitorEvidence` ORM models |
| `app/repositories/competitor.py` | `CompetitorRepository` with org isolation |
| `alembic/versions/0003_competitors.py` | Migration |
| `app/graph/nodes/competitor_discovery.py` | Graph node replacing `competitor_discovery_mock` |

## Modified Modules

| Module | Change |
|--------|--------|
| `app/graph/builder.py` | Register `competitor_discovery` in `NODE_ORDER`/`_NODES` |
| `app/graph/nodes/__init__.py` | Export `competitor_discovery`, keep `competitor_discovery_mock` |
| `app/core/config.py` | Add competitor search settings |
| `backend/.env.example` | Add competitor env vars |
| `docs/architecture.md`, `docs/agent-design.md`, `docs/development-roadmap.md`, `README.md` | Update docs |

## Design Decisions

- **Four competitor types**: `direct`, `indirect`, `emerging`, `substitute` — every competitor has a documented `competitor_type`
- **Transparent qualification scoring**: weighted sum of evidence-backed factors (product similarity, customer overlap, problem-space overlap, geographic overlap, business-model similarity). No unexplained LLM score.
- **Separation**: evidence-backed observations vs analytical judgments vs unknown information
- **Duplicate removal**: by normalized company name and domain
- **Resource reuse**: reuses company research search results, caches queries, budgeted search/LLM calls
- **Organization isolation**: all repository queries filter by `organization_id`
- **No uncontrolled loops**: linear discovery flow, bounded candidates
- **Graceful degradation**: without LLM, uses heuristic qualification from search snippets

## Test Plan

- Unit: schemas, qualification scoring, deduplication, agent (mocked LLM/search), persistence, org isolation
- Integration: LangGraph node execution, checkpoint recovery, failure handling
- All tests use deterministic fixtures; no real search APIs or LLM credits

## Acceptance Criteria

1. Competitor Discovery Agent implemented ✅
2. Four competitor categories supported ✅
3. Candidate qualification is explainable ✅
4. Evidence attached to claims ✅
5. Competitors persist in PostgreSQL ✅
6. Organization isolation enforced ✅
7. Mock node replaced in LangGraph ✅
8. Existing functionality preserved ✅
9. Existing tests pass ✅
10. New tests pass ✅
11. Documentation updated ✅
12. No secrets committed ✅
