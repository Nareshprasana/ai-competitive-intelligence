# Graph Report - ai-competitive-intelligence  (2026-11-02)

## Corpus Check
- 112 files · ~36,825 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1148 nodes · 2776 edges · 58 communities (40 shown, 18 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 318 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1877431e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ResearchForm.js
- asyncio
- research_service.py
- DatabaseManager
- test_graph.py
- test_persistence.py
- ResearchRepository
- test_persistence_company.py
- database.py
- CompetitorResearcherAgent
- AI Competitive Intelligence System (ACIS)
- LLMConfigurationError
- builder.py
- company_researcher
- competitor_discovery_node.py
- CompetitorProfile
- agents/base.py
- LLMConfig
- test_checkpoint.py
- ResearchState
- intelligence/competitor.py
- test_competitor_intelligence.py
- CompanyProfile
- Settings
- Evidence
- BaseAgent
- SearchResult
- test_competitor_discovery_node.py
- agents/company_researcher.py
- run_node
- competitor_researcher.py
- test_persistence_api.py
- main.py
- CompanyResearcherAgent
- DuckDuckGoProvider
- test_company_researcher_agent.py
- test_nodes.py
- LLMResponse
- SearchQuery
- ResearchError
- test_api.py
- get_url
- AgentBudget
- SearchResultCache
- compilerOptions
- next.config.js

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 70 edges
2. `SearchResult` - 50 edges
3. `CompetitorResearcherAgent` - 46 edges
4. `get_settings()` - 37 edges
5. `SearchQuery` - 37 edges
6. `CompanyResearcherAgent` - 33 edges
7. `ResearchError` - 31 edges
8. `run_node()` - 31 edges
9. `MockSearchProvider` - 30 edges
10. `CompetitorProfile` - 25 edges

## Surprising Connections (you probably didn't know these)
- `Design principles` --references--> `ResearchState`  [INFERRED]
  docs/agent-design.md → backend/app/graph/state.py
- `Phase 0 + Phase 1 (complete)` --references--> `ResearchState`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/state.py
- `SSRF/DNS-rebinding mitigation` --references--> `fetch_page()`  [EXTRACTED]
  docs/development-roadmap.md → backend/app/agents/base.py
- `Phase 2A — Real Company Research Agent (complete)` --references--> `BaseAgent`  [INFERRED]
  docs/development-roadmap.md → backend/app/agents/base.py
- `Company Research Agent pipeline` --references--> `CompanyResearcherAgent`  [INFERRED]
  docs/agent-design.md → backend/app/agents/company_researcher.py

## Import Cycles
- None detected.

## Communities (58 total, 18 thin omitted)

### Community 0 - "ResearchForm.js"
Cohesion: 0.06
Nodes (54): metadata, RootLayout(), Home(), ReportDisplay(), ResearchForm(), handleSubmit(), NAV, Sidebar() (+46 more)

### Community 1 - "asyncio"
Cohesion: 0.13
Nodes (15): _company_profile(), FakeLLMClient, _make_agent(), test_agent_competitor_discovery_with_llm(), test_agent_competitor_discovery_without_llm(), test_agent_rejects_empty_company_name(), test_competitor_profiles_have_required_fields(), test_conflicting_source_status_and_duplicate_candidates_are_preserved() (+7 more)

### Community 2 - "research_service.py"
Cohesion: 0.06
Nodes (28): get_research_endpoint(), submit_research(), NodeExecutionMetadata, ResearchRequest, ResearchResponse, ResearchResult, ResearchStatusResponse, _fetch_from_db() (+20 more)

### Community 3 - "DatabaseManager"
Cohesion: 0.05
Nodes (7): AsyncPostgresSaver, DatabaseManager, test_base_declarative(), test_database_manager_starts_without_url(), test_session_factory_raises_when_unavailable(), Persistence and checkpointing (Phase 1.5 + 2A), LangGraph checkpointing

### Community 4 - "test_graph.py"
Cohesion: 0.08
Nodes (21): build_graph(), get_graph(), disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_company_researcher(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm() (+13 more)

### Community 5 - "test_persistence.py"
Cohesion: 0.21
Nodes (11): repo(), _rid(), session(), test_alembic_table_exists(), test_database_is_configured(), test_repository_create_and_get_by_id(), test_repository_get_by_id_wrong_organization_returns_none(), test_repository_list_by_organization() (+3 more)

### Community 6 - "ResearchRepository"
Cohesion: 0.13
Nodes (3): Research, ResearchRepository, Phase 1.5 — Integration Verification & Database Persistence (complete)

### Community 7 - "test_persistence_company.py"
Cohesion: 0.10
Nodes (14): _persist_company_research(), CompanyProfile, EvidenceClaim, CompanyRepository, EvidenceRepository, company_repo(), evidence_repo(), session() (+6 more)

### Community 8 - "database.py"
Cohesion: 0.08
Nodes (8): upgrade(), upgrade(), upgrade(), Base, get_db_session(), get_logger(), database_health(), get_session()

### Community 10 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.06
Nodes (29): Development Roadmap, Graphify installation and use, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned), Ponytail and combined Copilot workflow (+21 more)

### Community 11 - "LLMConfigurationError"
Cohesion: 0.12
Nodes (9): LLMConfigurationError, BaseLLMClient, LLMMessage, OpenRouterLLMClient, test_llm_client_configured_with_key(), test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises() (+1 more)

### Community 12 - "builder.py"
Cohesion: 0.12
Nodes (10): _evidence_validator(), evidence_validator_mock(), _report_generator(), report_generator_mock(), research_planner(), _research_planner(), _strategic_analyst(), strategic_analyst_mock() (+2 more)

### Community 13 - "company_researcher"
Cohesion: 0.08
Nodes (22): company_researcher(), competitor_discovery(), test_node_records_failure_safely(), Agent Design — ACIS LangGraph Multi-Agent System (Phase 1 + 1.5 + 2A + 2B), Company Research Agent pipeline, Competitor Discovery Agent pipeline (Phase 2B), Design principles, Error handling (+14 more)

### Community 14 - "competitor_discovery_node.py"
Cohesion: 0.06
Nodes (19): _build_search_provider(), _competitor_discovery(), _persist_competitor_discovery(), Competitor, CompetitorEvidence, _company_key(), CompetitorEvidenceRepository, CompetitorRepository (+11 more)

### Community 15 - "CompetitorProfile"
Cohesion: 0.14
Nodes (10): CompetitorCollection, CompetitorEvidenceItem, CompetitorProfile, test_competitor_collection(), test_competitor_evidence_requires_a_valid_http_source(), test_competitor_profile_full(), test_competitor_profile_minimal(), test_competitor_profile_rejects_bad_type() (+2 more)

### Community 16 - "agents/base.py"
Cohesion: 0.13
Nodes (9): fetch_page(), _resolve_public_addresses(), retry_async(), validate_url_for_fetch(), _is_private_or_internal(), test_retry_async_non_transient_not_retried(), test_retry_async_transient(), test_validate_url_for_fetch_allows_public() (+1 more)

### Community 17 - "LLMConfig"
Cohesion: 0.15
Nodes (6): LLMConfig, LLMFactory, test_complete_without_api_key_raises_clear_error(), test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured(), test_llm_factory_is_lazy_until_client_requested()

### Community 18 - "test_checkpoint.py"
Cohesion: 0.11
Nodes (10): _company_researcher(), company_researcher_mock(), _competitor_discovery(), competitor_discovery_mock(), _build_graph(), _reset_db_each_test(), test_checkpointer_setup_creates_tables(), test_database_available_for_checkpointing() (+2 more)

### Community 19 - "ResearchState"
Cohesion: 0.21
Nodes (4): ResearchState, test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields()

### Community 20 - "intelligence/competitor.py"
Cohesion: 0.12
Nodes (8): build_competitor_evidence(), deduplicate_competitors(), _domain_of(), extract_keywords(), _normalize_name(), pytest_configure(), test_deduplicate_competitors_by_domain(), test_deduplicate_competitors_by_name()

### Community 21 - "test_competitor_intelligence.py"
Cohesion: 0.18
Nodes (12): classify_from_score(), compute_text_overlap(), score_qualification(), test_classify_from_score_direct(), test_classify_from_score_emerging(), test_classify_from_score_indirect(), test_classify_from_score_substitute(), test_compute_text_overlap() (+4 more)

### Community 22 - "CompanyProfile"
Cohesion: 0.17
Nodes (7): CompanyProfile, CompanySize, test_company_profile_full(), test_company_profile_minimal(), test_company_profile_rejects_bad_website(), test_company_size(), test_company_size_max_gte_min()

### Community 23 - "Settings"
Cohesion: 0.13
Nodes (6): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default()

### Community 24 - "Evidence"
Cohesion: 0.09
Nodes (19): build_evidence_from_result(), classify_evidence_type(), detect_conflicts(), _domain_of(), _is_trusted_domain(), score_confidence(), Evidence, EvidenceCollection (+11 more)

### Community 25 - "BaseAgent"
Cohesion: 0.15
Nodes (10): BaseAgent, test_base_agent_rate_limited_search_budget(), test_base_agent_search_cache(), test_fetch_page_blocks_private_url(), test_fetch_page_does_not_use_ip_literal_as_tls_sni(), test_fetch_page_pins_dns_result_and_preserves_tls_hostname(), resolve(), respond() (+2 more)

### Community 26 - "SearchResult"
Cohesion: 0.15
Nodes (7): SearchResult, DummyProvider, test_search_query_creation(), test_search_query_priority_bounds(), test_search_result_creation(), test_search_result_normalizes_domain(), test_search_result_rejects_empty_url()

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.17
Nodes (7): disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_node_records_failure_safely(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient

### Community 28 - "agents/company_researcher.py"
Cohesion: 0.13
Nodes (4): health(), get_settings(), get_sync_database_url(), root()

### Community 29 - "run_node"
Cohesion: 0.18
Nodes (7): make_metadata(), run_node(), utc_now_iso(), finalize_research(), _finalize_research(), initialize_research(), _initialize_research()

### Community 30 - "competitor_researcher.py"
Cohesion: 0.22
Nodes (4): classify_from_factors(), CompetitorType, QualificationFactor, test_classifies_all_competitor_types_from_overlap_evidence()

### Community 31 - "test_persistence_api.py"
Cohesion: 0.24
Nodes (6): client(), _make_app(), test_cross_organization_isolation_at_api(), test_get_research_not_found(), test_health_reports_database_available(), test_submit_and_retrieve_research_persisted()

### Community 32 - "main.py"
Cohesion: 0.10
Nodes (6): unhandled_exception_handler(), validation_exception_handler(), configure_logging(), _MaskingFormatter, create_app(), lifespan()

### Community 33 - "CompanyResearcherAgent"
Cohesion: 0.14
Nodes (4): CompanyResearcherAgent, get_llm_client(), _build_search_provider(), _company_researcher()

### Community 35 - "test_company_researcher_agent.py"
Cohesion: 0.26
Nodes (7): _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm(), test_agent_research_without_llm(), test_evidence_items_have_provenance(), UnavailableLLMClient

### Community 37 - "test_nodes.py"
Cohesion: 0.38
Nodes (11): _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_finalize_research_success_no_errors(), test_initialize_research(), test_nodes_record_execution_metadata() (+3 more)

### Community 38 - "LLMResponse"
Cohesion: 0.20
Nodes (3): LLMResponse, FakeLLMClient, test_llm_response_structure()

### Community 39 - "SearchQuery"
Cohesion: 0.13
Nodes (9): SearchProvider, MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_provider_is_abstract() (+1 more)

### Community 40 - "ResearchError"
Cohesion: 0.16
Nodes (9): acis_exception_handler(), ACISException, DatabaseUnavailableError, _error_payload(), NotFoundError, ResearchError, ValidationError, test_exception_error_codes_and_message() (+1 more)

### Community 42 - "test_api.py"
Cohesion: 0.43
Nodes (6): _client(), test_get_research_by_id(), test_get_research_not_found(), test_health_endpoint(), test_request_validation_rejects_invalid_input(), test_submit_research_returns_id_and_results()

### Community 43 - "get_url"
Cohesion: 0.29
Nodes (3): get_url(), run_migrations_offline(), run_migrations_online()

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 447 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `agents/company_researcher.py` to `main.py`, `CompanyResearcherAgent`, `research_service.py`, `DatabaseManager`, `test_company_researcher_agent.py`, `test_persistence.py`, `test_persistence_company.py`, `database.py`, `get_url`, `company_researcher`, `competitor_discovery_node.py`, `agents/base.py`, `LLMConfig`, `test_checkpoint.py`, `Settings`, `test_persistence_api.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ResearchForm.js` be split into smaller, more focused modules?**
  _Cohesion score 0.06189640035118525 - nodes in this community are weakly interconnected._
- **Why does `ResearchState` connect `ResearchState` to `CompanyResearcherAgent`, `research_service.py`, `test_graph.py`, `test_nodes.py`, `test_persistence_company.py`, `AI Competitive Intelligence System (ACIS)`, `builder.py`, `company_researcher`, `competitor_discovery_node.py`, `test_checkpoint.py`, `test_competitor_discovery_node.py`, `run_node`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `asyncio` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._