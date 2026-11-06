# Graph Report - ai-competitive-intelligence  (2026-11-06)

## Corpus Check
- 146 files · ~73,566 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 3, .ini 2, .example 1)

## Summary
- 1829 nodes · 5089 edges · 86 communities (61 shown, 25 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 706 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f111b1aa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- research_service.py
- asyncio
- CompetitorRepository
- crypto.py
- agents/company_researcher.py
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
- test_agent_base.py
- company_researcher
- AI Competitive Intelligence System (ACIS)
- CompetitorResearcherAgent
- test_competitor_intelligence.py
- test_crypto_security.py
- pytest
- typing
- logging.py
- CompetitorProfile
- main.py
- AsyncPostgresSaver
- test_competitor_discovery_node.py
- StrategicAnalystAgent
- agents/evidence_validator.py
- SearchResult
- config.py
- exceptions.py
- agents/strategic_analyst.py
- test_nodes.py
- deduplicate_competitors
- test_evidence_validator.py
- agents/report_generator.py
- test_report_generator_node.py
- ResearchState
- 0005_encrypt_sensitive_payloads.py
- test_report_generator.py
- EncryptedText
- DuckDuckGoProvider
- schemas/competitor.py
- ResearchRepository
- test_auth_and_tenant_isolation.py
- EncryptedCheckpointSerializer
- ResearchError
- VerificationStatus
- CompanyResearcherAgent
- competitor_researcher.py
- sqlalchemy
- CompanyRepository
- test_evidence_validator_node.py
- compilerOptions
- next.config.js
- security/auth.py
- LLMConfig
- Research
- SourceCredibilityAssessment
- EvidenceRepository
- test_competitor_persistence.py
- reports.py
- CompetitorEvidenceRepository
- test_persistence_company.py
- Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B + Phase 2E
- Development Roadmap
- llm.py
- NumberedCanvas
- SWOTItem

## God Nodes (most connected - your core abstractions)
1. `ResearchState` - 105 edges
2. `get_settings()` - 73 edges
3. `SearchResult` - 50 edges
4. `StrategicAnalystAgent` - 48 edges
5. `CompetitorResearcherAgent` - 46 edges
6. `ResearchError` - 43 edges
7. `run_node()` - 39 edges
8. `MockSearchProvider` - 39 edges
9. `Research` - 38 edges
10. `SearchQuery` - 37 edges

## Surprising Connections (you probably didn't know these)
- `Company Research Agent pipeline (Phase 2A)` --references--> `company_researcher()`  [INFERRED]
  docs/architecture.md → backend/app/graph/nodes/company_researcher.py
- `Phase 2B — Competitor Discovery Agent` --references--> `competitor_discovery_mock()`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/nodes/competitor_discovery_mock.py
- `Design principles` --references--> `ResearchState`  [INFERRED]
  docs/agent-design.md → backend/app/graph/state.py
- `Phase 0 + Phase 1 (complete)` --references--> `ResearchState`  [INFERRED]
  docs/development-roadmap.md → backend/app/graph/state.py
- `Phase 1.5 — Integration Verification & Database Persistence (complete)` --references--> `commit()`  [INFERRED]
  docs/development-roadmap.md → backend/tests/unit/test_auth_security.py

## Import Cycles
- None detected.

## Communities (86 total, 25 thin omitted)

### Community 0 - "research_service.py"
Cohesion: 0.07
Nodes (26): NodeExecutionMetadata, ResearchRequest, ResearchResponse, ResearchResult, ResearchStatusResponse, _fetch_from_db(), _get_repository(), get_research() (+18 more)

### Community 1 - "asyncio"
Cohesion: 0.06
Nodes (30): CompanyProfile, CompanySize, FakeLLMClient, _make_agent(), test_agent_budget_limits_searches(), test_agent_rejects_empty_company_name(), test_agent_research_with_llm(), test_agent_research_without_llm() (+22 more)

### Community 2 - "CompetitorRepository"
Cohesion: 0.17
Nodes (4): Competitor, _company_key(), CompetitorRepository, _website_key()

### Community 3 - "crypto.py"
Cohesion: 0.17
Nodes (5): decrypt_bytes(), encrypt_bytes(), EncryptionConfigurationError, _keyring(), pytest_configure()

### Community 4 - "agents/company_researcher.py"
Cohesion: 0.12
Nodes (12): build_evidence_from_result(), classify_evidence_type(), detect_conflicts(), _domain_of(), _is_trusted_domain(), score_confidence(), EvidenceType, _make_result() (+4 more)

### Community 5 - "test_evidence_validator_adversarial.py"
Cohesion: 0.04
Nodes (23): _root_domain(), LLMResponse, agent(), test_adversarial_prompt_injection_attempts_neutralized(), test_business_model_contradiction(), test_confidence_scores_strictly_bounded_between_zero_and_one(), test_contradiction_detection_preserves_both_sides(), test_contradictory_product_availability() (+15 more)

### Community 6 - "page.js"
Cohesion: 0.06
Nodes (66): metadata, RootLayout(), Home(), handleLogin(), handleLogout(), handleOrganizationChange(), restoreSession(), ReportDisplay() (+58 more)

### Community 7 - "test_sqlite_security.py"
Cohesion: 0.08
Nodes (21): get_url(), run_migrations_offline(), run_migrations_online(), Base, get_db_session(), get_sync_database_url(), AuditEvent, AuthSession (+13 more)

### Community 8 - "test_strategic_analyst_node.py"
Cohesion: 0.11
Nodes (9): _persist_strategic_analysis(), strategic_analyst(), _strategic_analyst(), StrategyRepository, test_strategic_analyst_node_executes_and_populates_state(), test_strategic_analyst_node_requires_company_name(), test_strategic_analyst_persists_to_sqlite(), test_strategic_analyst_retry_idempotency() (+1 more)

### Community 9 - "agents/base.py"
Cohesion: 0.22
Nodes (4): _resolve_public_addresses(), validate_url_for_fetch(), test_validate_url_for_fetch_allows_public(), test_validate_url_for_fetch_blocks_private()

### Community 10 - "get_settings"
Cohesion: 0.14
Nodes (24): _check_origin(), _clear_auth_cookies(), _create_invitation(), create_organization(), create_organization_invitation(), create_platform_invitation(), _create_session(), list_user_organizations() (+16 more)

### Community 11 - "LLMConfigurationError"
Cohesion: 0.12
Nodes (8): LLMConfigurationError, BaseLLMClient, OpenRouterLLMClient, test_llm_client_configured_with_key(), test_llm_client_malformed_json(), run(), test_llm_client_not_configured_raises(), test_llm_response_structure()

### Community 12 - "run_node"
Cohesion: 0.07
Nodes (25): make_metadata(), run_node(), utc_now_iso(), _company_researcher(), company_researcher_mock(), _evidence_validator(), evidence_validator_mock(), finalize_research() (+17 more)

### Community 13 - "test_graph.py"
Cohesion: 0.14
Nodes (14): build_graph(), get_graph(), test_graph_execution_order_includes_competitor_discovery(), _disable_live_llm(), _skip_persistence(), test_build_graph_produces_expected_nodes(), test_competitor_and_search_results_are_checkpointed(), test_full_graph_execution_all_nodes_completed() (+6 more)

### Community 14 - "DatabaseManager"
Cohesion: 0.08
Nodes (4): DatabaseManager, test_base_declarative(), test_database_manager_starts_without_url(), test_session_factory_raises_when_unavailable()

### Community 15 - "test_agent_base.py"
Cohesion: 0.11
Nodes (15): BaseAgent, fetch_page(), retry_async(), DummyProvider, test_base_agent_rate_limited_search_budget(), test_base_agent_search_cache(), test_fetch_page_blocks_private_url(), test_fetch_page_does_not_use_ip_literal_as_tls_sni() (+7 more)

### Community 16 - "company_researcher"
Cohesion: 0.09
Nodes (18): company_researcher(), disable_live_llm(), _run_graph_with_mock_agent(), _skip_persistence(), test_graph_execution_order_includes_company_researcher(), test_node_records_failure_safely(), test_node_returns_dict_with_profile_and_evidence(), _unavailable_llm() (+10 more)

### Community 17 - "AI Competitive Intelligence System (ACIS)"
Cohesion: 0.09
Nodes (19): Combined coding workflow, graphify, Ponytail implementation discipline, 1. Create a virtual environment and install dependencies, 2. Configure environment, 3. (Optional) Initialize the database, 4. Run the server, 4. Verify (+11 more)

### Community 19 - "test_competitor_intelligence.py"
Cohesion: 0.11
Nodes (17): build_competitor_evidence(), classify_from_factors(), classify_from_score(), compute_text_overlap(), extract_keywords(), score_qualification(), QualificationFactor, test_classifies_all_competitor_types_from_overlap_evidence() (+9 more)

### Community 20 - "test_crypto_security.py"
Cohesion: 0.16
Nodes (13): decrypt_text(), _join_envelope(), _settings(), _split_envelope(), test_aes_gcm_uses_unique_12_byte_nonces_and_round_trips(), test_all_sensitive_orm_columns_use_encrypted_types(), test_checkpoint_adapter_rejects_plaintext_channel_values(), test_checkpoint_serializer_rejects_unencrypted_payloads() (+5 more)

### Community 21 - "pytest"
Cohesion: 0.11
Nodes (13): _client(), test_get_research_by_id(), test_get_research_not_found(), test_health_endpoint(), test_request_validation_rejects_invalid_input(), test_submit_research_returns_id_and_results(), test_cross_organization_isolation_at_api(), test_get_research_not_found() (+5 more)

### Community 22 - "typing"
Cohesion: 0.12
Nodes (8): SearchProvider, MockSearchProvider, SearchQuery, test_mock_search_provider_counts_calls(), test_mock_search_provider_is_deterministic(), test_mock_search_provider_returns_canned_results(), test_mock_search_provider_unknown_query_placeholder(), test_search_provider_is_abstract()

### Community 23 - "logging.py"
Cohesion: 0.10
Nodes (5): configure_logging(), get_logger(), _MaskingFormatter, database_health(), get_session()

### Community 24 - "CompetitorProfile"
Cohesion: 0.14
Nodes (10): CompetitorCollection, CompetitorEvidenceItem, CompetitorProfile, test_competitor_collection(), test_competitor_evidence_requires_a_valid_http_source(), test_competitor_profile_full(), test_competitor_profile_minimal(), test_competitor_profile_rejects_bad_type() (+2 more)

### Community 25 - "main.py"
Cohesion: 0.07
Nodes (14): health(), create_app(), request_security(), lifespan(), root(), client_identity(), enforce_rate_limit(), get_current_user() (+6 more)

### Community 26 - "AsyncPostgresSaver"
Cohesion: 0.15
Nodes (4): AsyncPostgresSaver, test_checkpointer_encrypts_checkpoint_values_and_metadata_and_reads_them(), Persistence and checkpointing (Phase 1.5 + 2A), LangGraph checkpointing

### Community 27 - "test_competitor_discovery_node.py"
Cohesion: 0.13
Nodes (9): competitor_discovery(), disable_live_llm(), _run_node_with_mock_agent(), _skip_persistence(), test_node_records_failure_safely(), test_node_returns_dict_with_competitors_and_metadata(), _unavailable_llm(), UnavailableLLMClient (+1 more)

### Community 28 - "StrategicAnalystAgent"
Cohesion: 0.11
Nodes (7): StrategicAnalystAgent, CompetitivePositioning, CompetitorComparison, DimensionComparison, EvidenceGap, StrategicCompanyProfile, SWOTAnalysis

### Community 29 - "agents/evidence_validator.py"
Cohesion: 0.07
Nodes (17): _availability_status(), _clean_snippet(), _detect_claim_category(), _detect_prompt_injection(), EvidenceValidatorAgent, _extract_numbers(), _extract_structured_quantities(), _has_negation() (+9 more)

### Community 30 - "SearchResult"
Cohesion: 0.14
Nodes (8): SearchResultCache, SearchResult, test_search_result_cache(), test_search_query_creation(), test_search_query_priority_bounds(), test_search_result_creation(), test_search_result_normalizes_domain(), test_search_result_rejects_empty_url()

### Community 31 - "config.py"
Cohesion: 0.07
Nodes (17): get_settings_uncached(), Settings, test_cors_origin_list_unchanged(), test_cors_origin_string_parsing(), test_settings_defaults(), test_settings_not_configured_by_default(), repo(), _rid() (+9 more)

### Community 32 - "exceptions.py"
Cohesion: 0.16
Nodes (10): acis_exception_handler(), ACISException, DatabaseUnavailableError, _error_payload(), NotFoundError, unhandled_exception_handler(), validation_exception_handler(), ValidationError (+2 more)

### Community 33 - "agents/strategic_analyst.py"
Cohesion: 0.10
Nodes (20): FeatureAvailability, InformationClass, StrategicAnalysisResult, StrategicImpact, StrategicPriority, ThreatLikelihood, ThreatSeverity, TimeHorizon (+12 more)

### Community 34 - "test_nodes.py"
Cohesion: 0.22
Nodes (16): _competitor_discovery(), competitor_discovery_mock(), _base_state(), _run(), test_company_researcher_mock(), test_competitor_discovery_mock(), test_evidence_validator_mock(), test_evidence_validator_real_node() (+8 more)

### Community 35 - "deduplicate_competitors"
Cohesion: 0.25
Nodes (5): deduplicate_competitors(), _domain_of(), _normalize_name(), test_deduplicate_competitors_by_domain(), test_deduplicate_competitors_by_name()

### Community 36 - "test_evidence_validator.py"
Cohesion: 0.10
Nodes (8): _canonical_domain(), _canonicalize_url(), SourceCredibilityTier, agent(), test_credibility_assessment_across_tiers(), test_domain_canonicalization(), test_url_canonicalization_strips_tracking_params_and_lowercases(), test_validate_state_generates_human_review_queue_and_summary()

### Community 37 - "agents/report_generator.py"
Cohesion: 0.11
Nodes (12): ReportGeneratorAgent, ConfidentialityClassification, ContradictionReportItem, EvidenceCitationItem, ExecutiveSummary, ReportFormat, ReportMetadata, ResearchLimitationItem (+4 more)

### Community 38 - "test_report_generator_node.py"
Cohesion: 0.11
Nodes (9): _persist_report(), report_generator(), _report_generator(), ReportRepository, test_report_generator_node_execution_populates_state(), test_report_generator_persists_to_sqlite_and_storage(), test_report_generator_requires_company_name(), test_report_generator_retry_idempotency() (+1 more)

### Community 39 - "ResearchState"
Cohesion: 0.18
Nodes (5): ResearchState, test_graph_failure_does_not_expose_exception_content(), test_state_add_node_metadata_and_error(), test_state_rejects_extra_fields(), test_state_required_fields()

### Community 40 - "0005_encrypt_sensitive_payloads.py"
Cohesion: 0.25
Nodes (8): _encode_field(), _encrypt_column(), _encrypt_existing_checkpoints(), _encrypt_identity_email(), upgrade(), encrypt_checkpoint_payload(), encrypt_text(), validate_encryption_configuration()

### Community 41 - "test_report_generator.py"
Cohesion: 0.10
Nodes (12): StrategicReport, render_report_to_markdown(), render_report_to_pdf(), agent(), sample_state(), test_citation_validation_against_corpus(), test_generate_report_14_sections(), test_json_serialization_roundtrip() (+4 more)

### Community 42 - "EncryptedText"
Cohesion: 0.24
Nodes (3): EncryptedJSON, EncryptedText, test_orm_encrypted_types_hide_plaintext_and_reject_plaintext_storage()

### Community 43 - "DuckDuckGoProvider"
Cohesion: 0.24
Nodes (3): _build_search_provider(), DuckDuckGoProvider, _is_private_or_internal()

### Community 45 - "ResearchRepository"
Cohesion: 0.17
Nodes (5): _persist_evidence_validation(), ResearchRepository, session(), test_sqlite_encryption_failure_and_plaintext_rejection(), test_sqlite_research_company_competitor_and_evidence_round_trip()

### Community 46 - "test_auth_and_tenant_isolation.py"
Cohesion: 0.18
Nodes (19): accept_invitation(), accept_invitation_existing(), _bootstrap_admin(), main(), OrganizationInvitation, OrganizationMembership, User, email_lookup_hash() (+11 more)

### Community 47 - "EncryptedCheckpointSerializer"
Cohesion: 0.39
Nodes (3): EncryptedCheckpointSerializer, test_encrypted_text_and_checkpoint_payload_round_trip(), test_checkpoint_serializer_round_trips_langgraph_value_types()

### Community 48 - "ResearchError"
Cohesion: 0.13
Nodes (3): ResearchError, ArtifactStorageService, get_artifact_storage()

### Community 50 - "VerificationStatus"
Cohesion: 0.16
Nodes (9): Evidence, EvidenceCollection, VerificationStatus, test_evidence_collection(), test_evidence_confidence_clamped(), test_evidence_creation(), test_evidence_rejects_bad_url(), Modules (+1 more)

### Community 51 - "CompanyResearcherAgent"
Cohesion: 0.15
Nodes (3): CompanyResearcherAgent, _build_search_provider(), _company_researcher()

### Community 54 - "sqlalchemy"
Cohesion: 0.21
Nodes (4): upgrade(), upgrade(), upgrade(), upgrade()

### Community 55 - "CompanyRepository"
Cohesion: 0.20
Nodes (3): _persist_company_research(), CompanyProfile, CompanyRepository

### Community 56 - "test_evidence_validator_node.py"
Cohesion: 0.18
Nodes (7): evidence_validator(), _evidence_validator(), test_evidence_validator_cross_tenant_isolation_idor_protection(), test_evidence_validator_node_evaluates_evidence_and_produces_summary(), test_evidence_validator_node_requires_research_question(), test_evidence_validator_persists_full_validation_summary_and_human_review_queue(), test_evidence_validator_retry_idempotency()

### Community 59 - "security/auth.py"
Cohesion: 0.08
Nodes (29): get_research_endpoint(), submit_research(), AuthenticatedUser, decode_access_token(), get_organization_context(), OrganizationContext, Permission, require_permission() (+21 more)

### Community 60 - "LLMConfig"
Cohesion: 0.13
Nodes (7): LLMConfig, LLMFactory, test_complete_without_api_key_raises_clear_error(), test_create_client_is_openrouter_compatible(), test_llm_config_from_env_without_key_not_configured(), test_llm_factory_is_lazy_until_client_requested(), LLM abstraction

### Community 74 - "EvidenceRepository"
Cohesion: 0.27
Nodes (3): EvidenceClaim, EvidenceRepository, test_evidence_validator_persists_to_sqlite()

### Community 75 - "test_competitor_persistence.py"
Cohesion: 0.21
Nodes (10): competitor_repo(), evidence_repo(), session(), test_competitor_duplicate_prevention(), test_competitor_evidence_org_isolation(), test_competitor_evidence_repository(), test_competitor_lookup_is_scoped_by_research_and_organization(), test_competitor_repository_create_and_get() (+2 more)

### Community 76 - "reports.py"
Cohesion: 0.18
Nodes (3): download_report_pdf_endpoint(), get_report_json_endpoint(), get_report_markdown_endpoint()

### Community 77 - "CompetitorEvidenceRepository"
Cohesion: 0.31
Nodes (3): _persist_competitor_discovery(), CompetitorEvidence, CompetitorEvidenceRepository

### Community 78 - "test_persistence_company.py"
Cohesion: 0.27
Nodes (7): company_repo(), evidence_repo(), test_company_repository_create_and_get(), test_company_repository_org_isolation(), test_database_tables_exist(), test_evidence_repository_create_and_list(), test_evidence_repository_org_isolation()

### Community 79 - "Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B + Phase 2E"
Cohesion: 0.18
Nodes (10): Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B + Phase 2E, Company Research Agent pipeline (Phase 2A), Database degradation, Frontend, High-level data flow, Overview, Persistent storage: company profiles and evidence, Persistent storage (`researches` table) (+2 more)

### Community 80 - "Development Roadmap"
Cohesion: 0.20
Nodes (10): Development Roadmap, Graphify installation and use, Immediate next steps to run locally, Phase 0 + Phase 1 (complete), Phase 2 (planned), Phase 2B — Competitor Discovery Agent, Phase 2C - Codebase knowledge and development workflow, Phase 3 (planned) (+2 more)

## Knowledge Gaps
- **6 isolated node(s):** `react-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `eslint` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 690 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `research_service.py`, `asyncio`, `crypto.py`, `agents/company_researcher.py`, `test_sqlite_security.py`, `test_strategic_analyst_node.py`, `agents/base.py`, `run_node`, `DatabaseManager`, `company_researcher`, `CompetitorResearcherAgent`, `pytest`, `logging.py`, `main.py`, `test_competitor_discovery_node.py`, `agents/evidence_validator.py`, `config.py`, `agents/strategic_analyst.py`, `agents/report_generator.py`, `test_report_generator_node.py`, `0005_encrypt_sensitive_payloads.py`, `DuckDuckGoProvider`, `test_auth_and_tenant_isolation.py`, `ResearchError`, `CompanyResearcherAgent`, `competitor_researcher.py`, `test_evidence_validator_node.py`, `security/auth.py`, `LLMConfig`, `test_competitor_persistence.py`, `test_persistence_company.py`, `llm.py`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `ResearchState` (e.g. with `build_graph()` and `run_node()`) actually correct?**
  _`ResearchState` has 55 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `tailwindcss`, `postcss` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `research_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07088989441930618 - nodes in this community are weakly interconnected._
- **Why does `ResearchState` connect `ResearchState` to `research_service.py`, `test_strategic_analyst_node.py`, `run_node`, `test_graph.py`, `company_researcher`, `CompetitorResearcherAgent`, `test_crypto_security.py`, `logging.py`, `test_competitor_discovery_node.py`, `agents/strategic_analyst.py`, `test_nodes.py`, `test_report_generator_node.py`, `test_report_generator.py`, `EncryptedCheckpointSerializer`, `VerificationStatus`, `CompanyResearcherAgent`, `competitor_researcher.py`, `test_evidence_validator_node.py`, `security/auth.py`, `EvidenceRepository`, `Development Roadmap`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `SearchResult` (e.g. with `BaseAgent` and `SearchResultCache`) actually correct?**
  _`SearchResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `asyncio` be split into smaller, more focused modules?**
  _Cohesion score 0.0553116769095698 - nodes in this community are weakly interconnected._