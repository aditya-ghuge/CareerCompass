"""
CareerCompass AI - PDF Generation Module
Produces a professional, branded PDF report using ReportLab.
"""

import io
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand Colors
# ---------------------------------------------------------------------------
IBM_BLUE = colors.HexColor("#0f62fe")
DARK_NAVY = colors.HexColor("#0a0e1a")
LIGHT_GRAY = colors.HexColor("#f4f4f4")
MID_GRAY = colors.HexColor("#8d8d8d")
BORDER_GRAY = colors.HexColor("#e0e0e0")
SUCCESS_GREEN = colors.HexColor("#24a148")
WARNING_ORANGE = colors.HexColor("#f1620c")
GAP_RED = colors.HexColor("#da1e28")
TEXT_DARK = colors.HexColor("#161616")
TEXT_MUTED = colors.HexColor("#525252")
WHITE = colors.white


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        "h1": ParagraphStyle(
            "h1", parent=base["Normal"],
            fontSize=26, fontName="Helvetica-Bold",
            textColor=DARK_NAVY, spaceAfter=8, leading=32,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Normal"],
            fontSize=16, fontName="Helvetica-Bold",
            textColor=IBM_BLUE, spaceAfter=6, spaceBefore=16, leading=22,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Normal"],
            fontSize=12, fontName="Helvetica-Bold",
            textColor=TEXT_DARK, spaceAfter=4, spaceBefore=8, leading=16,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10.5, fontName="Helvetica",
            textColor=TEXT_DARK, spaceAfter=6, leading=16,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["Normal"],
            fontSize=9.5, fontName="Helvetica",
            textColor=TEXT_MUTED, spaceAfter=4, leading=14,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=MID_GRAY, spaceAfter=2, leading=11,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontSize=8, fontName="Helvetica-Bold",
            textColor=IBM_BLUE, spaceAfter=1, leading=11,
            textTransform="uppercase",
        ),
        "center_h1": ParagraphStyle(
            "center_h1", parent=base["Normal"],
            fontSize=26, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=6, leading=32,
        ),
        "center_sub": ParagraphStyle(
            "center_sub", parent=base["Normal"],
            fontSize=12, fontName="Helvetica",
            textColor=colors.HexColor("#c6c6c6"), alignment=TA_CENTER,
            spaceAfter=4, leading=16,
        ),
        "center_muted": ParagraphStyle(
            "center_muted", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=MID_GRAY, alignment=TA_CENTER, leading=12,
        ),
        "right": ParagraphStyle(
            "right", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=TEXT_MUTED, alignment=TA_RIGHT, leading=12,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontSize=10.5, fontName="Helvetica",
            textColor=TEXT_DARK, leftIndent=14, bulletIndent=0,
            spaceAfter=4, leading=16,
        ),
        "tag": ParagraphStyle(
            "tag", parent=base["Normal"],
            fontSize=8, fontName="Helvetica-Bold",
            textColor=IBM_BLUE, spaceAfter=1, leading=11,
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Helper flowable builders
# ---------------------------------------------------------------------------

def _hr(color=BORDER_GRAY, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=6)


def _spacer(h=4):
    return Spacer(1, h * mm)


def _section_header(title: str, styles: dict):
    return [
        _spacer(3),
        Paragraph(title.upper(), styles["label"]),
        _hr(IBM_BLUE, 1.5),
    ]


def _score_bar_drawing(score: int, width=140, height=14, color=IBM_BLUE):
    """Draw a progress bar for a score (0–100)."""
    d = Drawing(width, height)
    # Background
    d.add(Rect(0, 0, width, height, fillColor=LIGHT_GRAY, strokeColor=None))
    # Fill
    fill_w = max(2, int(width * score / 100))
    d.add(Rect(0, 0, fill_w, height, fillColor=color, strokeColor=None))
    return d


def _skill_tag_table(skills: list, styles: dict, col_width=85):
    """Render skill tags as a flowing table."""
    if not skills:
        return Paragraph("No skills listed.", styles["muted"])
    cols = 4
    rows = []
    row = []
    for i, skill in enumerate(skills):
        cell = Table(
            [[Paragraph(skill, styles["tag"])]],
            colWidths=[col_width],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#edf5ff")),
                ("ROUNDEDCORNERS", [4]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]),
        )
        row.append(cell)
        if len(row) == cols:
            rows.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append(Paragraph("", styles["muted"]))
        rows.append(row)
    if not rows:
        return Paragraph("", styles["muted"])
    return Table(rows, colWidths=[col_width] * cols,
                 style=TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 3),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _build_cover(story, analysis: dict, styles: dict):
    profile = analysis["profile"]
    cr = analysis["career_recommendation"]
    generated = analysis.get("generated_at", "")
    try:
        dt = datetime.fromisoformat(generated)
        date_str = dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        date_str = datetime.now().strftime("%B %d, %Y")

    # Header banner
    banner_data = [[
        Paragraph("CareerCompass AI", ParagraphStyle(
            "banner", fontSize=18, fontName="Helvetica-Bold",
            textColor=WHITE, leading=22,
        )),
        Paragraph("Developed by Aditya Ghuge", ParagraphStyle(
            "banner_sub", fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#a8c7fa"), alignment=TA_RIGHT, leading=12,
        )),
    ]]
    banner = Table(banner_data, colWidths=[280, 215],
                   style=TableStyle([
                       ("BACKGROUND", (0, 0), (-1, -1), DARK_NAVY),
                       ("TOPPADDING", (0, 0), (-1, -1), 14),
                       ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                       ("LEFTPADDING", (0, 0), (0, 0), 14),
                       ("RIGHTPADDING", (-1, -1), (-1, -1), 14),
                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ]))
    story.append(banner)
    story.append(_spacer(10))

    # Name + Title block
    story.append(Paragraph(f"Career Analysis Report", styles["h1"]))
    story.append(Paragraph(
        f"Prepared for <b>{profile['name']}</b>",
        ParagraphStyle("prep", fontSize=14, fontName="Helvetica",
                       textColor=TEXT_DARK, spaceAfter=4, leading=18),
    ))
    story.append(_hr(BORDER_GRAY, 0.5))
    story.append(_spacer(4))

    # Profile summary table
    profile_data = [
        ["College", profile["college"], "Branch / Major", profile["branch"]],
        ["Year", profile["year"], "CGPA", f"{profile['cgpa']} / 10.0"],
        ["Age", str(profile["age"]), "Career Goal", profile["career_goal"]],
        ["Report Date", date_str, "Model", "IBM watsonx.ai"],
    ]
    pt = Table(profile_data, colWidths=[80, 160, 80, 160],
               style=TableStyle([
                   ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                   ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8f9fa")),
                   ("TEXTCOLOR", (0, 0), (-1, -1), TEXT_DARK),
                   ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                   ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                   ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                   ("FONTNAME", (3, 0), (3, -1), "Helvetica"),
                   ("FONTSIZE", (0, 0), (-1, -1), 10),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                   ("TOPPADDING", (0, 0), (-1, -1), 8),
                   ("LEFTPADDING", (0, 0), (-1, -1), 10),
                   ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
               ]))
    story.append(pt)
    story.append(_spacer(10))

    # Career recommendation highlight box
    match_pct = cr["match_score"]
    conf_pct = cr["confidence_score"]
    highlight_data = [
        [
            Paragraph("RECOMMENDED CAREER", styles["label"]),
            Paragraph("CAREER MATCH", styles["label"]),
            Paragraph("CONFIDENCE", styles["label"]),
        ],
        [
            Paragraph(f"<b>{cr['primary_career']}</b>",
                      ParagraphStyle("big", fontSize=13, fontName="Helvetica-Bold",
                                     textColor=IBM_BLUE, leading=18)),
            Paragraph(f"<b>{match_pct}%</b>",
                      ParagraphStyle("score", fontSize=20, fontName="Helvetica-Bold",
                                     textColor=SUCCESS_GREEN, alignment=TA_CENTER, leading=26)),
            Paragraph(f"<b>{conf_pct}%</b>",
                      ParagraphStyle("conf", fontSize=20, fontName="Helvetica-Bold",
                                     textColor=IBM_BLUE, alignment=TA_CENTER, leading=26)),
        ],
        [
            Paragraph(cr["career_category"], styles["muted"]),
            Paragraph(f"Market Demand: {cr['market_demand']}", styles["muted"]),
            Paragraph(f"Job Growth: +{cr['job_growth_percent']}%", styles["muted"]),
        ],
    ]
    ht = Table(highlight_data, colWidths=[200, 100, 100],
               style=TableStyle([
                   ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#edf5ff")),
                   ("GRID", (0, 0), (-1, -1), 0.5, IBM_BLUE),
                   ("TOPPADDING", (0, 0), (-1, -1), 8),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                   ("LEFTPADDING", (0, 0), (-1, -1), 10),
                   ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("ALIGN", (1, 0), (2, -1), "CENTER"),
               ]))
    story.append(ht)
    story.append(_spacer(8))

    # Why this career
    story.append(Paragraph("Why This Career?", styles["h3"]))
    story.append(Paragraph(cr.get("why_this_career", ""), styles["body"]))
    story.append(Paragraph(cr.get("confidence_explanation", ""), styles["muted"]))
    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Salary & timeline section
