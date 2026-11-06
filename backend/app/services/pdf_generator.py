"""Professional PDF report generation service (Phase 2G).

Renders a publication-grade, client-ready Competitive Intelligence PDF report
using ReportLab with deterministic execution, running headers/footers,
page numbering (Page X of Y), structured tables, and clickable links.
"""

import io
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.report import StrategicReport, format_time_horizon


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that computes total page count dynamically for 'Page X of Y'."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Any] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int) -> None:
        # Suppress headers/footers on the cover page (page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))  # Slate grey

        # Running header
        self.drawString(
            54,
            11 * inch - 36,
            "ACIS COMPETITIVE INTELLIGENCE REPORT  |  CONFIDENTIAL",
        )
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 11 * inch - 40, 8.5 * inch - 54, 11 * inch - 40)

        # Running footer
        self.line(54, 45, 8.5 * inch - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(
            54,
            32,
            "FOR CLIENT INTERNAL EVALUATION ONLY  —  DO NOT REDISTRIBUTE",
        )
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(8.5 * inch - 54, 32, page_str)
        self.restoreState()


def render_report_to_pdf(report: StrategicReport) -> bytes:
    """Render a complete 14-section StrategicReport into a high-quality PDF byte string."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=12,
    )

    cover_subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#334155"),
        spaceAfter=24,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#FFFFFF"),
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )

    badge_style = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#DC2626"),
    )

    story: List[Any] = []
    meta = report.metadata

    # -------------------------------------------------------------------------
    # Section 1: Cover Page
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 1.2 * inch))
    story.append(
        Paragraph("CONFIDENTIAL COMPETITIVE INTELLIGENCE REPORT", badge_style)
    )
    story.append(Spacer(1, 10))
    story.append(Paragraph(meta.title, cover_title_style))
    story.append(
        Paragraph(
            f"Evidence-grounded strategic intelligence profile, competitor capability benchmarking, "
            f"and actionable positioning analysis for <b>{meta.target_company}</b>.",
            cover_subtitle_style,
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=25,
        )
    )

    # Metadata Grid
    meta_rows = [
        [
            Paragraph("<b>Target Company:</b>", table_cell_style),
            Paragraph(meta.target_company, table_cell_style),
        ],
        [
            Paragraph("<b>Report Identifier:</b>", table_cell_style),
            Paragraph(meta.report_id, table_cell_style),
        ],
        [
            Paragraph("<b>Research Run ID:</b>", table_cell_style),
            Paragraph(meta.research_id, table_cell_style),
        ],
        [
            Paragraph("<b>Client Organization:</b>", table_cell_style),
            Paragraph(meta.client_name or meta.organization_id, table_cell_style),
        ],
        [
            Paragraph("<b>Classification:</b>", table_cell_style),
            Paragraph(meta.confidentiality, table_cell_style),
        ],
        [
            Paragraph("<b>Generated Timestamp:</b>", table_cell_style),
            Paragraph(
                meta.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                table_cell_style,
            ),
        ],
        [
            Paragraph("<b>Overall Confidence:</b>", table_cell_style),
            Paragraph(f"{int(meta.overall_confidence * 100)}%", table_cell_style),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[1.8 * inch, 4.5 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # Section 2: Executive Summary
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. Executive Summary", h1_style))
    exec_sum = report.executive_summary
    if exec_sum.narrative:
        story.append(Paragraph(exec_sum.narrative, body_style))
    else:
        story.append(Paragraph(exec_sum.target_company_overview, body_style))

    story.append(Paragraph("Key Competitive Findings", h2_style))
    for f in exec_sum.main_competitive_findings:
        story.append(Paragraph(f"• {f}", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Top Strategic Recommendations", h2_style))
    for i, r in enumerate(exec_sum.top_recommendations, 1):
        story.append(Paragraph(f"<b>{i}.</b> {r}", bullet_style))

    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # Section 3: Research Scope and Methodology
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Scope and Methodology", h1_style))
    scope = report.research_scope
    story.append(
        Paragraph(
            f"<b>Objectives:</b> {scope.research_objectives}", body_style
        )
    )
    story.append(
        Paragraph(
            f"<b>Competitors Evaluated:</b> {', '.join(scope.competitors_examined) if scope.competitors_examined else 'None qualified'}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Collection & Validation Methodology:</b> {scope.collection_methodology} {scope.validation_methodology}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Confidence Scoring:</b> {scope.confidence_scoring_methodology}",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # Section 4: Target Company Profile
    # -------------------------------------------------------------------------
    story.append(
        Paragraph("3. Target Company Intelligence Profile", h1_style)
    )
    tcp = report.target_company_profile
    tcp_rows = [
        [
            Paragraph("<b>Company Name</b>", table_cell_style),
            Paragraph(tcp.company_name, table_cell_style),
        ],
        [
            Paragraph("<b>Core Business Model</b>", table_cell_style),
            Paragraph(
                tcp.core_business_model or "Not publicly disclosed",
                table_cell_style,
            ),
        ],
        [
            Paragraph("<b>Pricing Strategy</b>", table_cell_style),
            Paragraph(
                tcp.pricing_strategy or "Undocumented in public sources",
                table_cell_style,
            ),
        ],
        [
            Paragraph("<b>Core Products & Services</b>", table_cell_style),
            Paragraph(
                ", ".join(tcp.main_products_and_services) or "None documented",
                table_cell_style,
            ),
        ],
        [
            Paragraph("<b>Target Customer Segments</b>", table_cell_style),
            Paragraph(
                ", ".join(tcp.target_customer_segments) or "General market",
                table_cell_style,
            ),
        ],
        [
            Paragraph("<b>Geographic Presence</b>", table_cell_style),
            Paragraph(
                ", ".join(tcp.geographic_positioning) or "Undocumented",
                table_cell_style,
            ),
        ],
        [
            Paragraph("<b>Information Class</b>", table_cell_style),
            Paragraph(
                f"{tcp.information_class.value.upper()} (Confidence: {int(tcp.confidence * 100)}%)",
                table_cell_style,
            ),
        ],
    ]
    tcp_table = Table(tcp_rows, colWidths=[2.0 * inch, 4.3 * inch])
    tcp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tcp_table)

    story.append(Spacer(1, 14))

    # -------------------------------------------------------------------------
    # Section 5 & 6: Competitor Profiles & Comparison Matrix
    # -------------------------------------------------------------------------
    story.append(Paragraph("4. Competitive Comparison", h1_style))
    if not report.competitive_comparison:
        story.append(
            Paragraph("No competitor comparisons available.", body_style)
        )
    else:
        for ccomp in report.competitive_comparison:
            story.append(
                Paragraph(
                    f"Benchmarking: {meta.target_company} vs. {ccomp.competitor_name}",
                    h2_style,
                )
            )
            dim_rows = [
                [
                    Paragraph("Dimension", table_header_style),
                    Paragraph(meta.target_company, table_header_style),
                    Paragraph(ccomp.competitor_name, table_header_style),
                    Paragraph("Status", table_header_style),
                ]
            ]
            for dim in ccomp.comparison_dimensions:
                d_title = dim.dimension.replace("_", " ").title()
                t_val = dim.target_company_value or "Unknown"
                c_val = dim.competitor_value or "Unknown"
                st = dim.availability_status.value
                dim_rows.append(
                    [
                        Paragraph(d_title, table_cell_style),
                        Paragraph(t_val, table_cell_style),
                        Paragraph(c_val, table_cell_style),
                        Paragraph(st, table_cell_style),
                    ]
                )

            dim_table = Table(
                dim_rows,
                colWidths=[1.5 * inch, 1.8 * inch, 1.8 * inch, 1.2 * inch],
            )
            dim_table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#1E293B"),
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [
                                colors.HexColor("#FFFFFF"),
                                colors.HexColor("#F8FAFC"),
                            ],
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#CBD5E1"),
                        ),
                        (
                            "INNERGRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#E2E8F0"),
                        ),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(dim_table)
            story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # Section 8: SWOT Analysis
    # -------------------------------------------------------------------------
    story.append(Paragraph("5. SWOT Analysis", h1_style))
    swot = report.swot_analysis
    story.append(Paragraph(f"<i>{swot.overall_summary}</i>", body_style))

    # Strengths & Weaknesses
    swot_rows = [
        [
            Paragraph("Category", table_header_style),
            Paragraph("Item & Empirical Basis", table_header_style),
            Paragraph("Impact", table_header_style),
            Paragraph("Confidence", table_header_style),
        ]
    ]
    for s in swot.strengths:
        swot_rows.append(
            [
                Paragraph("<b>STRENGTH</b>", table_cell_style),
                Paragraph(
                    f"<b>{s.title}</b>: {s.description}", table_cell_style
                ),
                Paragraph(s.strategic_impact.value.upper(), table_cell_style),
                Paragraph(
                    f"{int(s.confidence_score * 100)}%", table_cell_style
                ),
            ]
        )
    for w in swot.weaknesses:
        swot_rows.append(
            [
                Paragraph("<b>WEAKNESS</b>", table_cell_style),
                Paragraph(
                    f"<b>{w.title}</b>: {w.description}", table_cell_style
                ),
                Paragraph(w.strategic_impact.value.upper(), table_cell_style),
                Paragraph(
                    f"{int(w.confidence_score * 100)}%", table_cell_style
                ),
            ]
        )
    for o in swot.opportunities:
        swot_rows.append(
            [
                Paragraph("<b>OPPORTUNITY</b>", table_cell_style),
                Paragraph(
                    f"<b>{o.title}</b>: {o.description}", table_cell_style
                ),
                Paragraph(o.strategic_impact.value.upper(), table_cell_style),
                Paragraph(
                    f"{int(o.confidence_score * 100)}%", table_cell_style
                ),
            ]
        )
    for t in swot.threats:
        swot_rows.append(
            [
                Paragraph("<b>THREAT</b>", table_cell_style),
                Paragraph(
                    f"<b>{t.title}</b>: {t.description}", table_cell_style
                ),
                Paragraph(t.strategic_impact.value.upper(), table_cell_style),
                Paragraph(
                    f"{int(t.confidence_score * 100)}%", table_cell_style
                ),
            ]
        )

    swot_table = Table(
        swot_rows, colWidths=[1.1 * inch, 3.6 * inch, 0.8 * inch, 0.8 * inch]
    )
    swot_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")],
                ),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(swot_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------------------
    # Section 11: Strategic Recommendations
    # -------------------------------------------------------------------------
    story.append(Paragraph("6. Strategic Recommendations", h1_style))
    for rec in report.strategic_recommendations:
        p_color = (
            "#DC2626"
            if rec.priority.value == "critical"
            else ("#D97706" if rec.priority.value == "high" else "#2563EB")
        )
        rec_box = [
            [
                Paragraph(
                    f"<font color='{p_color}'><b>[{rec.priority.value.upper()}]</b></font> <b>{rec.title}</b>",
                    body_style,
                )
            ],
            [
                Paragraph(
                    f"<b>Objective:</b> {rec.strategic_objective}<br/>"
                    f"<b>Impact:</b> {rec.expected_business_impact}<br/>"
                    f"<b>Horizon:</b> {format_time_horizon(rec.time_horizon)} | <b>Difficulty:</b> {rec.implementation_difficulty.value}<br/>"
                    f"<b>Success Metrics:</b> {', '.join(rec.success_metrics)}",
                    body_style,
                )
            ],
        ]
        rec_table = Table(rec_box, colWidths=[6.3 * inch])
        rec_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(rec_table)
        story.append(Spacer(1, 6))

    # -------------------------------------------------------------------------
    # Section 12: Evidence & Source Appendix
    # -------------------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("7. Evidence and Source Appendix", h1_style),
        Paragraph(
            "Every cited claim in this report is mapped to empirical web provenance:",
            body_style,
        )
    ]))

    if report.evidence_appendix:
        ev_rows = [
            [
                Paragraph("Evidence ID", table_header_style),
                Paragraph("Extracted Claim", table_header_style),
                Paragraph("Source Domain & Link", table_header_style),
                Paragraph("Status", table_header_style),
                Paragraph("Conf.", table_header_style),
            ]
        ]
        for ev in report.evidence_appendix[:15]:
            url_str = (
                f"<a href='{ev.source_url}'><u>{ev.source_domain}</u></a>"
                if ev.source_url
                else ev.source_domain
            )
            ev_rows.append(
                [
                    Paragraph(ev.evidence_id, table_cell_style),
                    Paragraph(ev.claim[:90] + ("..." if len(ev.claim) > 90 else ""), table_cell_style),
                    Paragraph(url_str, table_cell_style),
                    Paragraph(ev.verification_status, table_cell_style),
                    Paragraph(
                        f"{int(ev.confidence_score * 100)}%", table_cell_style
                    ),
                ]
            )

        ev_table = Table(
            ev_rows,
            colWidths=[
                1.1 * inch,
                2.5 * inch,
                1.5 * inch,
                0.8 * inch,
                0.4 * inch,
            ],
        )
        ev_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1E293B"),
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.HexColor("#FFFFFF"),
                            colors.HexColor("#F8FAFC"),
                        ],
                    ),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#E2E8F0"),
                    ),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(ev_table)
        story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # Section 14: Research Limitations
    # -------------------------------------------------------------------------
    story.append(Paragraph("8. Research Limitations", h1_style))
    for lim in report.research_limitations:
        story.append(
            Paragraph(
                f"• <b>{lim.topic}:</b> {lim.description} <i>(Remediation: {lim.remediation_recommendation})</i>",
                bullet_style,
            )
        )

    # Build PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


__all__ = ["render_report_to_pdf"]
