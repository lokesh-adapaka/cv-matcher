import io
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

logger = logging.getLogger(__name__)


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CVName",
        parent=styles["Title"],
        fontSize=22,
        textColor=HexColor("#1a365d"),
        spaceAfter=2 * mm,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "CVContact",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#4a5568"),
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        "CVSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=HexColor("#2b6cb0"),
        spaceBefore=6 * mm,
        spaceAfter=2 * mm,
        borderPadding=(0, 0, 2, 0),
    ))
    styles.add(ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=HexColor("#2d3748"),
    ))
    styles.add(ParagraphStyle(
        "CVJobTitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=HexColor("#1a365d"),
        fontName="Helvetica-Bold",
        spaceAfter=1 * mm,
    ))
    styles.add(ParagraphStyle(
        "CVJobMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#718096"),
        spaceAfter=2 * mm,
    ))
    return styles


def generate_cv_pdf(name: str, email: str, phone: str, cv_data: dict) -> bytes:
    """Generate a professional PDF CV from structured data."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = _build_styles()
    elements = []

    # --- Header ---
    elements.append(Paragraph(name or "Candidate", styles["CVName"]))

    contact_parts = [p for p in [email, phone] if p]
    if contact_parts:
        elements.append(Paragraph(" | ".join(contact_parts), styles["CVContact"]))

    elements.append(HRFlowable(
        width="100%", thickness=1, color=HexColor("#2b6cb0"),
        spaceAfter=4 * mm, spaceBefore=2 * mm,
    ))

    # --- Summary ---
    summary = cv_data.get("summary", "")
    if summary:
        elements.append(Paragraph("PROFESSIONAL SUMMARY", styles["CVSection"]))
        elements.append(Paragraph(summary, styles["CVBody"]))

    # --- Skills ---
    skills = cv_data.get("skills", [])
    if skills:
        elements.append(Paragraph("SKILLS", styles["CVSection"]))
        # Display skills in a wrapped format
        skills_text = " &bull; ".join(skills)
        elements.append(Paragraph(skills_text, styles["CVBody"]))

    # --- Keywords Added (for tailored CVs) ---
    keywords = cv_data.get("keywords_added", [])
    if keywords:
        elements.append(Spacer(1, 2 * mm))
        kw_text = f"<i>Key competencies: {', '.join(keywords)}</i>"
        elements.append(Paragraph(kw_text, styles["CVBody"]))

    # --- Experience ---
    experience = cv_data.get("experience", [])
    if experience:
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["CVSection"]))
        for exp in experience:
            title = exp.get("title", "")
            company = exp.get("company", "")
            duration = exp.get("duration", "")
            desc = exp.get("description", "")

            elements.append(Paragraph(title, styles["CVJobTitle"]))
            meta = f"{company}"
            if duration:
                meta += f" | {duration}"
            elements.append(Paragraph(meta, styles["CVJobMeta"]))
            if desc:
                elements.append(Paragraph(desc, styles["CVBody"]))
            elements.append(Spacer(1, 2 * mm))

    # --- Education ---
    education = cv_data.get("education", [])
    if education:
        elements.append(Paragraph("EDUCATION", styles["CVSection"]))
        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")

            elements.append(Paragraph(degree, styles["CVJobTitle"]))
            meta = institution
            if year:
                meta += f" | {year}"
            elements.append(Paragraph(meta, styles["CVJobMeta"]))

    # Build PDF
    try:
        doc.build(elements)
    except Exception as e:
        logger.error(f"Failed to build PDF: {e}")
        raise ValueError(f"PDF generation failed: {e}")

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
