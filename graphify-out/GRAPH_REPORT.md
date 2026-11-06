# Graph Report - ai-competitive-intelligence  (2026-11-06)

## Corpus Check
- 135 files · ~65,736 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1676 nodes · 4585 edges · 75 communities (52 shown, 23 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 608 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a16b53e9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- research_service.py
- asyncio
- test_competitor_persistence.py
- crypto.py
- CompanyResearcherAgent
- test_evidence_validator_adversarial.py
- page.js
- test_sqlite_security.py
- test_strategic_analyst_node.py
- agents/base.py
- get_settings
- LLMConfigurationError
- run_node
- test_graph.py
- DatabaseManager
- BaseAgent
- company_researcher
- AI Competitive Intelligence System (ACIS)
- CompetitorResearcherAgent
- test_competitor_intelligence.py
- test_crypto_security.py
- AuthenticatedUser
- SearchQuery
- database.py
- CompetitorProfile
- security/auth.py
- AsyncPostgresSaver
- test_competitor_discovery_node.py
- test_persistence.py
- agents/evidence_validator.py
- SearchResult
- Settings
- agents/company_researcher.py
- StrategicAnalystAgent
- test_nodes.py
- deduplicate_competitors
- test_evidence_validator.py
- sqlite_security_environment
- _canonical_domain
- ResearchState
- 0005_encrypt_sensitive_payloads.py
- _clean_snippet
- models/company.py
- DuckDuckGoProvider
- intelligence/competitor.py
- ResearchRepository
- pytest
- EncryptedCheckpointSerializer
- get_url
- .assess_freshness
- test_checkpoint.py
- AgentBudget
- sqlalchemy
- compilerOptions
- next.config.js
- datetime
- llm.py
- EvidenceValidatorAgent
- test_auth_security.py
- test_api_rate_limit_applies_before_authentication
- config.py
- _normalize_email

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 94 edges
2. `get_settings()` - 67 edges
3. `SearchResult` - 50 edges
4. `CompetitorResearcherAgent` - 46 edges
5. `StrategicAnalystAgent` - 45 edges
6. `run_node()` - 37 edges
7. `SearchQuery` - 37 edges
8. `ResearchError` - 36 edges
9. `MockSearchProvider` - 36 edges
10. `EvidenceValidatorAgent` - 34 edges

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

## Communities (75 total, 23 thin omitted)

### Community 0 - "research_service.py"
Cohesion: 0.08
Nodes (24): NodeExecutionMetadata, ResearchRequest, ResearchResult, _fetch_from_db(), _get_repository(), get_research(), list_research_ids(), _new_id() (+16 more)

### Community 1 - "asyncio"
Cohesion: 0.05
Nodes (32): LLMResponse, CompanyProfile, CompanySize, FakeLLMClient, _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm() (+24 more)

### Community 2 - "test_competitor_persistence.py"
Cohesion: 0.07
Nodes (18): _persist_competitor_discovery(), _persist_evidence_validation(), Competitor, CompetitorEvidence, _company_key(), CompetitorEvidenceRepository, CompetitorRepository, _website_key() (+10 more)

### Community 3 - "crypto.py"
Cohesion: 0.20
Nodes (5): decrypt_bytes(), encrypt_bytes(), EncryptionConfigurationError, _keyring(), validate_encryption_configuration()

### Community 4 - "CompanyResearcherAgent"
Cohesion: 0.05
Nodes (33): CompanyResearcherAgent, _company_researcher(), build_evidence_from_result(), classify_evidence_type(), detect_conflicts(), _domain_of(), _is_trusted_domain(), score_confidence() (+25 more)

### Community 5 - "test_evidence_validator_adversarial.py"
Cohesion: 0.05
Nodes (21): ClaimEvidenceMatch, agent(), test_adversarial_prompt_injection_attempts_neutralized(), test_business_model_contradiction(), test_confidence_scores_strictly_bounded_between_zero_and_one(), test_contradiction_detection_preserves_both_sides(), test_contradictory_product_availability(), test_different_billing_frequencies_conflict() (+13 more)

### Community 6 - "page.js"
Cohesion: 0.06
Nodes (66): metadata, RootLayout(), Home(), handleLogin(), handleLogout(), handleOrganizationChange(), restoreSession(), ReportDisplay() (+58 more)

### Community 7 - "test_sqlite_security.py"
Cohesion: 0.11
Nodes (28): _bootstrap_admin(), main(), Base, AuditEvent, AuthSession, Organization, OrganizationMembership, RateLimitBucket (+20 more)

### Community 8 - "test_strategic_analyst_node.py"
Cohesion: 0.11
Nodes (9): _persist_strategic_analysis(), strategic_analyst(), _strategic_analyst(), StrategyRepository, test_strategic_analyst_node_executes_and_populates_state(), test_strategic_analyst_node_requires_company_name(), test_strategic_analyst_persists_to_sqlite(), test_strategic_analyst_retry_idempotency() (+1 more)

### Community 9 - "agents/base.py"
Cohesion: 0.14
Nodes (8): fetch_page(), _resolve_public_addresses(), retry_async(), validate_url_for_fetch(), test_retry_async_non_transient_not_retried(), test_retry_async_transient(), test_validate_url_for_fetch_allows_public(), test_validate_url_for_fetch_blocks_private()

### Community 10 - "get_settings"
Cohesion: 0.18
Nodes (26): accept_invitation(), accept_invitation_existing(), _check_origin(), _clear_auth_cookies(), _create_invitation(), create_organization(), create_organization_invitation(), create_platform_invitation() (+18 more)

### Community 11 - "LLMConfigurationError"
Cohesion: 0.16
Nodes (7): LLMConfigurationError, LLMMessage, OpenRouterLLMClient, test_llm_client_configured_with_key(), test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises()

### Community 12 - "run_node"
Cohesion: 0.09
Nodes (16): make_metadata(), run_node(), utc_now_iso(), _evidence_validator(), evidence_validator_mock(), finalize_research(), _finalize_research(), initialize_research() (+8 more)

### Community 13 - "test_graph.py"
Cohesion: 0.13
Nodes (15): build_graph(), get_graph(), test_graph_execution_order_includes_company_researcher(), test_graph_execution_order_includes_competitor_discovery(), _disable_live_llm(), _skip_persistence(), test_build_graph_produces_expected_nodes(), test_competitor_and_search_results_are_checkpointed() (+7 more)

### Community 14 - "DatabaseManager"
Cohesion: 0.09
Nodes (5): DatabaseManager, DatabaseUnavailableError, test_base_declarative(), test_database_manager_starts_without_url(), test_session_factory_raises_when_unavailable()

### Community 15 - "BaseAgent"
Cohesion: 0.14
Nodes (10): BaseAgent, test_base_agent_rate_limited_search_budget(), test_base_agent_search_cache(), test_fetch_page_blocks_private_url(), test_fetch_page_does_not_use_ip_literal_as_tls_sni(), test_fetch_page_pins_dns_result_and_preserves_tls_hostname(), resolve(), respond() (+2 more)

### Community 16 - "company_researcher"
Cohesion: 0.09
Nodes (18): company_researcher(), disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_node_records_failure_safely(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm(), UnavailableLLMClient (+10 more)

### Community 17 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.06
Nodes (29): Development Roadmap, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2B — Competitor Discovery Agent, Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned), Ponytail and combined Copilot workflow (+21 more)

### Community 19 - "test_competitor_intelligence.py"
Cohesion: 0.16
Nodes (13): classify_from_score(), compute_text_overlap(), extract_keywords(), score_qualification(), test_classify_from_score_direct(), test_classify_from_score_emerging(), test_classify_from_score_indirect(), test_classify_from_score_substitute() (+5 more)

### Community 20 - "test_crypto_security.py"
Cohesion: 0.16
Nodes (13): decrypt_text(), _join_envelope(), _settings(), _split_envelope(), test_aes_gcm_uses_unique_12_byte_nonces_and_round_trips(), test_all_sensitive_orm_columns_use_encrypted_types(), test_checkpoint_adapter_rejects_plaintext_channel_values(), test_checkpoint_serializer_rejects_unencrypted_payloads() (+5 more)

### Community 21 - "AuthenticatedUser"
Cohesion: 0.13
Nodes (17): AuthenticatedUser, authenticated_test_context(), current_user(), organization_context(), _client(), test_get_research_by_id(), test_get_research_not_found(), test_health_endpoint() (+9 more)

### Community 22 - "SearchQuery"
Cohesion: 0.13
Nodes (8): SearchProvider, MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_provider_is_abstract()

### Community 23 - "database.py"
Cohesion: 0.08
Nodes (6): get_sync_database_url(), configure_logging(), get_logger(), _MaskingFormatter, database_health(), get_session()

### Community 24 - "CompetitorProfile"
Cohesion: 0.14
Nodes (10): CompetitorCollection, CompetitorEvidenceItem, CompetitorProfile, test_competitor_collection(), test_competitor_evidence_requires_a_valid_http_source(), test_competitor_profile_full(), test_competitor_profile_minimal(), test_competitor_profile_rejects_bad_type() (+2 more)

### Community 25 - "security/auth.py"
Cohesion: 0.08
Nodes (13): create_app(), request_security(), lifespan(), root(), client_identity(), enforce_rate_limit(), get_current_user(), get_organization_context() (+5 more)

### Community 26 - "AsyncPostgresSaver"
Cohesion: 0.15
Nodes (5): AsyncPostgresSaver, commit(), test_checkpointer_encrypts_checkpoint_values_and_metadata_and_reads_them(), LangGraph checkpointing, Phase 1.5 — Integration Verification & Database Persistence (complete)

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.19
Nodes (6): disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient

### Community 28 - "test_persistence.py"
Cohesion: 0.21
Nodes (11): repo(), _rid(), session(), test_alembic_table_exists(), test_database_is_configured(), test_repository_create_and_get_by_id(), test_repository_get_by_id_wrong_organization_returns_none(), test_repository_list_by_organization() (+3 more)

### Community 29 - "agents/evidence_validator.py"
Cohesion: 0.15
Nodes (7): _availability_status(), _detect_prompt_injection(), _extract_numbers(), _extract_structured_quantities(), _has_negation(), _stem(), _tokens()

### Community 30 - "SearchResult"
Cohesion: 0.13
Nodes (9): SearchResultCache, SearchResult, DummyProvider, test_search_result_cache(), test_search_query_creation(), test_search_query_priority_bounds(), test_search_result_creation(), test_search_result_normalizes_domain() (+1 more)

### Community 31 - "Settings"
Cohesion: 0.12
Nodes (6): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default()

### Community 32 - "agents/company_researcher.py"
Cohesion: 0.13
Nodes (10): acis_exception_handler(), ACISException, _error_payload(), NotFoundError, ResearchError, unhandled_exception_handler(), validation_exception_handler(), ValidationError (+2 more)

### Community 33 - "StrategicAnalystAgent"
Cohesion: 0.05
Nodes (31): StrategicAnalystAgent, CompetitivePositioning, CompetitiveThreat, CompetitorComparison, DimensionComparison, EvidenceGap, FeatureAvailability, InformationClass (+23 more)

### Community 34 - "test_nodes.py"
Cohesion: 0.24
Nodes (15): _company_researcher(), company_researcher_mock(), _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_evidence_validator_real_node() (+7 more)

### Community 35 - "deduplicate_competitors"
Cohesion: 0.25
Nodes (5): deduplicate_competitors(), _domain_of(), _normalize_name(), test_deduplicate_competitors_by_domain(), test_deduplicate_competitors_by_name()

### Community 36 - "test_evidence_validator.py"
Cohesion: 0.11
Nodes (6): _canonicalize_url(), SourceCredibilityTier, agent(), test_credibility_assessment_across_tiers(), test_url_canonicalization_strips_tracking_params_and_lowercases(), test_validate_state_generates_human_review_queue_and_summary()

### Community 37 - "sqlite_security_environment"
Cohesion: 0.29
Nodes (4): sqlite_client(), sqlite_security_environment(), create_test_app(), override_db_session()

### Community 38 - "_canonical_domain"
Cohesion: 0.29
Nodes (4): _canonical_domain(), _root_domain(), test_root_domain_deduplication_prevents_subdomain_gaming(), test_domain_canonicalization()

### Community 39 - "ResearchState"
Cohesion: 0.11
Nodes (10): competitor_discovery(), _competitor_discovery(), ResearchState, test_node_records_failure_safely(), test_graph_failure_does_not_expose_exception_content(), test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields() (+2 more)

### Community 40 - "0005_encrypt_sensitive_payloads.py"
Cohesion: 0.33
Nodes (7): _encode_field(), _encrypt_column(), _encrypt_existing_checkpoints(), _encrypt_identity_email(), upgrade(), encrypt_checkpoint_payload(), encrypt_text()

### Community 42 - "models/company.py"
Cohesion: 0.17
Nodes (3): EncryptedJSON, EncryptedText, test_orm_encrypted_types_hide_plaintext_and_reject_plaintext_storage()

### Community 43 - "DuckDuckGoProvider"
Cohesion: 0.18
Nodes (4): _build_search_provider(), _build_search_provider(), DuckDuckGoProvider, _is_private_or_internal()

### Community 44 - "intelligence/competitor.py"
Cohesion: 0.18
Nodes (5): build_competitor_evidence(), classify_from_factors(), CompetitorType, QualificationFactor, test_classifies_all_competitor_types_from_overlap_evidence()

### Community 45 - "ResearchRepository"
Cohesion: 0.05
Nodes (25): _persist_company_research(), evidence_validator(), CompanyProfile, EvidenceClaim, Research, CompanyRepository, EvidenceRepository, ResearchRepository (+17 more)

### Community 47 - "EncryptedCheckpointSerializer"
Cohesion: 0.39
Nodes (3): EncryptedCheckpointSerializer, test_encrypted_text_and_checkpoint_payload_round_trip(), test_checkpoint_serializer_round_trips_langgraph_value_types()

### Community 48 - "get_url"
Cohesion: 0.29
Nodes (3): get_url(), run_migrations_offline(), run_migrations_online()

### Community 51 - "test_checkpoint.py"
Cohesion: 0.12
Nodes (9): _competitor_discovery(), competitor_discovery_mock(), _report_generator(), report_generator_mock(), _build_graph(), _reset_db_each_test(), test_checkpointer_setup_creates_tables(), test_database_available_for_checkpointing() (+1 more)

### Community 54 - "sqlalchemy"
Cohesion: 0.21
Nodes (4): upgrade(), upgrade(), upgrade(), upgrade()

### Community 59 - "datetime"
Cohesion: 0.14
Nodes (9): get_research_endpoint(), submit_research(), ResearchResponse, ResearchStatusResponse, OrganizationContext, Permission, require_permission(), test_role_permission_matrix_and_platform_admin_boundary() (+1 more)

### Community 60 - "llm.py"
Cohesion: 0.11
Nodes (9): BaseLLMClient, get_llm_client(), LLMConfig, LLMFactory, test_complete_without_api_key_raises_clear_error(), test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured(), test_llm_factory_is_lazy_until_client_requested() (+1 more)

### Community 63 - "EvidenceValidatorAgent"
Cohesion: 0.13
Nodes (8): EvidenceValidatorAgent, _evidence_validator(), ClaimValidationResult, ContradictionRecord, FreshnessAssessment, HumanReviewItem, SourceCredibilityAssessment, ValidationSummary

### Community 74 - "test_auth_security.py"
Cohesion: 0.19
Nodes (11): get_db_session(), create_access_token(), decode_access_token(), verify_password(), _settings(), test_access_token_validates_and_rejects_tampering(), test_argon2id_password_hashing_and_password_bounds(), test_csrf_requires_allowed_origin_and_matching_double_submit_token() (+3 more)

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 622 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ResearchState` connect `ResearchState` to `research_service.py`, `StrategicAnalystAgent`, `test_nodes.py`, `CompanyResearcherAgent`, `test_strategic_analyst_node.py`, `test_auth_security.py`, `run_node`, `test_graph.py`, `ResearchRepository`, `EncryptedCheckpointSerializer`, `company_researcher`, `AI Competitive Intelligence System (ACIS)`, `test_checkpoint.py`, `test_crypto_security.py`, `test_competitor_discovery_node.py`, `EvidenceValidatorAgent`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 47 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `research_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07777777777777778 - nodes in this community are weakly interconnected._
- **Why does `get_settings()` connect `get_settings` to `research_service.py`, `asyncio`, `test_competitor_persistence.py`, `crypto.py`, `CompanyResearcherAgent`, `test_sqlite_security.py`, `test_strategic_analyst_node.py`, `agents/base.py`, `run_node`, `DatabaseManager`, `company_researcher`, `AuthenticatedUser`, `database.py`, `security/auth.py`, `test_persistence.py`, `agents/evidence_validator.py`, `Settings`, `agents/company_researcher.py`, `StrategicAnalystAgent`, `ResearchState`, `0005_encrypt_sensitive_payloads.py`, `DuckDuckGoProvider`, `ResearchRepository`, `get_url`, `test_checkpoint.py`, `llm.py`, `EvidenceValidatorAgent`, `test_auth_security.py`, `config.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `asyncio` be split into smaller, more focused modules?**
  _Cohesion score 0.053923541247484906 - nodes in this community are weakly interconnected._