# ---------------------------------------------------------------------------

def _build_salary_section(story, analysis: dict, styles: dict):
    cr = analysis["career_recommendation"]
    story += _section_header("Salary Growth Projection", styles)

    salary_data = [
        ["Career Stage", "Expected Annual Salary (USD)", "Approx. Years"],
        ["Entry Level", f"${cr['avg_salary_entry']:,}", "0–2 years"],
        ["Mid-Level", f"${cr['avg_salary_mid']:,}", "3–5 years"],
        ["Senior Level", f"${cr['avg_salary_senior']:,}", "5–8 years"],
        ["Lead / Principal", f"${cr['avg_salary_lead']:,}", "8+ years"],
    ]
    st = Table(salary_data, colWidths=[160, 160, 120],
               style=TableStyle([
                   ("BACKGROUND", (0, 0), (-1, 0), DARK_NAVY),
                   ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                   ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                   ("FONTSIZE", (0, 0), (-1, -1), 10),
                   ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                   ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
                   ("TOPPADDING", (0, 0), (-1, -1), 6),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                   ("LEFTPADDING", (0, 0), (-1, -1), 10),
                   ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                   ("ALIGN", (1, 0), (2, -1), "CENTER"),
               ]))
    story.append(st)
    story.append(_spacer(6))

    story.append(Paragraph("Future Scope", styles["h3"]))
    story.append(Paragraph(cr.get("future_scope", ""), styles["body"]))
    story.append(_spacer(4))

    # Career timeline
    timeline = analysis.get("career_timeline", [])
    if timeline:
        story += _section_header("Career Timeline", styles)
        for stage in timeline:
            row_data = [[
                Paragraph(f"<b>{stage['stage']}</b>", styles["h3"]),
                Paragraph(
                    f"<b>Year {stage['years_from_now']}</b> · ${stage['expected_salary']:,}/yr",
                    ParagraphStyle("tline_right", fontSize=10, fontName="Helvetica-Bold",
                                   textColor=SUCCESS_GREEN, alignment=TA_RIGHT, leading=14)),
            ]]
            rt = Table(row_data, colWidths=[280, 160],
                       style=TableStyle([
                           ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                       ]))
            story.append(rt)
            story.append(Paragraph(stage.get("description", ""), styles["body"]))
            if stage.get("key_skills_needed"):
                story.append(Paragraph(
                    "Key skills: " + ", ".join(stage["key_skills_needed"]),
                    styles["muted"],
                ))
            story.append(_hr(BORDER_GRAY))


