import io
import re
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from core.schemas import SCORE_WEIGHTS, Analysis

PAGE_W = A4[0] - 40 * mm  # usable width with 20 mm margins
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
ACCENT = colors.HexColor("#4338CA")
HEADER_BG = colors.HexColor("#EEF2FF")
GRID = colors.HexColor("#D1D5DB")

_REPLACE = {"\u2192": "->", "\u00a0": " ", "\u2212": "-", "\u2011": "-", "\u200b": ""}

LABELS = {
    "required_skills": "Required skills",
    "experience_level": "Experience level",
    "domain_relevance": "Domain relevance",
    "keywords": "Keywords",
}


def _safe(text) -> str:
    """Make text safe for ReportLab: strip unsupported characters, escape markup."""
    text = str(text or "")
    for old, new in _REPLACE.items():
        text = text.replace(old, new)
    text = text.encode("cp1252", "replace").decode("cp1252")  # Helvetica's character set
    return escape(text)


def _highlight(text) -> str:
    """Escape text and emphasize [placeholders] the user needs to fill in."""
    return re.sub(r"\[[^\]]*\]",
                  lambda m: f'<font color="#B45309"><b>{m.group(0)}</b></font>',
                  _safe(text))


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=22, textColor=INK,
                                alignment=0, spaceAfter=2),
        "sub": ParagraphStyle("sub", parent=base["Normal"], fontSize=9, textColor=MUTED),
                "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, textColor=ACCENT,
                             spaceBefore=10, spaceAfter=6, keepWithNext=1),
        "note": ParagraphStyle("note", parent=base["Normal"], fontSize=9, textColor=MUTED,
                               spaceAfter=6, keepWithNext=1),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=14, textColor=INK),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=9, leading=12, textColor=INK),
        "head": ParagraphStyle("head", parent=base["Normal"], fontSize=9, leading=12,
                               textColor=ACCENT, fontName="Helvetica-Bold"),
        "score": ParagraphStyle("score", parent=base["Normal"], fontSize=34, leading=38,
                                fontName="Helvetica-Bold"),
    }


def _score_color(score: int):
    if score >= 75:
        return colors.HexColor("#15803D")
    if score >= 50:
        return colors.HexColor("#B45309")
    return colors.HexColor("#B91C1C")


def _table(header, rows, widths, st, html_cols=()):
    """Table with wrapped Paragraph cells. Columns in html_cols get placeholder highlighting."""
    data = [[Paragraph(_safe(h), st["head"]) for h in header]]
    for row in rows:
        data.append([
            Paragraph(_highlight(c) if i in html_cols else _safe(c), st["cell"])
            for i, c in enumerate(row)
        ])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 10 * mm, "AI Career Copilot - AI-generated analysis, verify before use")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(analysis: Analysis, job_title: str = "", cover_letter: str = "") -> bytes:
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=15 * mm, bottomMargin=18 * mm,
                        title="Resume Audit", author="AI Career Copilot")
    story = []

    # Header
    story.append(Paragraph("Resume Audit", st["title"]))
    subtitle = f"{date.today():%d %b %Y}" + (f"  |  Target role: {job_title}" if job_title else "")
    story.append(Paragraph(_safe(subtitle), st["sub"]))
    story.append(Spacer(1, 10))

    # Score + breakdown
    score = analysis.overall_score
    score_style = ParagraphStyle("s", parent=st["score"], textColor=_score_color(score))
    left = [Paragraph(f"{score}%", score_style), Paragraph("Overall match", st["sub"])]
    breakdown = [[LABELS[k], f"{getattr(analysis.score_breakdown, k)}", f"{int(w * 100)}%"]
                 for k, w in SCORE_WEIGHTS.items()]
    right = _table(["Category", "Score", "Weight"], breakdown, [45 * mm, 20 * mm, 20 * mm], st)
    top = Table([[left, right]], colWidths=[PAGE_W - 90 * mm, 90 * mm])
    top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(top)

    story.append(Paragraph("Summary", st["h2"]))
    story.append(Paragraph(_safe(analysis.summary), st["body"]))

    # Matched skills
    story.append(Paragraph("Matched skills", st["h2"]))
    if analysis.matched_skills:
        rows = [[s.skill, s.evidence] for s in analysis.matched_skills]
        story.append(_table(["Skill", "Evidence from your resume"], rows, [40 * mm, PAGE_W - 40 * mm], st))
    else:
        story.append(Paragraph("None identified.", st["body"]))

    # Missing skills
    story.append(Paragraph("Missing skills", st["h2"]))
    if analysis.missing_skills:
        ordered = sorted(analysis.missing_skills, key=lambda s: s.importance != "required")
        rows = [[s.skill, s.importance.capitalize(), s.suggestion] for s in ordered]
        story.append(_table(["Skill", "Importance", "How to address it"], rows,
                            [35 * mm, 25 * mm, PAGE_W - 60 * mm], st))
    else:
        story.append(Paragraph("None identified.", st["body"]))

    # Missing keywords
    story.append(Paragraph("Missing keywords", st["h2"]))
    story.append(Paragraph(_safe(", ".join(analysis.missing_keywords) or "None identified."), st["body"]))

    # Bullet fixes
    story.append(Paragraph("Suggested bullet rewrites", st["h2"]))
    if analysis.bullet_fixes:
        if any(b.needs_user_input for b in analysis.bullet_fixes):
            story.append(Paragraph(
                'Items in <font color="#B45309"><b>[brackets]</b></font> are placeholders. '
                "Replace them with your real numbers, or remove them if you have none.",
                st["note"]))
        rows = [[b.original, b.improved, b.reason] for b in analysis.bullet_fixes]
        story.append(_table(["Original", "Improved", "Why"], rows,
                            [55 * mm, 65 * mm, PAGE_W - 120 * mm], st, html_cols=(1,)))
    else:
        story.append(Paragraph("No rewrites available.", st["body"]))

    # Optional cover letter
    if cover_letter.strip():
        story.append(PageBreak())
        story.append(Paragraph("Cover letter draft", st["title"]))
        story.append(Spacer(1, 8))
        for para in cover_letter.strip().split("\n\n"):
            story.append(Paragraph(_safe(para).replace("\n", "<br/>"), st["body"]))
            story.append(Spacer(1, 8))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()