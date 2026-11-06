"""Markdown report generation service (Phase 2G).

Renders a complete, professional 14-section Competitive Intelligence Report
in standard GitHub-Flavored Markdown with tables, callouts, citations, and provenance.
"""

from typing import Any, Dict

from app.schemas.report import StrategicReport, format_time_horizon


def render_report_to_markdown(report: StrategicReport) -> str:
    """Render a StrategicReport into full professional Markdown."""
    meta = report.metadata
    lines: list[str] = []

    # -------------------------------------------------------------------------
    # Section 1: Cover Page / Header
    # -------------------------------------------------------------------------
    lines.append(f"# {meta.title}")
    lines.append("")
    lines.append(f"> **Confidentiality:** {meta.confidentiality}")
    lines.append(f"> **Target Company:** {meta.target_company}")
    lines.append(f"> **Report ID:** `{meta.report_id}` | **Research ID:** `{meta.research_id}`")
    lines.append(f"> **Generated:** {meta.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | **Version:** {meta.version}")
    lines.append(f"> **Overall Evidence Confidence:** {int(meta.overall_confidence * 100)}%")
    if meta.client_name:
        lines.append(f"> **Prepared For:** {meta.client_name}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("1. [Executive Summary](#1-executive-summary)")
    lines.append("2. [Research Scope and Methodology](#2-research-scope-and-methodology)")
    lines.append("3. [Target Company Intelligence Profile](#3-target-company-intelligence-profile)")
    lines.append("4. [Competitor Intelligence Profiles](#4-competitor-intelligence-profiles)")
    lines.append("5. [Competitive Comparison](#5-competitive-comparison)")
    lines.append("6. [Competitive Positioning](#6-competitive-positioning)")
    lines.append("7. [SWOT Analysis](#7-swot-analysis)")
    lines.append("8. [Market Opportunities](#8-market-opportunities)")
    lines.append("9. [Competitive Threat Assessment](#9-competitive-threat-assessment)")
    lines.append("10. [Strategic Recommendations](#10-strategic-recommendations)")
    lines.append("11. [Evidence and Source Appendix](#11-evidence-and-source-appendix)")
    lines.append("12. [Contradictions and Human Review](#12-contradictions-and-human-review)")
    lines.append("13. [Research Limitations](#13-research-limitations)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # -------------------------------------------------------------------------
    # Section 2: Executive Summary
    # -------------------------------------------------------------------------
    lines.append("## 1. Executive Summary")
    lines.append("")
    exec_sum = report.executive_summary
    if exec_sum.narrative:
        lines.append(exec_sum.narrative)
        lines.append("")
    else:
        lines.append(exec_sum.target_company_overview)
        lines.append("")

    lines.append("### Key Competitive Findings")
    for finding in exec_sum.main_competitive_findings:
        lines.append(f"- {finding}")
    lines.append("")

    lines.append("### Major Strategic Strengths & Limitations")
    for adv in exec_sum.major_advantages:
        lines.append(f"- **Advantage:** {adv}")
    for wk in exec_sum.major_weaknesses:
        lines.append(f"- **Limitation:** {wk}")
    lines.append("")

    lines.append("### Top Strategic Recommendations")
    for rec in exec_sum.top_recommendations:
        lines.append(f"1. {rec}")
    lines.append("")

    # -------------------------------------------------------------------------
    # Section 3: Research Scope and Methodology
    # -------------------------------------------------------------------------
    lines.append("## 2. Research Scope and Methodology")
    lines.append("")
    scope = report.research_scope
    lines.append(f"**Research Objectives:** {scope.research_objectives}")
    lines.append("")
    lines.append(f"**Competitors Evaluated:** {', '.join(scope.competitors_examined) if scope.competitors_examined else 'None qualified'}")
    lines.append("")
    lines.append(f"**Collection Methodology:** {scope.collection_methodology}")
    lines.append("")
    lines.append(f"**Validation Methodology:** {scope.validation_methodology}")
    lines.append("")
    lines.append(f"**Confidence Scoring:** {scope.confidence_scoring_methodology}")
    lines.append("")

    # -------------------------------------------------------------------------
    # Section 4: Target Company Intelligence Profile
    # -------------------------------------------------------------------------
    lines.append("## 3. Target Company Intelligence Profile")
    lines.append("")
    tcp = report.target_company_profile
    lines.append(f"- **Company Name:** {tcp.company_name}")
    lines.append(f"- **Business Model:** {tcp.core_business_model or 'Not publicly disclosed'}")
    lines.append(f"- **Pricing Strategy:** {tcp.pricing_strategy or 'Undocumented in public sources'}")
    lines.append(f"- **Core Products:** {', '.join(tcp.main_products_and_services) if tcp.main_products_and_services else 'None documented'}")
    lines.append(f"- **Target Customer Segments:** {', '.join(tcp.target_customer_segments) if tcp.target_customer_segments else 'General market'}")
    lines.append(f"- **Geographic Footprint:** {', '.join(tcp.geographic_positioning) if tcp.geographic_positioning else 'Undocumented'}")
    lines.append(f"- **Information Classification:** `{tcp.information_class.value}` (Confidence: {int(tcp.confidence * 100)}%)")
    lines.append("")
    if tcp.known_limitations:
        lines.append("#### Documented Limitations")
        for lim in tcp.known_limitations:
            lines.append(f"- {lim}")
        lines.append("")

    # -------------------------------------------------------------------------
    # Section 5: Competitor Intelligence Profiles
    # -------------------------------------------------------------------------
    lines.append("## 4. Competitor Intelligence Profiles")
    lines.append("")
    if not report.competitor_profiles:
        lines.append("_No qualifying competitor profiles available in research scope._")
        lines.append("")
    else:
        for comp in report.competitor_profiles:
            c_name = comp.get("company_name", "Competitor")
            c_type = comp.get("competitor_type", "direct")
            if isinstance(c_type, dict):
                c_type = c_type.get("value", "direct")
            prods = comp.get("products_and_services") or []
            custs = comp.get("target_customers") or []
            geos = comp.get("geographic_markets") or []
            strengths = comp.get("competitive_strengths") or []
            weaknesses = comp.get("competitive_weaknesses") or []

            lines.append(f"### {c_name} (`{c_type.upper()}`)")
            lines.append(f"- **Overview:** {comp.get('company_description') or 'Documented commercial entity.'}")
            lines.append(f"- **Products & Services:** {', '.join(prods) if prods else 'Unobserved in public search'}")
            lines.append(f"- **Target Segments:** {', '.join(custs) if custs else 'General enterprise'}")
            lines.append(f"- **Geographic Coverage:** {', '.join(geos) if geos else 'Undocumented'}")
            lines.append(f"- **Observed Strengths:** {', '.join(strengths) if strengths else 'Standard commercial capabilities'}")
            lines.append(f"- **Observed Limitations:** {', '.join(weaknesses) if weaknesses else 'Limited public disclosures'}")
            lines.append("")

    # -------------------------------------------------------------------------
    # Section 6: Competitive Comparison
    # -------------------------------------------------------------------------
    lines.append("## 5. Competitive Comparison")
    lines.append("")
    if not report.competitive_comparison:
        lines.append("_No multi-dimensional comparisons available._")
        lines.append("")
    else:
        for ccomp in report.competitive_comparison:
            lines.append(f"### Comparison: {meta.target_company} vs. {ccomp.competitor_name}")
            lines.append("")
            lines.append("| Dimension | Target Company | Competitor | Capability Status | Confidence |")
            lines.append("| :--- | :--- | :--- | :---: | :---: |")
            for dim in ccomp.comparison_dimensions:
                d_name = dim.dimension.replace("_", " ").title()
                t_val = (dim.target_company_value or "Unknown").replace("|", "/")
                c_val = (dim.competitor_value or "Unknown").replace("|", "/")
                status = dim.availability_status.value
                conf = f"{int(dim.confidence * 100)}%"
                lines.append(f"| {d_name} | {t_val} | {c_val} | `{status}` | {conf} |")
            lines.append("")
            if ccomp.differentiation_summary:
                lines.append(f"**Differentiation Synthesis:** {ccomp.differentiation_summary}")
                lines.append("")

    # -------------------------------------------------------------------------
    # Section 7: Competitive Positioning
    # -------------------------------------------------------------------------
    lines.append("## 6. Competitive Positioning")
    lines.append("")
    pos = report.competitive_positioning
    lines.append(f"- **Direct Competitors:** {', '.join(pos.direct_competitors) if pos.direct_competitors else 'None identified'}")
    lines.append(f"- **Indirect Competitors:** {', '.join(pos.indirect_competitors) if pos.indirect_competitors else 'None identified'}")
    lines.append(f"- **Potential Substitutes:** {', '.join(pos.potential_substitutes) if pos.potential_substitutes else 'None identified'}")
    lines.append("")
    lines.append("### Strategic Advantages & Vulnerabilities")
    for adv in pos.strategic_advantages:
        lines.append(f"- **Advantage:** {adv}")
    for vuln in pos.competitive_vulnerabilities:
        lines.append(f"- **Vulnerability:** {vuln}")
    lines.append("")

    # -------------------------------------------------------------------------
    # Section 8: SWOT Analysis
    # -------------------------------------------------------------------------
    lines.append("## 7. SWOT Analysis")
    lines.append("")
    swot = report.swot_analysis
    lines.append(f"_{swot.overall_summary}_")
    lines.append("")

    lines.append("### Strengths (Internal Advantages)")
    for s in swot.strengths:
        c_pct = int(s.confidence_score * 100)
        ev_str = f" [Evidence: {', '.join(s.supporting_evidence_ids)}]" if s.supporting_evidence_ids else ""
        lines.append(f"- **{s.title}** (`Impact: {s.strategic_impact.value.upper()}`, `Confidence: {c_pct}%`){ev_str}")
        lines.append(f"  {s.description} — _{s.explanation}_")
    lines.append("")

    lines.append("### Weaknesses (Internal Limitations)")
    for w in swot.weaknesses:
        c_pct = int(w.confidence_score * 100)
        lines.append(f"- **{w.title}** (`Impact: {w.strategic_impact.value.upper()}`, `Confidence: {c_pct}%`)")
        lines.append(f"  {w.description} — _{w.explanation}_")
    lines.append("")

    lines.append("### Opportunities (External Openings)")
    for o in swot.opportunities:
        c_pct = int(o.confidence_score * 100)
        lines.append(f"- **{o.title}** (`Impact: {o.strategic_impact.value.upper()}`, `Confidence: {c_pct}%`)")
        lines.append(f"  {o.description} — _{o.explanation}_")
    lines.append("")

    lines.append("### Threats (External Market Risks)")
    for t in swot.threats:
        c_pct = int(t.confidence_score * 100)
        lines.append(f"- **{t.title}** (`Impact: {t.strategic_impact.value.upper()}`, `Confidence: {c_pct}%`)")
        lines.append(f"  {t.description} — _{t.explanation}_")
    lines.append("")

    # -------------------------------------------------------------------------
    # Section 9: Market Opportunities
    # -------------------------------------------------------------------------
    lines.append("## 8. Market Opportunities")
    lines.append("")
    for opp in report.market_opportunities:
        lines.append(f"### {opp.title}")
        lines.append(f"- **Market Need:** {opp.market_or_customer_need}")
        lines.append(f"- **Rationale:** {opp.opportunity_rationale}")
        lines.append(f"- **Business Impact:** {opp.potential_business_impact}")
        lines.append(f"- **Complexity:** `{opp.implementation_complexity.value}` | **Horizon:** {format_time_horizon(opp.time_horizon)}")
        lines.append(f"- **Confidence:** {int(opp.confidence * 100)}% | **Class:** `{opp.information_class.value}`")
        lines.append("")

    # -------------------------------------------------------------------------
    # Section 10: Competitive Threat Assessment
    # -------------------------------------------------------------------------
    lines.append("## 9. Competitive Threat Assessment")
    lines.append("")
    for thr in report.threat_assessment:
        lines.append(f"### {thr.title}")
        lines.append(f"- **Description:** {thr.description}")
        lines.append(f"- **Severity:** `{thr.severity.value.upper()}` | **Likelihood:** `{thr.likelihood.value.upper()}`")
        lines.append(f"- **Impact Assessment:** {thr.impact}")
        if thr.risks_and_mitigations:
            lines.append(f"- **Actionable Mitigations:** {'; '.join(thr.risks_and_mitigations)}")
        lines.append(f"- **Confidence:** {int(thr.confidence * 100)}% | **Class:** `{thr.information_class.value}`")
        lines.append("")

    # -------------------------------------------------------------------------
    # Section 11: Strategic Recommendations
    # -------------------------------------------------------------------------
    lines.append("## 10. Strategic Recommendations")
    lines.append("")
    for rec in report.strategic_recommendations:
        lines.append(f"### [{rec.priority.value.upper()}] {rec.title}")
        lines.append(f"- **Objective:** {rec.strategic_objective}")
        lines.append(f"- **Analysis:** {rec.supporting_analysis}")
        lines.append(f"- **Expected Business Impact:** {rec.expected_business_impact}")
        lines.append(f"- **Difficulty:** `{rec.implementation_difficulty.value}` | **Time Horizon:** {format_time_horizon(rec.time_horizon)}")
        lines.append(f"- **Success Metrics:** {', '.join(rec.success_metrics)}")
        if rec.risks:
            lines.append(f"- **Risks:** {', '.join(rec.risks)}")
        lines.append(f"- **Confidence:** {int(rec.confidence_score * 100)}%")
        lines.append("")

    # -------------------------------------------------------------------------
    # Section 12: Evidence and Source Appendix
    # -------------------------------------------------------------------------
    lines.append("## 11. Evidence and Source Appendix")
    lines.append("")
    if not report.evidence_appendix:
        lines.append("_No empirical evidence items available._")
        lines.append("")
    else:
        lines.append("| Evidence ID | Claim | Source | Status | Confidence |")
        lines.append("| :--- | :--- | :--- | :---: | :---: |")
        for ev in report.evidence_appendix:
            e_id = f"`{ev.evidence_id}`"
            claim = ev.claim.replace("|", "/")
            url = f"[{ev.source_domain}]({ev.source_url})" if ev.source_url else ev.source_domain
            stat = f"`{ev.verification_status}`"
            conf = f"{int(ev.confidence_score * 100)}%"
            lines.append(f"| {e_id} | {claim} | {url} | {stat} | {conf} |")
        lines.append("")

    # -------------------------------------------------------------------------
    # Section 13: Contradictions and Human Review
    # -------------------------------------------------------------------------
    lines.append("## 12. Contradictions and Human Review")
    lines.append("")
    if not report.contradictions_and_review:
        lines.append("No active unresolvable contradictions detected in empirical intelligence corpus.")
        lines.append("")
    else:
        for contra in report.contradictions_and_review:
            lines.append(f"### Contradiction: {contra.topic} (`Severity: {contra.severity.upper()}`)")
            lines.append(f"- **Claim A:** \"{contra.claim_a}\" ([Source]({contra.source_url_a}))")
            lines.append(f"- **Claim B:** \"{contra.claim_b}\" ([Source]({contra.source_url_b}))")
            lines.append(f"- **Analysis:** {contra.explanation}")
            lines.append(f"- **Required Action:** {contra.required_action}")
            lines.append("")

    # -------------------------------------------------------------------------
    # Section 14: Research Limitations
    # -------------------------------------------------------------------------
    lines.append("## 13. Research Limitations")
    lines.append("")
    for lim in report.research_limitations:
        lines.append(f"- **{lim.topic}:** {lim.description}")
        lines.append(f"  _Impact on Analysis:_ {lim.impact}")
        lines.append(f"  _Remediation:_ {lim.remediation_recommendation}")
    lines.append("")

    return "\n".join(lines)


__all__ = ["render_report_to_markdown"]