# ---------------------------------------------------------------------------
# Skills section
# ---------------------------------------------------------------------------

def _build_skills_section(story, analysis: dict, styles: dict):
    sa = analysis["skill_analysis"]
    story += _section_header("Skill Analysis", styles)

    # Radar scores as bar chart
    radar = sa.get("radar_scores", {})
    score_labels = {
        "technical_skills": "Technical Skills",
        "problem_solving": "Problem Solving",
        "communication": "Communication",
        "industry_knowledge": "Industry Knowledge",
        "project_experience": "Project Experience",
        "soft_skills": "Soft Skills",
    }
    bar_data = [[
        Paragraph(label, styles["body"]),
        _score_bar_drawing(radar.get(key, 50), width=160, height=12, color=IBM_BLUE),
        Paragraph(f"{radar.get(key, 50)}%",
                  ParagraphStyle("pct", fontSize=9, fontName="Helvetica-Bold",
                                 textColor=IBM_BLUE, leading=12)),
    ] for key, label in score_labels.items()]

    bt = Table(bar_data, colWidths=[110, 165, 35],
               style=TableStyle([
                   ("TOPPADDING", (0, 0), (-1, -1), 4),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                   ("LEFTPADDING", (0, 0), (-1, -1), 0),
                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
               ]))
    story.append(bt)
    story.append(_spacer(6))

    # Existing, Required, Gap
    for title, key, color in [
        ("Existing Skills", "existing_skills", SUCCESS_GREEN),
        ("Required Skills", "required_skills", IBM_BLUE),
        ("Skill Gaps", "skill_gap", GAP_RED),
    ]:
        story.append(Paragraph(title, styles["h3"]))
        skills = sa.get(key, [])
        if skills:
            story.append(_skill_tag_table(skills, styles))
        else:
            story.append(Paragraph("None identified.", styles["muted"]))
        story.append(_spacer(4))

    # Skill gap reasons
    gap_reasons = sa.get("skill_gap_reasons", {})
    if gap_reasons:
        story.append(Paragraph("Why These Skills Are Needed", styles["h3"]))
        for skill, reason in list(gap_reasons.items())[:8]:
            story.append(Paragraph(f"<b>{skill}:</b> {reason}", styles["bullet"]))
        story.append(_spacer(4))


