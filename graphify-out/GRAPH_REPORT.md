# Graph Report - ai-competitive-intelligence  (2026-11-06)

## Corpus Check
- 128 files · ~54,701 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1485 nodes · 4044 edges · 81 communities (59 shown, 22 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 513 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c46c7239`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- research_service.py
- asyncio
- repositories/competitor.py
- crypto.py
- agents/company_researcher.py
- EvidenceRepository
- page.js
- test_sqlite_security.py
- test_service.py
- test_agent_base.py
- get_settings
- LLMConfigurationError
- builder.py
- test_graph.py
- DatabaseManager
- CompanyProfile
- test_company_researcher_node.py
- AI Competitive Intelligence System (ACIS)
- CompetitorResearcherAgent
- test_competitor_intelligence.py
- test_crypto_security.py
- AuthenticatedUser
- SearchQuery
- competitor_researcher.py
- CompetitorProfile
- security/auth.py
- AsyncPostgresSaver
- test_competitor_discovery_node.py
- test_persistence.py
- run_node
- SearchResult
- Settings
- exceptions.py
- test_llm_client.py
- test_nodes.py
- test_company_researcher_agent.py
- agents/evidence_validator.py
- EncryptedText
- company_researcher
- ResearchState
- 0005_encrypt_sensitive_payloads.py
- package.json
- database.py
- DuckDuckGoProvider
- intelligence/competitor.py
- ResearchError
- test_persistence_company.py
- EncryptedCheckpointSerializer
- get_url
- test_competitor_persistence.py
- test_checkpoint.py
- AgentBudget
- compute_text_overlap
- sqlalchemy
- CompanyResearcherAgent
- Evidence
- compilerOptions
- next.config.js
- endpoints/research.py
- llm.py
- CompanyRepository
- nodes/evidence_validator.py
- get_db_session
- test_api_rate_limit_applies_before_authentication
- health.py
- _normalize_email
- _competitor_discovery
- _domain_of

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 81 edges
2. `get_settings()` - 63 edges
3. `SearchResult` - 50 edges
4. `CompetitorResearcherAgent` - 46 edges
5. `SearchQuery` - 37 edges
6. `run_node()` - 35 edges
7. `CompanyResearcherAgent` - 33 edges
8. `ResearchError` - 33 edges
9. `MockSearchProvider` - 33 edges
10. `EvidenceValidatorAgent` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Phase 2B — Competitor Discovery Agent` --references--> `competitor_discovery_mock()`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/nodes/competitor_discovery_mock.py
- `Design principles` --references--> `ResearchState`  [INFERRED]
  docs/agent-design.md → backend/app/graph/state.py
- `Phase 0 + Phase 1 (complete)` --references--> `ResearchState`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/state.py
- `Phase 1.5 — Integration Verification & Database Persistence (complete)` --references--> `commit()`  [INFERRED]
  docs/development-roadmap.md → backend/tests/unit/test_auth_security.py
- `SSRF/DNS-rebinding mitigation` --references--> `fetch_page()`  [EXTRACTED]
  docs/development-roadmap.md → backend/app/agents/base.py

## Import Cycles
- None detected.

## Communities (81 total, 22 thin omitted)

### Community 0 - "research_service.py"
Cohesion: 0.16
Nodes (11): NodeExecutionMetadata, ResearchResult, _fetch_from_db(), _get_repository(), _new_id(), _persist_result(), _row_to_result(), run_research() (+3 more)

### Community 1 - "asyncio"
Cohesion: 0.20
Nodes (14): _company_profile(), _make_agent(), test_agent_competitor_discovery_with_llm(), test_agent_competitor_discovery_without_llm(), test_agent_rejects_empty_company_name(), test_competitor_profiles_have_required_fields(), test_conflicting_source_status_and_duplicate_candidates_are_preserved(), test_independent_source_corroboration_and_unknown_fields_are_explicit() (+6 more)

### Community 2 - "repositories/competitor.py"
Cohesion: 0.11
Nodes (6): _persist_competitor_discovery(), CompetitorEvidence, _company_key(), CompetitorEvidenceRepository, CompetitorRepository, _website_key()

### Community 3 - "crypto.py"
Cohesion: 0.15
Nodes (7): _encrypt_existing_checkpoints(), decrypt_bytes(), encrypt_bytes(), encrypt_checkpoint_payload(), EncryptionConfigurationError, _keyring(), pytest_configure()

### Community 4 - "agents/company_researcher.py"
Cohesion: 0.13
Nodes (13): build_evidence_from_result(), classify_evidence_type(), detect_conflicts(), _is_trusted_domain(), score_confidence(), EvidenceType, VerificationStatus, _make_result() (+5 more)

### Community 5 - "EvidenceRepository"
Cohesion: 0.21
Nodes (3): _persist_evidence_validation(), EvidenceClaim, EvidenceRepository

### Community 6 - "page.js"
Cohesion: 0.18
Nodes (31): Home(), handleLogin(), handleLogout(), handleOrganizationChange(), restoreSession(), ReportDisplay(), ResearchForm(), handleSubmit() (+23 more)

### Community 7 - "test_sqlite_security.py"
Cohesion: 0.10
Nodes (33): list_user_organizations(), _bootstrap_admin(), main(), AuditEvent, AuthSession, Organization, OrganizationMembership, RateLimitBucket (+25 more)

### Community 8 - "test_service.py"
Cohesion: 0.16
Nodes (11): get_research(), list_research_ids(), disable_live_llm(), _skip_persistence(), _submit(), test_get_research_missing_raises_not_found(), test_get_research_returns_stored_result(), test_run_research_returns_structured_result() (+3 more)

### Community 9 - "test_agent_base.py"
Cohesion: 0.10
Nodes (15): fetch_page(), _resolve_public_addresses(), retry_async(), validate_url_for_fetch(), test_fetch_page_blocks_private_url(), test_fetch_page_does_not_use_ip_literal_as_tls_sni(), test_fetch_page_pins_dns_result_and_preserves_tls_hostname(), resolve() (+7 more)

### Community 10 - "get_settings"
Cohesion: 0.19
Nodes (27): accept_invitation(), accept_invitation_existing(), _check_origin(), _clear_auth_cookies(), _create_invitation(), create_organization(), create_organization_invitation(), create_platform_invitation() (+19 more)

### Community 11 - "LLMConfigurationError"
Cohesion: 0.13
Nodes (8): LLMConfigurationError, BaseLLMClient, LLMMessage, OpenRouterLLMClient, test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises(), LLM abstraction

### Community 12 - "builder.py"
Cohesion: 0.12
Nodes (8): _evidence_validator(), evidence_validator_mock(), finalize_research(), _finalize_research(), _report_generator(), report_generator_mock(), Evidence Validation Agent pipeline (Phase 2E), The agents (nodes)

### Community 13 - "test_graph.py"
Cohesion: 0.15
Nodes (13): build_graph(), get_graph(), _disable_live_llm(), _skip_persistence(), test_build_graph_produces_expected_nodes(), test_competitor_and_search_results_are_checkpointed(), test_full_graph_execution_all_nodes_completed(), test_get_graph_returns_cached_compiled_graph() (+5 more)

### Community 14 - "DatabaseManager"
Cohesion: 0.07
Nodes (9): DatabaseManager, DatabaseUnavailableError, sqlite_client(), sqlite_security_environment(), create_test_app(), override_db_session(), test_base_declarative(), test_database_manager_starts_without_url() (+1 more)

### Community 15 - "CompanyProfile"
Cohesion: 0.17
Nodes (7): CompanyProfile, CompanySize, test_company_profile_full(), test_company_profile_minimal(), test_company_profile_rejects_bad_website(), test_company_size(), test_company_size_max_gte_min()

### Community 16 - "test_company_researcher_node.py"
Cohesion: 0.16
Nodes (8): disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_company_researcher(), test_node_records_failure_safely(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm(), UnavailableLLMClient

### Community 17 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.06
Nodes (29): Development Roadmap, Graphify installation and use, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2B — Competitor Discovery Agent, Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned) (+21 more)

### Community 19 - "test_competitor_intelligence.py"
Cohesion: 0.18
Nodes (12): classify_from_score(), deduplicate_competitors(), score_qualification(), test_classify_from_score_direct(), test_classify_from_score_emerging(), test_classify_from_score_indirect(), test_classify_from_score_substitute(), test_deduplicate_competitors_by_domain() (+4 more)

### Community 20 - "test_crypto_security.py"
Cohesion: 0.26
Nodes (11): _join_envelope(), _settings(), _split_envelope(), test_aes_gcm_uses_unique_12_byte_nonces_and_round_trips(), test_checkpoint_adapter_rejects_plaintext_channel_values(), test_checkpoint_serializer_rejects_unencrypted_payloads(), test_checkpointer_defaults_to_encryption_and_encrypts_pending_writes(), test_ciphertext_or_nonce_modification_fails_authentication() (+3 more)

### Community 21 - "AuthenticatedUser"
Cohesion: 0.08
Nodes (26): get_research_endpoint(), submit_research(), AuthenticatedUser, OrganizationContext, Permission, require_permission(), require_platform_admin(), authenticated_test_context() (+18 more)

### Community 22 - "SearchQuery"
Cohesion: 0.11
Nodes (9): SearchProvider, MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_provider_is_abstract() (+1 more)

### Community 23 - "competitor_researcher.py"
Cohesion: 0.10
Nodes (3): configure_logging(), get_logger(), _MaskingFormatter

### Community 24 - "CompetitorProfile"
Cohesion: 0.14
Nodes (10): CompetitorCollection, CompetitorEvidenceItem, CompetitorProfile, test_competitor_collection(), test_competitor_evidence_requires_a_valid_http_source(), test_competitor_profile_full(), test_competitor_profile_minimal(), test_competitor_profile_rejects_bad_type() (+2 more)

### Community 25 - "security/auth.py"
Cohesion: 0.07
Nodes (19): create_app(), request_security(), lifespan(), root(), client_identity(), decode_access_token(), enforce_rate_limit(), get_current_user() (+11 more)

### Community 26 - "AsyncPostgresSaver"
Cohesion: 0.16
Nodes (4): AsyncPostgresSaver, test_checkpointer_encrypts_checkpoint_values_and_metadata_and_reads_them(), LangGraph checkpointing, Phase 1.5 — Integration Verification & Database Persistence (complete)

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.15
Nodes (8): disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_competitor_discovery(), test_node_records_failure_safely(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient

### Community 28 - "test_persistence.py"
Cohesion: 0.21
Nodes (11): repo(), _rid(), session(), test_alembic_table_exists(), test_database_is_configured(), test_repository_create_and_get_by_id(), test_repository_get_by_id_wrong_organization_returns_none(), test_repository_list_by_organization() (+3 more)

### Community 29 - "run_node"
Cohesion: 0.21
Nodes (6): make_metadata(), run_node(), utc_now_iso(), initialize_research(), _initialize_research(), test_graph_failure_does_not_expose_exception_content()

### Community 30 - "SearchResult"
Cohesion: 0.13
Nodes (9): SearchResultCache, SearchResult, DummyProvider, test_search_result_cache(), test_search_query_creation(), test_search_query_priority_bounds(), test_search_result_creation(), test_search_result_normalizes_domain() (+1 more)

### Community 31 - "Settings"
Cohesion: 0.12
Nodes (6): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default()

### Community 32 - "exceptions.py"
Cohesion: 0.15
Nodes (9): acis_exception_handler(), ACISException, _error_payload(), NotFoundError, unhandled_exception_handler(), validation_exception_handler(), ValidationError, test_exception_error_codes_and_message() (+1 more)

### Community 33 - "test_llm_client.py"
Cohesion: 0.15
Nodes (4): LLMResponse, FakeLLMClient, test_llm_client_configured_with_key(), test_llm_response_structure()

### Community 34 - "test_nodes.py"
Cohesion: 0.23
Nodes (15): _company_researcher(), company_researcher_mock(), _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_evidence_validator_real_node() (+7 more)

### Community 35 - "test_company_researcher_agent.py"
Cohesion: 0.15
Nodes (8): FakeLLMClient, _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm(), test_agent_research_without_llm(), test_evidence_items_have_provenance(), UnavailableLLMClient

### Community 36 - "agents/evidence_validator.py"
Cohesion: 0.05
Nodes (23): _canonical_domain(), _canonicalize_url(), _clean_snippet(), _detect_claim_category(), _detect_prompt_injection(), EvidenceValidatorAgent, _extract_numbers(), _stem() (+15 more)

### Community 37 - "EncryptedText"
Cohesion: 0.27
Nodes (4): decrypt_text(), encrypt_text(), EncryptedText, test_orm_encrypted_types_hide_plaintext_and_reject_plaintext_storage()

### Community 38 - "company_researcher"
Cohesion: 0.09
Nodes (21): company_researcher(), competitor_discovery(), Agent Design — ACIS LangGraph Multi-Agent System (Phase 1 + 1.5 + 2A + 2B + 2E), Company Research Agent pipeline, Competitor Discovery Agent pipeline (Phase 2B), Design principles, Error handling, Persistence and checkpointing (Phase 1.5 + 2A) (+13 more)

### Community 39 - "ResearchState"
Cohesion: 0.15
Nodes (7): research_planner(), _research_planner(), ResearchState, test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields(), Extensibility (future phases)

### Community 40 - "0005_encrypt_sensitive_payloads.py"
Cohesion: 0.26
Nodes (5): _encode_field(), _encrypt_column(), _encrypt_identity_email(), upgrade(), validate_encryption_configuration()

### Community 41 - "package.json"
Cohesion: 0.06
Nodes (35): metadata, RootLayout(), NAV, Sidebar(), dependencies, clsx, lucide-react, next (+27 more)

### Community 42 - "database.py"
Cohesion: 0.13
Nodes (7): Base, get_sync_database_url(), CompanyProfile, Competitor, Research, EncryptedJSON, test_all_sensitive_orm_columns_use_encrypted_types()

### Community 43 - "DuckDuckGoProvider"
Cohesion: 0.22
Nodes (3): _build_search_provider(), DuckDuckGoProvider, _is_private_or_internal()

### Community 44 - "intelligence/competitor.py"
Cohesion: 0.14
Nodes (7): build_competitor_evidence(), classify_from_factors(), _domain_of(), _normalize_name(), CompetitorType, QualificationFactor, test_classifies_all_competitor_types_from_overlap_evidence()

### Community 45 - "ResearchError"
Cohesion: 0.18
Nodes (3): ResearchError, ResearchRepository, test_sqlite_research_company_competitor_and_evidence_round_trip()

### Community 46 - "test_persistence_company.py"
Cohesion: 0.16
Nodes (7): company_repo(), evidence_repo(), test_company_repository_create_and_get(), test_company_repository_org_isolation(), test_database_tables_exist(), test_evidence_repository_create_and_list(), test_evidence_repository_org_isolation()

### Community 47 - "EncryptedCheckpointSerializer"
Cohesion: 0.39
Nodes (3): EncryptedCheckpointSerializer, test_encrypted_text_and_checkpoint_payload_round_trip(), test_checkpoint_serializer_round_trips_langgraph_value_types()

### Community 48 - "get_url"
Cohesion: 0.29
Nodes (3): get_url(), run_migrations_offline(), run_migrations_online()

### Community 50 - "test_competitor_persistence.py"
Cohesion: 0.21
Nodes (10): competitor_repo(), evidence_repo(), session(), test_competitor_duplicate_prevention(), test_competitor_evidence_org_isolation(), test_competitor_evidence_repository(), test_competitor_lookup_is_scoped_by_research_and_organization(), test_competitor_repository_create_and_get() (+2 more)

### Community 51 - "test_checkpoint.py"
Cohesion: 0.12
Nodes (9): _competitor_discovery(), competitor_discovery_mock(), _strategic_analyst(), strategic_analyst_mock(), _build_graph(), _reset_db_each_test(), test_checkpointer_setup_creates_tables(), test_database_available_for_checkpointing() (+1 more)

### Community 52 - "AgentBudget"
Cohesion: 0.22
Nodes (5): AgentBudget, BaseAgent, test_agent_budget_defaults(), test_base_agent_rate_limited_search_budget(), test_base_agent_search_cache()

### Community 53 - "compute_text_overlap"
Cohesion: 0.25
Nodes (4): compute_text_overlap(), extract_keywords(), test_compute_text_overlap(), test_compute_text_overlap_identical()

### Community 54 - "sqlalchemy"
Cohesion: 0.21
Nodes (4): upgrade(), upgrade(), upgrade(), upgrade()

### Community 55 - "CompanyResearcherAgent"
Cohesion: 0.20
Nodes (3): CompanyResearcherAgent, _company_researcher(), Phase 2A: Real Company Research Agent

### Community 56 - "Evidence"
Cohesion: 0.21
Nodes (6): Evidence, EvidenceCollection, test_evidence_collection(), test_evidence_confidence_clamped(), test_evidence_creation(), test_evidence_rejects_bad_url()

### Community 59 - "endpoints/research.py"
Cohesion: 0.22
Nodes (3): ResearchRequest, ResearchResponse, ResearchStatusResponse

### Community 60 - "llm.py"
Cohesion: 0.16
Nodes (6): LLMConfig, LLMFactory, test_complete_without_api_key_raises_clear_error(), test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured(), test_llm_factory_is_lazy_until_client_requested()

### Community 63 - "nodes/evidence_validator.py"
Cohesion: 0.24
Nodes (5): evidence_validator(), _evidence_validator(), test_evidence_validator_node_evaluates_evidence_and_produces_summary(), test_evidence_validator_node_requires_research_question(), test_evidence_validator_persists_to_sqlite()

### Community 74 - "get_db_session"
Cohesion: 0.29
Nodes (3): get_db_session(), database_health(), get_session()

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 537 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ResearchState` connect `ResearchState` to `research_service.py`, `test_nodes.py`, `company_researcher`, `builder.py`, `test_graph.py`, `_competitor_discovery`, `test_company_researcher_node.py`, `EncryptedCheckpointSerializer`, `AI Competitive Intelligence System (ACIS)`, `test_checkpoint.py`, `test_crypto_security.py`, `CompanyResearcherAgent`, `SearchQuery`, `competitor_researcher.py`, `security/auth.py`, `test_competitor_discovery_node.py`, `run_node`, `nodes/evidence_validator.py`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 37 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repositories/competitor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11261261261261261 - nodes in this community are weakly interconnected._
- **Why does `get_settings()` connect `get_settings` to `research_service.py`, `crypto.py`, `agents/company_researcher.py`, `test_sqlite_security.py`, `DatabaseManager`, `AuthenticatedUser`, `competitor_researcher.py`, `security/auth.py`, `test_persistence.py`, `Settings`, `test_company_researcher_agent.py`, `agents/evidence_validator.py`, `company_researcher`, `0005_encrypt_sensitive_payloads.py`, `database.py`, `DuckDuckGoProvider`, `test_persistence_company.py`, `get_url`, `test_competitor_persistence.py`, `test_checkpoint.py`, `CompanyResearcherAgent`, `llm.py`, `nodes/evidence_validator.py`, `health.py`, `_competitor_discovery`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `crypto.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1471861471861472 - nodes in this community are weakly interconnected._