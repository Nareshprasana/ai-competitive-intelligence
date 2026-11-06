# Graph Report - ai-competitive-intelligence  (2026-11-06)

## Corpus Check
- 124 files · ~48,760 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1394 nodes · 3775 edges · 69 communities (50 shown, 19 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 474 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `65fcde98`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- research_service.py
- asyncio
- test_competitor_persistence.py
- crypto.py
- agents/company_researcher.py
- test_persistence_company.py
- page.js
- test_sqlite_security.py
- test_service.py
- test_agent_base.py
- endpoints/auth.py
- LLMConfigurationError
- state.py
- test_graph.py
- DatabaseManager
- CompanyProfile
- test_company_researcher_node.py
- AI Competitive Intelligence System (ACIS)
- CompetitorResearcherAgent
- competitor_researcher.py
- test_crypto_security.py
- AuthenticatedUser
- SearchQuery
- get_settings
- CompetitorProfile
- security/auth.py
- AsyncPostgresSaver
- test_competitor_discovery_node.py
- ResearchRepository
- run_node
- SearchResult
- Settings
- exceptions.py
- LLMResponse
- test_nodes.py
- test_company_researcher_agent.py
- logging.py
- models/competitor.py
- company_researcher
- ResearchState
- 0005_encrypt_sensitive_payloads.py
- Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B
- sqlite_security_environment
- duckduckgo.py
- build_competitor_evidence
- test_auth_and_tenant_isolation.py
- deduplicate_competitors
- EncryptedCheckpointSerializer
- get_url
- test_checkpoint.py
- re
- CompanyResearcherAgent
- compilerOptions
- next.config.js
- LLMConfig
- main.py

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 74 edges
2. `get_settings()` - 59 edges
3. `SearchResult` - 50 edges
4. `CompetitorResearcherAgent` - 46 edges
5. `SearchQuery` - 37 edges
6. `CompanyResearcherAgent` - 33 edges
7. `ResearchError` - 33 edges
8. `run_node()` - 33 edges
9. `MockSearchProvider` - 30 edges
10. `AsyncPostgresSaver` - 28 edges

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

## Communities (69 total, 19 thin omitted)

### Community 0 - "research_service.py"
Cohesion: 0.10
Nodes (16): submit_research(), NodeExecutionMetadata, ResearchRequest, ResearchResponse, ResearchResult, ResearchStatusResponse, _fetch_from_db(), _get_repository() (+8 more)

### Community 1 - "asyncio"
Cohesion: 0.17
Nodes (15): _resolve_public_addresses(), _company_profile(), _make_agent(), test_agent_competitor_discovery_with_llm(), test_agent_competitor_discovery_without_llm(), test_agent_rejects_empty_company_name(), test_competitor_profiles_have_required_fields(), test_conflicting_source_status_and_duplicate_candidates_are_preserved() (+7 more)

### Community 2 - "test_competitor_persistence.py"
Cohesion: 0.08
Nodes (17): _persist_competitor_discovery(), Competitor, CompetitorEvidence, _company_key(), CompetitorEvidenceRepository, CompetitorRepository, _website_key(), competitor_repo() (+9 more)

### Community 3 - "crypto.py"
Cohesion: 0.23
Nodes (4): decrypt_bytes(), encrypt_bytes(), EncryptionConfigurationError, _keyring()

### Community 4 - "agents/company_researcher.py"
Cohesion: 0.09
Nodes (21): build_evidence_from_result(), classify_evidence_type(), detect_conflicts(), _domain_of(), _is_trusted_domain(), score_confidence(), Evidence, EvidenceCollection (+13 more)

### Community 5 - "test_persistence_company.py"
Cohesion: 0.10
Nodes (12): _persist_company_research(), CompanyProfile, EvidenceClaim, CompanyRepository, EvidenceRepository, company_repo(), evidence_repo(), test_company_repository_create_and_get() (+4 more)

### Community 6 - "page.js"
Cohesion: 0.06
Nodes (66): metadata, RootLayout(), Home(), handleLogin(), handleLogout(), handleOrganizationChange(), restoreSession(), ReportDisplay() (+58 more)

### Community 7 - "test_sqlite_security.py"
Cohesion: 0.17
Nodes (16): Base, AuditEvent, AuthSession, Organization, OrganizationMembership, RateLimitBucket, RefreshToken, User (+8 more)

### Community 8 - "test_service.py"
Cohesion: 0.13
Nodes (12): get_research_endpoint(), get_research(), list_research_ids(), disable_live_llm(), _skip_persistence(), _submit(), test_get_research_missing_raises_not_found(), test_get_research_returns_stored_result() (+4 more)

### Community 9 - "test_agent_base.py"
Cohesion: 0.10
Nodes (17): BaseAgent, fetch_page(), retry_async(), validate_url_for_fetch(), test_base_agent_rate_limited_search_budget(), test_base_agent_search_cache(), test_fetch_page_blocks_private_url(), test_fetch_page_does_not_use_ip_literal_as_tls_sni() (+9 more)

### Community 10 - "endpoints/auth.py"
Cohesion: 0.16
Nodes (26): accept_invitation(), accept_invitation_existing(), _check_origin(), _clear_auth_cookies(), _create_invitation(), create_organization(), create_organization_invitation(), create_platform_invitation() (+18 more)

### Community 11 - "LLMConfigurationError"
Cohesion: 0.13
Nodes (7): LLMConfigurationError, BaseLLMClient, LLMMessage, OpenRouterLLMClient, test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises()

### Community 12 - "state.py"
Cohesion: 0.13
Nodes (7): _evidence_validator(), evidence_validator_mock(), research_planner(), _research_planner(), _strategic_analyst(), strategic_analyst_mock(), Extensibility (future phases)

### Community 13 - "test_graph.py"
Cohesion: 0.14
Nodes (14): build_graph(), get_graph(), test_graph_execution_order_includes_competitor_discovery(), _disable_live_llm(), _skip_persistence(), test_build_graph_produces_expected_nodes(), test_competitor_and_search_results_are_checkpointed(), test_full_graph_execution_all_nodes_completed() (+6 more)

### Community 14 - "DatabaseManager"
Cohesion: 0.09
Nodes (5): DatabaseManager, DatabaseUnavailableError, test_base_declarative(), test_database_manager_starts_without_url(), test_session_factory_raises_when_unavailable()

### Community 15 - "CompanyProfile"
Cohesion: 0.18
Nodes (7): CompanyProfile, CompanySize, test_company_profile_full(), test_company_profile_minimal(), test_company_profile_rejects_bad_website(), test_company_size(), test_company_size_max_gte_min()

### Community 16 - "test_company_researcher_node.py"
Cohesion: 0.16
Nodes (8): disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_company_researcher(), test_node_records_failure_safely(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm(), UnavailableLLMClient

### Community 17 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.06
Nodes (29): Development Roadmap, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2B — Competitor Discovery Agent, Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned), Ponytail and combined Copilot workflow (+21 more)

### Community 19 - "competitor_researcher.py"
Cohesion: 0.13
Nodes (16): classify_from_factors(), classify_from_score(), compute_text_overlap(), score_qualification(), CompetitorType, QualificationFactor, test_classifies_all_competitor_types_from_overlap_evidence(), test_classify_from_score_direct() (+8 more)

### Community 20 - "test_crypto_security.py"
Cohesion: 0.16
Nodes (12): _join_envelope(), _settings(), _split_envelope(), test_aes_gcm_uses_unique_12_byte_nonces_and_round_trips(), test_all_sensitive_orm_columns_use_encrypted_types(), test_checkpoint_adapter_rejects_plaintext_channel_values(), test_checkpoint_serializer_rejects_unencrypted_payloads(), test_checkpointer_defaults_to_encryption_and_encrypts_pending_writes() (+4 more)

### Community 21 - "AuthenticatedUser"
Cohesion: 0.10
Nodes (24): AuthenticatedUser, OrganizationContext, Permission, require_permission(), require_platform_admin(), authenticated_test_context(), current_user(), organization_context() (+16 more)

### Community 22 - "SearchQuery"
Cohesion: 0.11
Nodes (8): SearchProvider, MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_provider_is_abstract()

### Community 23 - "get_settings"
Cohesion: 0.08
Nodes (10): health(), get_settings(), get_sync_database_url(), get_logger(), database_health(), get_session(), _build_search_provider(), _company_researcher() (+2 more)

### Community 24 - "CompetitorProfile"
Cohesion: 0.14
Nodes (10): CompetitorCollection, CompetitorEvidenceItem, CompetitorProfile, test_competitor_collection(), test_competitor_evidence_requires_a_valid_http_source(), test_competitor_profile_full(), test_competitor_profile_minimal(), test_competitor_profile_rejects_bad_type() (+2 more)

### Community 25 - "security/auth.py"
Cohesion: 0.09
Nodes (20): get_db_session(), create_app(), request_security(), client_identity(), create_access_token(), decode_access_token(), enforce_rate_limit(), get_current_user() (+12 more)

### Community 26 - "AsyncPostgresSaver"
Cohesion: 0.16
Nodes (3): AsyncPostgresSaver, test_checkpointer_encrypts_checkpoint_values_and_metadata_and_reads_them(), LangGraph checkpointing

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.16
Nodes (7): disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_node_records_failure_safely(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient

### Community 28 - "ResearchRepository"
Cohesion: 0.07
Nodes (19): Research, ResearchRepository, session(), test_sqlite_encryption_failure_and_plaintext_rejection(), test_sqlite_research_company_competitor_and_evidence_round_trip(), test_api_rate_limit_applies_before_authentication(), commit(), repo() (+11 more)

### Community 29 - "run_node"
Cohesion: 0.14
Nodes (10): make_metadata(), run_node(), utc_now_iso(), finalize_research(), _finalize_research(), initialize_research(), _initialize_research(), _report_generator() (+2 more)

### Community 30 - "SearchResult"
Cohesion: 0.13
Nodes (9): SearchResultCache, SearchResult, DummyProvider, test_search_result_cache(), test_search_query_creation(), test_search_query_priority_bounds(), test_search_result_creation(), test_search_result_normalizes_domain() (+1 more)

### Community 31 - "Settings"
Cohesion: 0.12
Nodes (6): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default()

### Community 32 - "exceptions.py"
Cohesion: 0.08
Nodes (12): upgrade(), upgrade(), upgrade(), upgrade(), acis_exception_handler(), ACISException, _error_payload(), NotFoundError (+4 more)

### Community 33 - "LLMResponse"
Cohesion: 0.12
Nodes (4): LLMResponse, FakeLLMClient, FakeLLMClient, test_llm_response_structure()

### Community 34 - "test_nodes.py"
Cohesion: 0.38
Nodes (11): _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_finalize_research_success_no_errors(), test_initialize_research(), test_nodes_record_execution_metadata() (+3 more)

### Community 35 - "test_company_researcher_agent.py"
Cohesion: 0.26
Nodes (7): _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm(), test_agent_research_without_llm(), test_evidence_items_have_provenance(), UnavailableLLMClient

### Community 37 - "models/competitor.py"
Cohesion: 0.18
Nodes (4): decrypt_text(), EncryptedJSON, EncryptedText, test_orm_encrypted_types_hide_plaintext_and_reject_plaintext_storage()

### Community 38 - "company_researcher"
Cohesion: 0.13
Nodes (14): company_researcher(), competitor_discovery(), Agent Design — ACIS LangGraph Multi-Agent System (Phase 1 + 1.5 + 2A + 2B), Company Research Agent pipeline, Competitor Discovery Agent pipeline (Phase 2B), Design principles, Error handling, Persistence and checkpointing (Phase 1.5 + 2A) (+6 more)

### Community 39 - "ResearchState"
Cohesion: 0.18
Nodes (5): ResearchState, test_graph_failure_does_not_expose_exception_content(), test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields()

### Community 40 - "0005_encrypt_sensitive_payloads.py"
Cohesion: 0.24
Nodes (8): _encode_field(), _encrypt_column(), _encrypt_existing_checkpoints(), _encrypt_identity_email(), upgrade(), encrypt_checkpoint_payload(), encrypt_text(), validate_encryption_configuration()

### Community 41 - "Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B"
Cohesion: 0.18
Nodes (10): Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B, Company Research Agent pipeline (Phase 2A), Database degradation, Frontend, High-level data flow, Overview, Persistent storage: company profiles and evidence, Persistent storage (`researches` table) (+2 more)

### Community 42 - "sqlite_security_environment"
Cohesion: 0.29
Nodes (4): sqlite_client(), sqlite_security_environment(), create_test_app(), override_db_session()

### Community 45 - "test_auth_and_tenant_isolation.py"
Cohesion: 0.16
Nodes (13): _bootstrap_admin(), main(), email_lookup_hash(), hash_password(), verify_password(), authenticated_client(), test_csrf_and_origin_are_required_for_refresh(), test_invitation_expiry_single_use_and_role_assignment() (+5 more)

### Community 46 - "deduplicate_competitors"
Cohesion: 0.33
Nodes (4): deduplicate_competitors(), _domain_of(), test_deduplicate_competitors_by_domain(), test_deduplicate_competitors_by_name()

### Community 47 - "EncryptedCheckpointSerializer"
Cohesion: 0.36
Nodes (3): EncryptedCheckpointSerializer, test_encrypted_text_and_checkpoint_payload_round_trip(), test_checkpoint_serializer_round_trips_langgraph_value_types()

### Community 48 - "get_url"
Cohesion: 0.29
Nodes (3): get_url(), run_migrations_offline(), run_migrations_online()

### Community 51 - "test_checkpoint.py"
Cohesion: 0.12
Nodes (9): _company_researcher(), company_researcher_mock(), _competitor_discovery(), competitor_discovery_mock(), _build_graph(), _reset_db_each_test(), test_checkpointer_setup_creates_tables(), test_database_available_for_checkpointing() (+1 more)

### Community 53 - "re"
Cohesion: 0.25
Nodes (3): extract_keywords(), _normalize_name(), pytest_configure()

### Community 55 - "CompanyResearcherAgent"
Cohesion: 0.15
Nodes (3): AgentBudget, CompanyResearcherAgent, test_agent_budget_defaults()

### Community 60 - "LLMConfig"
Cohesion: 0.13
Nodes (8): LLMConfig, LLMFactory, test_llm_client_configured_with_key(), test_complete_without_api_key_raises_clear_error(), test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured(), test_llm_factory_is_lazy_until_client_requested(), LLM abstraction

### Community 63 - "main.py"
Cohesion: 0.12
Nodes (4): unhandled_exception_handler(), validation_exception_handler(), lifespan(), root()

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 495 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `research_service.py`, `test_competitor_persistence.py`, `crypto.py`, `agents/company_researcher.py`, `test_persistence_company.py`, `test_sqlite_security.py`, `endpoints/auth.py`, `DatabaseManager`, `AuthenticatedUser`, `security/auth.py`, `ResearchRepository`, `Settings`, `test_company_researcher_agent.py`, `company_researcher`, `0005_encrypt_sensitive_payloads.py`, `test_auth_and_tenant_isolation.py`, `get_url`, `test_checkpoint.py`, `LLMConfig`, `main.py`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `research_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09581646423751687 - nodes in this community are weakly interconnected._
- **Why does `ResearchState` connect `ResearchState` to `research_service.py`, `test_nodes.py`, `agents/company_researcher.py`, `company_researcher`, `state.py`, `test_graph.py`, `EncryptedCheckpointSerializer`, `test_company_researcher_node.py`, `AI Competitive Intelligence System (ACIS)`, `test_checkpoint.py`, `test_crypto_security.py`, `get_settings`, `security/auth.py`, `test_competitor_discovery_node.py`, `run_node`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_competitor_persistence.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07607843137254902 - nodes in this community are weakly interconnected._