# ---------------------------------------------------------------------------
# Roadmap section
# ---------------------------------------------------------------------------

def _build_roadmap_section(story, analysis: dict, styles: dict):
    story.append(PageBreak())
    story += _section_header("Learning Roadmap (24 Months)", styles)
    roadmap = analysis.get("roadmap", {})

    phase_colors = [IBM_BLUE, SUCCESS_GREEN, WARNING_ORANGE, colors.HexColor("#8a3ffc")]

    for i, (key, color) in enumerate(
        zip(["phase_1", "phase_2", "phase_3", "phase_4"], phase_colors)
    ):
        phase = roadmap.get(key, {})
        if not phase:
            continue

        header_data = [[
            Paragraph(
                f"Phase {i + 1}: {phase.get('title', '')}",
                ParagraphStyle(
                    f"ph{i}", fontSize=12, fontName="Helvetica-Bold",
                    textColor=WHITE, leading=16,
                ),
            ),
            Paragraph(
                phase.get("duration", ""),
                ParagraphStyle(
                    f"ph_dur{i}", fontSize=10, fontName="Helvetica",
                    textColor=colors.HexColor("#d0d0d0"), alignment=TA_RIGHT, leading=14,
                ),
            ),
        ]]
        ht = Table(header_data, colWidths=[330, 110],
                   style=TableStyle([
                       ("BACKGROUND", (0, 0), (-1, -1), color),
                       ("TOPPADDING", (0, 0), (-1, -1), 8),
                       ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                       ("LEFTPADDING", (0, 0), (-1, -1), 10),
                       ("RIGHTPADDING", (-1, -1), (-1, -1), 10),
                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ]))
        story.append(ht)

        details_data = [
            [
                Paragraph("Weekly Focus", styles["label"]),
                Paragraph(phase.get("weekly_focus", ""), styles["body"]),
            ],
            [
                Paragraph("Monthly Milestone", styles["label"]),
                Paragraph(phase.get("monthly_milestone", ""), styles["body"]),
            ],
            [
                Paragraph("Study Hours / Week", styles["label"]),
                Paragraph(f"{phase.get('study_hours_per_week', 10)} hours", styles["body"]),
            ],
        ]
        dt = Table(details_data, colWidths=[100, 340],
                   style=TableStyle([
                       ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
                       ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                       ("TOPPADDING", (0, 0), (-1, -1), 5),
                       ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                       ("LEFTPADDING", (0, 0), (-1, -1), 8),
                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                   ]))
        story.append(dt)

        goals = phase.get("goals", [])
        if goals:
            for g in goals:
                story.append(Paragraph(f"• {g}", styles["bullet"]))

        story.append(_spacer(5))


