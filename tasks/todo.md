# Task List: ACIS Phase 2B — Competitor Discovery Agent

## Phase A: Repo inspection (done)
- [x] Inspected ResearchState, graph nodes/builder, LLM factory, DB models/repositories, search tools, evidence infra, existing tests
- [x] Confirmed PostgreSQL 18 running, acis_db/acis_app configured

## Phase B: Competitor schemas
- [ ] app/schemas/competitor.py — CompetitorProfile, CompetitorType, QualificationFactor, CompetitorCollection

## Phase C: Competitor intelligence (qualification + dedup)
- [ ] app/intelligence/competitor.py — transparent scoring, deduplication, overlap analysis

## Phase D: Competitor agent
- [ ] app/agents/competitor_researcher.py — CompetitorResearcherAgent extending BaseAgent

## Phase E: Database models + repositories + migration
- [ ] app/models/competitor.py — Competitor, CompetitorEvidence ORM
- [ ] app/repositories/competitor.py — CompetitorRepository with org isolation
- [ ] alembic/versions/0003_competitors.py — migration
- [ ] Update alembic/env.py to import new models

## Phase F: LangGraph integration
- [ ] app/graph/nodes/competitor_discovery.py — real node replacing mock
- [ ] app/graph/builder.py — register competitor_discovery node
- [ ] app/graph/nodes/__init__.py — export new node

## Phase G: Config + env
- [ ] app/core/config.py — competitor search settings
- [ ] backend/.env.example — competitor env vars

## Phase H: Tests (deterministic, no real APIs/credits)
- [ ] tests/unit/test_competitor_schemas.py
- [ ] tests/unit/test_competitor_intelligence.py
- [ ] tests/unit/test_competitor_agent.py (mocked LLM/search)
- [ ] tests/unit/test_competitor_persistence.py (DB + org isolation)
- [ ] tests/integration/test_competitor_discovery_node.py (LangGraph integration)
- [ ] Update existing tests (test_graph.py, test_service.py) for new node order
- [ ] Existing 55+ tests still pass

## Phase I: Docs + Git
- [ ] Update docs/architecture.md, docs/agent-design.md, docs/development-roadmap.md, README.md
- [ ] Commit on phase-0-1-foundation, don't merge to main