# Graph Report - ai-competitive-intelligence  (2026-11-05)

## Corpus Check
- 122 files · ~45,025 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1337 nodes · 3492 edges · 71 communities (49 shown, 22 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 409 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `baa76676`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_service.py
- asyncio
- endpoints/research.py
- crypto.py
- test_graph.py
- research_service.py
- page.js
- test_persistence_company.py
- database.py
- CompetitorResearcherAgent
- AI Competitive Intelligence System (ACIS)
- LLMMessage
- builder.py
- AsyncPostgresSaver
- ResearchError
- competitor_discovery_node.py
- llm.py
- test_checkpoint.py
- ResearchState
- checkpoint.py
- CompetitorProfile
- agents/company_researcher.py
- config.py
- Evidence
- test_agent_base.py
- SearchResult
- test_competitor_discovery_node.py
- nodes/company_researcher.py
- run_node
- test_api.py
- endpoints/auth.py
- exceptions.py
- CompanyResearcherAgent
- DuckDuckGoProvider
- test_company_researcher_agent.py
- logging.py
- test_nodes.py
- FakeLLMClient
- SearchQuery
- DatabaseManager
- test_persistence_api.py
- get_url
- sqlalchemy
- identity.py
- BaseAgent
- compilerOptions
- next.config.js
- intelligence/evidence.py
- security/auth.py
- CompanyRepository
- get_settings
- strategic_analyst_mock.py
- EvidenceRepository
- competitor_researcher.py
- test_api_rate_limit_applies_before_authentication
- detect_conflicts
- dependencies.py
- _normalize_email

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 72 edges
2. `get_settings()` - 55 edges
3. `SearchResult` - 50 edges
4. `CompetitorResearcherAgent` - 46 edges
5. `SearchQuery` - 37 edges
6. `CompanyResearcherAgent` - 33 edges
7. `run_node()` - 33 edges
8. `ResearchError` - 31 edges
9. `MockSearchProvider` - 30 edges
10. `CompetitorProfile` - 25 edges

## Surprising Connections (you probably didn't know these)
- `Ponytail and combined Copilot workflow` --references--> `main()`  [INFERRED]
  docs/development-roadmap.md → backend/app/cli.py
- `Company Research Agent pipeline (Phase 2A)` --references--> `company_researcher()`  [INFERRED]
  docs/architecture.md → backend/app/graph/nodes/company_researcher.py
- `Phase 2B — Competitor Discovery Agent` --references--> `competitor_discovery_mock()`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/nodes/competitor_discovery_mock.py
- `Design principles` --references--> `ResearchState`  [INFERRED]
  docs/agent-design.md → backend/app/graph/state.py
- `Phase 0 + Phase 1 (complete)` --references--> `ResearchState`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/state.py

## Import Cycles
- None detected.

## Communities (71 total, 22 thin omitted)

### Community 0 - "test_service.py"
Cohesion: 0.15
Nodes (12): NotFoundError, get_research(), list_research_ids(), disable_live_llm(), _skip_persistence(), _submit(), test_get_research_missing_raises_not_found(), test_get_research_returns_stored_result() (+4 more)

### Community 1 - "asyncio"
Cohesion: 0.23
Nodes (13): _company_profile(), _make_agent(), test_agent_competitor_discovery_with_llm(), test_agent_competitor_discovery_without_llm(), test_agent_rejects_empty_company_name(), test_competitor_profiles_have_required_fields(), test_conflicting_source_status_and_duplicate_candidates_are_preserved(), test_independent_source_corroboration_and_unknown_fields_are_explicit() (+5 more)

### Community 2 - "endpoints/research.py"
Cohesion: 0.13
Nodes (7): get_research_endpoint(), submit_research(), NodeExecutionMetadata, ResearchRequest, ResearchResponse, ResearchStatusResponse, test_research_request_rejects_client_organization_id()

### Community 3 - "crypto.py"
Cohesion: 0.12
Nodes (13): _encode_field(), _encrypt_column(), _encrypt_existing_checkpoints(), _encrypt_identity_email(), upgrade(), decrypt_bytes(), encrypt_bytes(), encrypt_checkpoint_payload() (+5 more)

### Community 4 - "test_graph.py"
Cohesion: 0.09
Nodes (20): build_graph(), get_graph(), disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_company_researcher(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm() (+12 more)

### Community 5 - "research_service.py"
Cohesion: 0.17
Nodes (10): ResearchResult, _fetch_from_db(), _get_repository(), _new_id(), _persist_result(), _row_to_result(), run_research(), _settings_default_organization_id() (+2 more)

### Community 6 - "page.js"
Cohesion: 0.06
Nodes (66): metadata, RootLayout(), Home(), handleLogin(), handleLogout(), handleOrganizationChange(), restoreSession(), ReportDisplay() (+58 more)

### Community 7 - "test_persistence_company.py"
Cohesion: 0.20
Nodes (8): company_repo(), evidence_repo(), session(), test_company_repository_create_and_get(), test_company_repository_org_isolation(), test_database_tables_exist(), test_evidence_repository_create_and_list(), test_evidence_repository_org_isolation()

### Community 8 - "database.py"
Cohesion: 0.12
Nodes (6): Base, get_sync_database_url(), Competitor, CompetitorEvidence, EncryptedJSON, EncryptedText

### Community 10 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.06
Nodes (29): Development Roadmap, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2B — Competitor Discovery Agent, Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned), Ponytail and combined Copilot workflow (+21 more)

### Community 11 - "LLMMessage"
Cohesion: 0.14
Nodes (6): LLMMessage, LLMResponse, test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises(), test_llm_response_structure()

### Community 12 - "builder.py"
Cohesion: 0.14
Nodes (7): _evidence_validator(), evidence_validator_mock(), _report_generator(), report_generator_mock(), research_planner(), _research_planner(), The agents (nodes)

### Community 13 - "AsyncPostgresSaver"
Cohesion: 0.11
Nodes (12): AsyncPostgresSaver, Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B, Company Research Agent pipeline (Phase 2A), Database degradation, Frontend, High-level data flow, LangGraph checkpointing, Overview (+4 more)

### Community 14 - "ResearchError"
Cohesion: 0.05
Nodes (20): ResearchError, _persist_competitor_discovery(), Research, _company_key(), CompetitorEvidenceRepository, CompetitorRepository, _website_key(), ResearchRepository (+12 more)

### Community 15 - "competitor_discovery_node.py"
Cohesion: 0.17
Nodes (6): AgentBudget, _build_search_provider(), competitor_discovery(), _competitor_discovery(), test_agent_budget_defaults(), Graphify installation and use

### Community 17 - "llm.py"
Cohesion: 0.11
Nodes (9): BaseLLMClient, LLMConfig, LLMFactory, OpenRouterLLMClient, test_llm_client_configured_with_key(), test_complete_without_api_key_raises_clear_error(), test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured() (+1 more)

### Community 18 - "test_checkpoint.py"
Cohesion: 0.15
Nodes (7): _competitor_discovery(), competitor_discovery_mock(), _build_graph(), _reset_db_each_test(), test_checkpointer_setup_creates_tables(), test_database_available_for_checkpointing(), test_thread_based_checkpoint_store_and_retrieve()

### Community 19 - "ResearchState"
Cohesion: 0.21
Nodes (4): ResearchState, test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields()

### Community 20 - "checkpoint.py"
Cohesion: 0.17
Nodes (3): decrypt_text(), EncryptedCheckpointSerializer, test_encrypted_text_and_checkpoint_payload_round_trip()

### Community 21 - "CompetitorProfile"
Cohesion: 0.06
Nodes (33): build_competitor_evidence(), classify_from_factors(), classify_from_score(), compute_text_overlap(), deduplicate_competitors(), _domain_of(), extract_keywords(), _normalize_name() (+25 more)

### Community 22 - "agents/company_researcher.py"
Cohesion: 0.16
Nodes (7): CompanyProfile, CompanySize, test_company_profile_full(), test_company_profile_minimal(), test_company_profile_rejects_bad_website(), test_company_size(), test_company_size_max_gte_min()

### Community 23 - "config.py"
Cohesion: 0.07
Nodes (17): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default(), repo(), _rid() (+9 more)

### Community 24 - "Evidence"
Cohesion: 0.20
Nodes (6): Evidence, EvidenceCollection, test_evidence_collection(), test_evidence_confidence_clamped(), test_evidence_creation(), test_evidence_rejects_bad_url()

### Community 25 - "test_agent_base.py"
Cohesion: 0.11
Nodes (15): fetch_page(), _resolve_public_addresses(), retry_async(), validate_url_for_fetch(), test_fetch_page_blocks_private_url(), test_fetch_page_does_not_use_ip_literal_as_tls_sni(), test_fetch_page_pins_dns_result_and_preserves_tls_hostname(), resolve() (+7 more)

### Community 26 - "SearchResult"
Cohesion: 0.12
Nodes (11): SearchResultCache, SearchResult, DummyProvider, test_base_agent_rate_limited_search_budget(), test_base_agent_search_cache(), test_search_result_cache(), test_search_query_creation(), test_search_query_priority_bounds() (+3 more)

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.15
Nodes (8): disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_competitor_discovery(), test_node_records_failure_safely(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient

### Community 28 - "nodes/company_researcher.py"
Cohesion: 0.15
Nodes (7): company_researcher(), _company_researcher(), finalize_research(), _finalize_research(), test_node_records_failure_safely(), Error handling, State (`ResearchState`)

### Community 29 - "run_node"
Cohesion: 0.21
Nodes (6): make_metadata(), run_node(), utc_now_iso(), initialize_research(), _initialize_research(), test_graph_failure_does_not_expose_exception_content()

### Community 30 - "test_api.py"
Cohesion: 0.20
Nodes (10): enforce_rate_limit(), get_current_user(), get_organization_context(), require_bearer_credentials(), _client(), test_get_research_by_id(), test_get_research_not_found(), test_health_endpoint() (+2 more)

### Community 31 - "endpoints/auth.py"
Cohesion: 0.20
Nodes (23): accept_invitation(), accept_invitation_existing(), _create_invitation(), create_organization(), create_organization_invitation(), create_platform_invitation(), _create_session(), list_user_organizations() (+15 more)

### Community 32 - "exceptions.py"
Cohesion: 0.14
Nodes (10): acis_exception_handler(), ACISException, _error_payload(), LLMConfigurationError, unhandled_exception_handler(), validation_exception_handler(), ValidationError, test_exception_error_codes_and_message() (+2 more)

### Community 33 - "CompanyResearcherAgent"
Cohesion: 0.17
Nodes (4): CompanyResearcherAgent, get_llm_client(), Company Research Agent pipeline, Phase 2A: Real Company Research Agent

### Community 34 - "DuckDuckGoProvider"
Cohesion: 0.22
Nodes (3): _build_search_provider(), DuckDuckGoProvider, _is_private_or_internal()

### Community 35 - "test_company_researcher_agent.py"
Cohesion: 0.15
Nodes (8): FakeLLMClient, _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm(), test_agent_research_without_llm(), test_evidence_items_have_provenance(), UnavailableLLMClient

### Community 36 - "logging.py"
Cohesion: 0.16
Nodes (3): configure_logging(), get_logger(), _MaskingFormatter

### Community 37 - "test_nodes.py"
Cohesion: 0.23
Nodes (14): _company_researcher(), company_researcher_mock(), _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_finalize_research_success_no_errors() (+6 more)

### Community 39 - "SearchQuery"
Cohesion: 0.13
Nodes (8): SearchProvider, MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_provider_is_abstract()

### Community 41 - "DatabaseManager"
Cohesion: 0.09
Nodes (5): DatabaseManager, DatabaseUnavailableError, test_base_declarative(), test_database_manager_starts_without_url(), test_session_factory_raises_when_unavailable()

### Community 42 - "test_persistence_api.py"
Cohesion: 0.16
Nodes (15): AuthenticatedUser, OrganizationContext, require_permission(), require_platform_admin(), authenticated_test_context(), current_user(), organization_context(), client() (+7 more)

### Community 43 - "get_url"
Cohesion: 0.29
Nodes (3): get_url(), run_migrations_offline(), run_migrations_online()

### Community 44 - "sqlalchemy"
Cohesion: 0.21
Nodes (4): upgrade(), upgrade(), upgrade(), upgrade()

### Community 45 - "identity.py"
Cohesion: 0.17
Nodes (10): _bootstrap_admin(), main(), Organization, RateLimitBucket, User, email_lookup_hash(), hash_password(), authenticated_client() (+2 more)

### Community 60 - "intelligence/evidence.py"
Cohesion: 0.17
Nodes (9): build_evidence_from_result(), classify_evidence_type(), _domain_of(), _is_trusted_domain(), score_confidence(), _make_result(), test_build_evidence_from_result(), test_classify_evidence_type() (+1 more)

### Community 61 - "security/auth.py"
Cohesion: 0.13
Nodes (11): create_access_token(), decode_access_token(), Permission, verify_csrf(), verify_password(), _settings(), test_access_token_validates_and_rejects_tampering(), test_argon2id_password_hashing_and_password_bounds() (+3 more)

### Community 62 - "CompanyRepository"
Cohesion: 0.28
Nodes (3): _persist_company_research(), CompanyProfile, CompanyRepository

### Community 63 - "get_settings"
Cohesion: 0.11
Nodes (14): _check_origin(), _clear_auth_cookies(), login(), refresh(), _set_auth_cookies(), health(), get_settings(), create_app() (+6 more)

### Community 64 - "strategic_analyst_mock.py"
Cohesion: 0.17
Nodes (9): _strategic_analyst(), strategic_analyst_mock(), Agent Design — ACIS LangGraph Multi-Agent System (Phase 1 + 1.5 + 2A + 2B), Competitor Discovery Agent pipeline (Phase 2B), Design principles, Extensibility (future phases), Persistence and checkpointing (Phase 1.5 + 2A), State transitions (+1 more)

### Community 66 - "competitor_researcher.py"
Cohesion: 0.25
Nodes (4): EvidenceType, VerificationStatus, Modules, Phase 2A — Real Company Research Agent (complete)

### Community 70 - "dependencies.py"
Cohesion: 0.29
Nodes (3): get_db_session(), database_health(), get_session()

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 484 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `crypto.py`, `research_service.py`, `test_persistence_company.py`, `database.py`, `ResearchError`, `competitor_discovery_node.py`, `typing`, `llm.py`, `test_checkpoint.py`, `agents/company_researcher.py`, `config.py`, `nodes/company_researcher.py`, `test_api.py`, `endpoints/auth.py`, `DuckDuckGoProvider`, `test_company_researcher_agent.py`, `DatabaseManager`, `test_persistence_api.py`, `get_url`, `identity.py`, `security/auth.py`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `endpoints/research.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12987012987012986 - nodes in this community are weakly interconnected._
- **Why does `ResearchState` connect `ResearchState` to `strategic_analyst_mock.py`, `competitor_researcher.py`, `test_graph.py`, `test_nodes.py`, `research_service.py`, `AI Competitive Intelligence System (ACIS)`, `builder.py`, `competitor_discovery_node.py`, `test_checkpoint.py`, `security/auth.py`, `test_competitor_discovery_node.py`, `nodes/company_researcher.py`, `run_node`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `crypto.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11553030303030302 - nodes in this community are weakly interconnected._