# ---------------------------------------------------------------------------
# Projects section
# ---------------------------------------------------------------------------

def _build_projects_section(story, analysis: dict, styles: dict):
    story.append(PageBreak())
    story += _section_header("Recommended Projects", styles)
    projects = analysis.get("projects", {})

    level_config = [
        ("beginner", "Beginner", SUCCESS_GREEN),
        ("intermediate", "Intermediate", WARNING_ORANGE),
        ("advanced", "Advanced", GAP_RED),
    ]

    for level, label, color in level_config:
        items = projects.get(level, [])
        if not items:
            continue
        story.append(Paragraph(f"{label} Projects", styles["h2"]))
        for p in items:
            story.append(KeepTogether([
                Paragraph(f"<b>{p['title']}</b>", styles["h3"]),
                Paragraph(
                    f"<b>Difficulty:</b> {p['difficulty']}  ·  "
                    f"<b>Est. Time:</b> {p['estimated_time']}",
                    styles["muted"],
                ),
                Paragraph(p.get("description", ""), styles["body"]),
                Paragraph(
                    f"<b>Technologies:</b> {', '.join(p.get('technologies', []))}",
                    styles["muted"],
                ),
                Paragraph(
                    f"<b>Skills Learned:</b> {', '.join(p.get('skills_learned', []))}",
                    styles["muted"],
                ),
                Paragraph(
                    f"<b>Expected Outcome:</b> {p.get('expected_outcome', '')}",
                    styles["muted"],
                ),
                _hr(BORDER_GRAY),
            ]))
        story.append(_spacer(4))


# ---------------------------------------------------------------------------
# Certifications section
# ---------------------------------------------------------------------------

def _build_certifications_section(story, analysis: dict, styles: dict):
    certs = analysis.get("certifications", [])
    if not certs:
        return
    story += _section_header("Recommended Certifications", styles)

    cert_data = [["Certification", "Provider", "Level", "Duration", "Cost"]]
    for c in certs:
        cert_data.append([
            Paragraph(c["name"], styles["body"]),
            Paragraph(c["provider"], styles["muted"]),
            c.get("level", "Intermediate"),
            c.get("duration", "Self-paced"),
            c.get("cost", "Varies"),
        ])

    ct = Table(cert_data, colWidths=[135, 90, 65, 65, 50],
               style=TableStyle([
                   ("BACKGROUND", (0, 0), (-1, 0), IBM_BLUE),
                   ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                   ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                   ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                   ("LINEBELOW", (0, 0), (-1, 0), 1, DARK_NAVY),
                   ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#fcfcfc")]),
                   ("TOPPADDING", (0, 0), (-1, -1), 8),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                   ("LEFTPADDING", (0, 0), (-1, -1), 10),
                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
               ]))
    story.append(ct)
    story.append(_spacer(6))

    for c in certs[:4]:
        if c.get("why_important"):
            story.append(Paragraph(
                f"<b>{c['name']}:</b> {c['why_important']}", styles["bullet"],
            ))
    story.append(_spacer(4))


# ---------------------------------------------------------------------------
# Action plan section
# ---------------------------------------------------------------------------

def _build_action_plan(story, analysis: dict, styles: dict):
    story += _section_header("Your Action Plan", styles)
    ap = analysis.get("action_plan", {})

    for bucket_key, bucket_label in [
        ("immediate_actions", "Immediate Actions (This Week)"),
        ("short_term", "Short-Term Goals (1–3 Months)"),
        ("long_term", "Long-Term Goals (3–12 Months)"),
    ]:
        items = ap.get(bucket_key, [])
        if not items:
            continue
        story.append(Paragraph(bucket_label, styles["h3"]))
        for item in items:
            story.append(Paragraph(
                f"<b>→ {item.get('action', '')}</b>", styles["bullet"],
            ))
            story.append(Paragraph(
                f"   Why: {item.get('reason', '')}  |  By: {item.get('time_to_complete', '')}",
                styles["muted"],
            ))
        story.append(_spacer(4))


