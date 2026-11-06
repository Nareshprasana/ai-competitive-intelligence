# Graph Report - ai-competitive-intelligence  (2026-11-06)

## Corpus Check
- 147 files · ~76,075 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1864 nodes · 5220 edges · 81 communities (62 shown, 19 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 738 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7f435eb0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- research_service.py
- asyncio
- test_competitor_persistence.py
- crypto.py
- VerificationStatus
- test_evidence_validator_adversarial.py
- page.js
- env.py
- Research
- run_node
- endpoints/auth.py
- OpenRouterLLMClient
- test_checkpoint.py
- test_graph.py
- DatabaseManager
- test_agent_base.py
- test_company_researcher_node.py
- AI Competitive Intelligence System (ACIS)
- CompetitorResearcherAgent
- CompetitorProfile
- test_crypto_security.py
- Organization
- MockSearchProvider
- typing
- agents/evidence_validator.py
- get_settings
- AsyncPostgresSaver
- test_competitor_discovery_node.py
- StrategicAnalystAgent
- EvidenceValidatorAgent
- SearchResult
- Settings
- ResearchError
- agents/strategic_analyst.py
- test_nodes.py
- test_company_researcher_agent.py
- test_evidence_validator.py
- ReportGeneratorAgent
- test_end_to_end_pipeline.py
- ResearchState
- CompanyProfile
- agents/report_generator.py
- models/company.py
- DuckDuckGoProvider
- test_persistence.py
- ResearchRepository
- test_sqlite_security.py
- EncryptedCheckpointSerializer
- ArtifactStorageService
- LLMResponse
- Evidence
- CompanyResearcherAgent
- AgentBudget
- EndToEndMockSearchProvider
- sqlite_security_environment
- CompanyRepository
- test_evidence_validator_node.py
- compilerOptions
- next.config.js
- security/auth.py
- LLMFactory
- test_api.py
- pytest
- _MaskingFormatter
- test_report_generator_persists_to_sqlite_and_storage
- test_persistence_company.py
- company_researcher
- Development Roadmap
- NumberedCanvas
- MarketOpportunity

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 109 edges
2. `get_settings()` - 73 edges
3. `SearchResult` - 53 edges
4. `CompetitorResearcherAgent` - 48 edges
5. `StrategicAnalystAgent` - 48 edges
6. `ResearchError` - 43 edges
7. `MockSearchProvider` - 41 edges
8. `Research` - 40 edges
9. `SearchQuery` - 40 edges
10. `run_node()` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Phase 2B — Competitor Discovery Agent` --references--> `competitor_discovery_mock()`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/nodes/competitor_discovery_mock.py
- `Design principles` --references--> `ResearchState`  [INFERRED]
  docs/agent-design.md → backend/app/graph/state.py
- `Phase 0 + Phase 1 (complete)` --references--> `ResearchState`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/state.py
- `SSRF/DNS-rebinding mitigation` --references--> `fetch_page()`  [EXTRACTED]
  docs/development-roadmap.md → backend/app/agents/base.py
- `Phase 2A — Real Company Research Agent (complete)` --references--> `BaseAgent`  [INFERRED]
  docs/development-roadmap.md → backend/app/agents/base.py

## Import Cycles
- None detected.

## Communities (81 total, 19 thin omitted)

### Community 0 - "research_service.py"
Cohesion: 0.07
Nodes (26): get_research_endpoint(), submit_research(), NodeExecutionMetadata, ResearchRequest, ResearchResponse, ResearchResult, ResearchStatusResponse, _fetch_from_db() (+18 more)

### Community 1 - "asyncio"
Cohesion: 0.20
Nodes (14): _company_profile(), _make_agent(), test_agent_competitor_discovery_with_llm(), test_agent_competitor_discovery_without_llm(), test_agent_rejects_empty_company_name(), test_competitor_profiles_have_required_fields(), test_conflicting_source_status_and_duplicate_candidates_are_preserved(), test_independent_source_corroboration_and_unknown_fields_are_explicit() (+6 more)

### Community 2 - "test_competitor_persistence.py"
Cohesion: 0.08
Nodes (17): _persist_competitor_discovery(), Competitor, CompetitorEvidence, _company_key(), CompetitorEvidenceRepository, CompetitorRepository, _website_key(), competitor_repo() (+9 more)

### Community 3 - "crypto.py"
Cohesion: 0.17
Nodes (9): _encrypt_existing_checkpoints(), decrypt_bytes(), encrypt_bytes(), encrypt_checkpoint_payload(), EncryptionConfigurationError, _keyring(), _split_envelope(), test_aes_gcm_uses_unique_12_byte_nonces_and_round_trips() (+1 more)

### Community 4 - "VerificationStatus"
Cohesion: 0.13
Nodes (13): build_evidence_from_result(), classify_evidence_type(), detect_conflicts(), _domain_of(), _is_trusted_domain(), score_confidence(), EvidenceType, VerificationStatus (+5 more)

### Community 5 - "test_evidence_validator_adversarial.py"
Cohesion: 0.05
Nodes (22): _root_domain(), agent(), test_adversarial_prompt_injection_attempts_neutralized(), test_business_model_contradiction(), test_confidence_scores_strictly_bounded_between_zero_and_one(), test_contradiction_detection_preserves_both_sides(), test_contradictory_product_availability(), test_different_billing_frequencies_conflict() (+14 more)

### Community 6 - "page.js"
Cohesion: 0.06
Nodes (66): metadata, RootLayout(), Home(), handleLogin(), handleLogout(), handleOrganizationChange(), restoreSession(), ReportDisplay() (+58 more)

### Community 7 - "env.py"
Cohesion: 0.16
Nodes (8): get_url(), run_migrations_offline(), run_migrations_online(), Base, AuditEvent, AuthSession, RateLimitBucket, RefreshToken

### Community 8 - "Research"
Cohesion: 0.11
Nodes (9): _persist_strategic_analysis(), strategic_analyst(), Research, StrategyRepository, test_strategic_analyst_node_executes_and_populates_state(), test_strategic_analyst_node_requires_company_name(), test_strategic_analyst_persists_to_sqlite(), test_strategic_analyst_retry_idempotency() (+1 more)

### Community 9 - "run_node"
Cohesion: 0.12
Nodes (12): make_metadata(), run_node(), utc_now_iso(), _evidence_validator(), evidence_validator_mock(), finalize_research(), _finalize_research(), initialize_research() (+4 more)

### Community 10 - "endpoints/auth.py"
Cohesion: 0.16
Nodes (25): accept_invitation(), accept_invitation_existing(), _check_origin(), _clear_auth_cookies(), _create_invitation(), create_organization(), create_organization_invitation(), create_platform_invitation() (+17 more)

### Community 11 - "OpenRouterLLMClient"
Cohesion: 0.10
Nodes (7): BaseLLMClient, LLMConfig, OpenRouterLLMClient, test_llm_client_configured_with_key(), test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises()

### Community 12 - "test_checkpoint.py"
Cohesion: 0.10
Nodes (11): _company_researcher(), company_researcher_mock(), _competitor_discovery(), competitor_discovery_mock(), research_planner(), _research_planner(), _build_graph(), _reset_db_each_test() (+3 more)

### Community 13 - "test_graph.py"
Cohesion: 0.11
Nodes (16): build_graph(), get_graph(), test_graph_execution_order_includes_company_researcher(), test_end_to_end_failure_handling_and_zero_false_success(), test_end_to_end_intelligence_pipeline_graph_execution(), _disable_live_llm(), _skip_persistence(), test_build_graph_produces_expected_nodes() (+8 more)

### Community 14 - "DatabaseManager"
Cohesion: 0.09
Nodes (5): DatabaseManager, DatabaseUnavailableError, test_base_declarative(), test_database_manager_starts_without_url(), test_session_factory_raises_when_unavailable()

### Community 15 - "test_agent_base.py"
Cohesion: 0.08
Nodes (20): BaseAgent, fetch_page(), _resolve_public_addresses(), retry_async(), validate_url_for_fetch(), DummyProvider, test_agent_budget_defaults(), test_base_agent_rate_limited_search_budget() (+12 more)

### Community 16 - "test_company_researcher_node.py"
Cohesion: 0.16
Nodes (7): disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_node_records_failure_safely(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm(), UnavailableLLMClient

### Community 17 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.09
Nodes (19): Combined coding workflow, graphify, Ponytail implementation discipline, 1. Create a virtual environment and install dependencies, 2. Configure environment, 3. (Optional) Initialize the database, 4. Run the server, 4. Verify (+11 more)

### Community 19 - "CompetitorProfile"
Cohesion: 0.06
Nodes (33): build_competitor_evidence(), classify_from_factors(), classify_from_score(), compute_text_overlap(), deduplicate_competitors(), _domain_of(), extract_keywords(), _normalize_name() (+25 more)

### Community 20 - "test_crypto_security.py"
Cohesion: 0.18
Nodes (10): encrypt_text(), _join_envelope(), _settings(), test_all_sensitive_orm_columns_use_encrypted_types(), test_checkpoint_adapter_rejects_plaintext_channel_values(), test_checkpoint_serializer_rejects_unencrypted_payloads(), test_checkpointer_defaults_to_encryption_and_encrypts_pending_writes(), test_key_rotation_reads_old_key_and_writes_with_active_key() (+2 more)

### Community 21 - "Organization"
Cohesion: 0.09
Nodes (23): Organization, AuthenticatedUser, OrganizationContext, Permission, require_permission(), authenticated_test_context(), current_user(), organization_context() (+15 more)

### Community 22 - "MockSearchProvider"
Cohesion: 0.15
Nodes (8): MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_query_creation(), test_search_query_priority_bounds()

### Community 23 - "typing"
Cohesion: 0.08
Nodes (7): upgrade(), upgrade(), upgrade(), upgrade(), get_logger(), database_health(), get_session()

### Community 24 - "agents/evidence_validator.py"
Cohesion: 0.16
Nodes (7): _availability_status(), _detect_claim_category(), _extract_numbers(), _extract_structured_quantities(), _has_negation(), _stem(), _tokens()

### Community 25 - "get_settings"
Cohesion: 0.07
Nodes (13): _encode_field(), _encrypt_column(), _encrypt_identity_email(), upgrade(), health(), get_settings(), get_sync_database_url(), configure_logging() (+5 more)

### Community 26 - "AsyncPostgresSaver"
Cohesion: 0.14
Nodes (6): AsyncPostgresSaver, decrypt_text(), commit(), test_checkpointer_encrypts_checkpoint_values_and_metadata_and_reads_them(), LangGraph checkpointing, Phase 1.5 — Integration Verification & Database Persistence (complete)

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.16
Nodes (8): disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_competitor_discovery(), test_node_records_failure_safely(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient

### Community 28 - "StrategicAnalystAgent"
Cohesion: 0.10
Nodes (9): StrategicAnalystAgent, _strategic_analyst(), CompetitivePositioning, CompetitorComparison, DimensionComparison, EvidenceGap, StrategicCompanyProfile, SWOTAnalysis (+1 more)

### Community 29 - "EvidenceValidatorAgent"
Cohesion: 0.10
Nodes (10): _detect_prompt_injection(), EvidenceValidatorAgent, _evidence_validator(), ClaimEvidenceMatch, ClaimValidationResult, ContradictionRecord, FreshnessAssessment, HumanReviewItem (+2 more)

### Community 30 - "SearchResult"
Cohesion: 0.18
Nodes (6): SearchResultCache, SearchResult, test_search_result_cache(), test_search_result_creation(), test_search_result_normalizes_domain(), test_search_result_rejects_empty_url()

### Community 31 - "Settings"
Cohesion: 0.12
Nodes (6): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default()

### Community 32 - "ResearchError"
Cohesion: 0.09
Nodes (12): acis_exception_handler(), ACISException, _error_payload(), LLMConfigurationError, NotFoundError, ResearchError, unhandled_exception_handler(), validation_exception_handler() (+4 more)

### Community 33 - "agents/strategic_analyst.py"
Cohesion: 0.11
Nodes (19): FeatureAvailability, InformationClass, StrategicAnalysisResult, StrategicImpact, StrategicPriority, ThreatLikelihood, ThreatSeverity, TimeHorizon (+11 more)

### Community 34 - "test_nodes.py"
Cohesion: 0.33
Nodes (14): _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_evidence_validator_real_node(), test_finalize_research_success_no_errors(), test_initialize_research() (+6 more)

### Community 35 - "test_company_researcher_agent.py"
Cohesion: 0.15
Nodes (8): FakeLLMClient, _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm(), test_agent_research_without_llm(), test_evidence_items_have_provenance(), UnavailableLLMClient

### Community 36 - "test_evidence_validator.py"
Cohesion: 0.09
Nodes (10): _canonical_domain(), _canonicalize_url(), _clean_snippet(), SourceCredibilityTier, agent(), test_credibility_assessment_across_tiers(), test_domain_canonicalization(), test_snippet_sanitization_strips_html_and_bounds_length() (+2 more)

### Community 37 - "ReportGeneratorAgent"
Cohesion: 0.11
Nodes (10): ReportGeneratorAgent, get_llm_client(), LLMMessage, ContradictionReportItem, EvidenceCitationItem, ExecutiveSummary, ReportMetadata, ResearchLimitationItem (+2 more)

### Community 38 - "test_end_to_end_pipeline.py"
Cohesion: 0.09
Nodes (8): _persist_report(), report_generator(), _report_generator(), ReportRepository, get_artifact_storage(), test_report_generator_node_execution_populates_state(), test_report_generator_requires_company_name(), test_report_generator_retry_idempotency()

### Community 39 - "ResearchState"
Cohesion: 0.13
Nodes (9): _report_generator(), report_generator_mock(), _strategic_analyst(), strategic_analyst_mock(), ResearchState, test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields() (+1 more)

### Community 40 - "CompanyProfile"
Cohesion: 0.17
Nodes (7): CompanyProfile, CompanySize, test_company_profile_full(), test_company_profile_minimal(), test_company_profile_rejects_bad_website(), test_company_size(), test_company_size_max_gte_min()

### Community 41 - "agents/report_generator.py"
Cohesion: 0.09
Nodes (15): ConfidentialityClassification, ReportFormat, StrategicReport, StrategicRecommendation, render_report_to_markdown(), render_report_to_pdf(), agent(), sample_state() (+7 more)

### Community 42 - "models/company.py"
Cohesion: 0.18
Nodes (3): EncryptedJSON, EncryptedText, test_orm_encrypted_types_hide_plaintext_and_reject_plaintext_storage()

### Community 44 - "test_persistence.py"
Cohesion: 0.21
Nodes (11): repo(), _rid(), session(), test_alembic_table_exists(), test_database_is_configured(), test_repository_create_and_get_by_id(), test_repository_get_by_id_wrong_organization_returns_none(), test_repository_list_by_organization() (+3 more)

### Community 45 - "ResearchRepository"
Cohesion: 0.16
Nodes (6): _persist_evidence_validation(), ResearchRepository, test_end_to_end_persistence_and_fresh_session_recovery(), session(), test_sqlite_encryption_failure_and_plaintext_rejection(), test_sqlite_research_company_competitor_and_evidence_round_trip()

### Community 46 - "test_sqlite_security.py"
Cohesion: 0.13
Nodes (25): _bootstrap_admin(), main(), OrganizationMembership, User, email_lookup_hash(), hash_password(), hash_refresh_token(), require_platform_admin() (+17 more)

### Community 47 - "EncryptedCheckpointSerializer"
Cohesion: 0.39
Nodes (3): EncryptedCheckpointSerializer, test_encrypted_text_and_checkpoint_payload_round_trip(), test_checkpoint_serializer_round_trips_langgraph_value_types()

### Community 49 - "LLMResponse"
Cohesion: 0.14
Nodes (4): LLMResponse, MockEndToEndLLMClient, FakeLLMClient, test_llm_response_structure()

### Community 50 - "Evidence"
Cohesion: 0.21
Nodes (6): Evidence, EvidenceCollection, test_evidence_collection(), test_evidence_confidence_clamped(), test_evidence_creation(), test_evidence_rejects_bad_url()

### Community 51 - "CompanyResearcherAgent"
Cohesion: 0.15
Nodes (4): CompanyResearcherAgent, _company_researcher(), disable_live_llm(), _skip_persistence()

### Community 52 - "AgentBudget"
Cohesion: 0.11
Nodes (4): AgentBudget, SearchProvider, test_search_provider_is_abstract(), Phase 2A — Real Company Research Agent (complete)

### Community 53 - "EndToEndMockSearchProvider"
Cohesion: 0.15
Nodes (4): _e2e_llm(), EndToEndMockSearchProvider, setup_e2e_environment(), _skip_persistence_mock()

### Community 54 - "sqlite_security_environment"
Cohesion: 0.22
Nodes (5): sqlite_client(), _sqlite_rate_limit(), sqlite_security_environment(), create_test_app(), override_db_session()

### Community 55 - "CompanyRepository"
Cohesion: 0.28
Nodes (3): _persist_company_research(), CompanyProfile, CompanyRepository

### Community 56 - "test_evidence_validator_node.py"
Cohesion: 0.13
Nodes (10): evidence_validator(), EvidenceClaim, EvidenceRepository, test_evidence_validator_cross_tenant_isolation_idor_protection(), test_evidence_validator_node_evaluates_evidence_and_produces_summary(), test_evidence_validator_node_requires_research_question(), test_evidence_validator_persists_full_validation_summary_and_human_review_queue(), test_evidence_validator_persists_to_sqlite() (+2 more)

### Community 59 - "security/auth.py"
Cohesion: 0.08
Nodes (21): get_db_session(), create_app(), request_security(), client_identity(), create_access_token(), decode_access_token(), enforce_rate_limit(), get_current_user() (+13 more)

### Community 60 - "LLMFactory"
Cohesion: 0.19
Nodes (5): LLMFactory, test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured(), test_llm_factory_is_lazy_until_client_requested(), LLM abstraction

### Community 61 - "test_api.py"
Cohesion: 0.36
Nodes (6): _client(), test_get_research_by_id(), test_get_research_not_found(), test_health_endpoint(), test_request_validation_rejects_invalid_input(), test_submit_research_returns_id_and_results()

### Community 76 - "test_report_generator_persists_to_sqlite_and_storage"
Cohesion: 0.11
Nodes (5): download_report_pdf_endpoint(), get_report_json_endpoint(), get_report_markdown_endpoint(), test_report_generator_persists_to_sqlite_and_storage(), test_report_generator_tenant_isolation()

### Community 78 - "test_persistence_company.py"
Cohesion: 0.27
Nodes (7): company_repo(), evidence_repo(), test_company_repository_create_and_get(), test_company_repository_org_isolation(), test_database_tables_exist(), test_evidence_repository_create_and_list(), test_evidence_repository_org_isolation()

### Community 79 - "company_researcher"
Cohesion: 0.08
Nodes (23): company_researcher(), competitor_discovery(), Agent Design — ACIS LangGraph Multi-Agent System (Phase 1 + 1.5 + 2A + 2B + 2E), Company Research Agent pipeline, Competitor Discovery Agent pipeline (Phase 2B), Design principles, Evidence Validation Agent pipeline (Phase 2E), Persistence and checkpointing (Phase 1.5 + 2A) (+15 more)

### Community 80 - "Development Roadmap"
Cohesion: 0.20
Nodes (10): Development Roadmap, Graphify installation and use, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2B — Competitor Discovery Agent, Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned) (+2 more)

### Community 84 - "MarketOpportunity"
Cohesion: 0.17
Nodes (4): format_time_horizon(), MarketOpportunity, SWOTItem, test_recommendation_timeline_consistency()

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 704 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `research_service.py`, `test_competitor_persistence.py`, `crypto.py`, `env.py`, `Research`, `endpoints/auth.py`, `test_checkpoint.py`, `DatabaseManager`, `CompetitorResearcherAgent`, `Organization`, `typing`, `agents/evidence_validator.py`, `StrategicAnalystAgent`, `EvidenceValidatorAgent`, `Settings`, `ResearchError`, `agents/strategic_analyst.py`, `test_company_researcher_agent.py`, `test_end_to_end_pipeline.py`, `agents/report_generator.py`, `test_persistence.py`, `test_sqlite_security.py`, `ArtifactStorageService`, `CompanyResearcherAgent`, `sqlite_security_environment`, `test_evidence_validator_node.py`, `security/auth.py`, `LLMFactory`, `test_persistence_company.py`, `company_researcher`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Are the 58 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 58 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `research_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06766917293233082 - nodes in this community are weakly interconnected._
- **Why does `ResearchState` connect `ResearchState` to `research_service.py`, `Research`, `run_node`, `test_checkpoint.py`, `test_graph.py`, `test_company_researcher_node.py`, `CompetitorResearcherAgent`, `test_crypto_security.py`, `typing`, `get_settings`, `test_competitor_discovery_node.py`, `StrategicAnalystAgent`, `EvidenceValidatorAgent`, `agents/strategic_analyst.py`, `test_nodes.py`, `test_end_to_end_pipeline.py`, `agents/report_generator.py`, `ResearchRepository`, `EncryptedCheckpointSerializer`, `CompanyResearcherAgent`, `test_evidence_validator_node.py`, `security/auth.py`, `test_report_generator_persists_to_sqlite_and_storage`, `company_researcher`, `Development Roadmap`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_competitor_persistence.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07541478129713423 - nodes in this community are weakly interconnected._