# ---------------------------------------------------------------------------
# Interview & resume section
# ---------------------------------------------------------------------------

def _build_interview_section(story, analysis: dict, styles: dict):
    story.append(PageBreak())
    story += _section_header("Interview Preparation", styles)
    ip = analysis.get("interview_preparation", {})

    story.append(Paragraph(ip.get("tips", ""), styles["body"]))
    story.append(_spacer(3))

    for key, label in [
        ("focus_areas", "Focus Areas"),
        ("technical_topics", "Technical Topics to Master"),
        ("common_questions", "Common Interview Questions"),
        ("preparation_resources", "Preparation Resources"),
    ]:
        items = ip.get(key, [])
        if items:
            story.append(Paragraph(label, styles["h3"]))
            for item in items:
                story.append(Paragraph(f"• {item}", styles["bullet"]))
            story.append(_spacer(3))

    # Resume tips
    pb = analysis.get("profile_building", {})
    story += _section_header("Resume & Profile Building", styles)
    for key, label in [
        ("resume_tips", "Resume Tips"),
        ("linkedin_tips", "LinkedIn Optimization"),
        ("github_tips", "GitHub Profile"),
        ("portfolio_tips", "Portfolio Building"),
    ]:
        tips = pb.get(key, [])
        if tips:
            story.append(Paragraph(label, styles["h3"]))
            for t in tips:
                story.append(Paragraph(f"• {t}", styles["bullet"]))
            story.append(_spacer(3))


# ---------------------------------------------------------------------------
# Footer helpers
# ---------------------------------------------------------------------------

def _add_page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(
        doc.leftMargin,
        10 * mm,
        "CareerCompass AI — Developed by Aditya Ghuge.(@_aditya.ghuge_)",
    )
    canvas.drawRightString(
        doc.width + doc.leftMargin,
        10 * mm,
        f"Page {doc.page}",
    )
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Main PDF builder
# ---------------------------------------------------------------------------

def generate_pdf(analysis: dict) -> bytes:
    """
    Generate a complete professional PDF report.
    Returns PDF bytes.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title="CareerCompass AI — Career Analysis Report",
        author="CareerCompass AI",
        subject=f"Career Report for {analysis['profile']['name']}",
        creator="IBM Watsonx.ai",
    )

    styles = _build_styles()
    story = []

    try:
        _build_cover(story, analysis, styles)
        _build_salary_section(story, analysis, styles)
        story.append(PageBreak())
        _build_skills_section(story, analysis, styles)
        _build_roadmap_section(story, analysis, styles)
        _build_projects_section(story, analysis, styles)
        _build_certifications_section(story, analysis, styles)
        _build_action_plan(story, analysis, styles)
        _build_interview_section(story, analysis, styles)

        # Motivational close
        story.append(_spacer(8))
        story += _section_header("A Message for You", styles)
        msg = analysis.get("motivational_message", "")
        story.append(
            Table(
                [[Paragraph(msg, ParagraphStyle(
                    "motiv", fontSize=11, fontName="Helvetica",
                    textColor=TEXT_DARK, leading=17, leftIndent=8,
                ))]],
                colWidths=[doc.width],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#edf5ff")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 14),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("BOX", (0, 0), (-1, -1), 1.5, IBM_BLUE),
                ]),
            )
        )

        # Disclaimer footer
        story.append(_spacer(10))
        story.append(_hr(BORDER_GRAY))
        story.append(Paragraph(
            "This report was generated by CareerCompass AI "
            "Recommendations are based on the student profile provided and current industry data. "
            "Career outcomes may vary. Use this report as one of many inputs in your career planning.",
            styles["caption"],
        ))

        doc.build(story, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)

    except Exception as exc:
        logger.error("PDF generation error: %s", exc)
        raise RuntimeError(f"PDF generation failed: {str(exc)}") from exc

    pdf_bytes = buffer.getvalue()
    buffer.close()
    logger.info("PDF generated successfully (%d bytes)", len(pdf_bytes))
    return pdf_bytes
