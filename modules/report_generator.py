# ============================================================
# modules/report_generator.py
# Generates a downloadable PDF report for each analysis
# Uses the 'reportlab' library to create PDFs with Python
# ============================================================

import os
import json
from datetime import datetime

def generate_pdf_report(analysis, username):
    """
    Create a PDF report with the analysis results.

    analysis = the database row with all the analysis data
    username = name of the person who ran the analysis
    Returns the path to the generated PDF file.
    """
    try:
        # Try to use reportlab (pip install reportlab)
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # Create output folder if it doesn't exist
        reports_folder = 'static/reports'
        os.makedirs(reports_folder, exist_ok=True)

        # File path for the PDF
        filename  = f"report_{analysis['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath  = os.path.join(reports_folder, filename)

        # Parse JSON strings back to lists
        matched_skills = json.loads(analysis['matched_skills']) if analysis['matched_skills'] else []
        missing_skills = json.loads(analysis['missing_skills']) if analysis['missing_skills'] else []

        # ---- Create PDF document ----
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        # Get default styles
        styles = getSampleStyleSheet()

        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6c63ff'),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=8
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )

        # ---- Build content ----
        content = []

        # Title
        content.append(Paragraph("🎯 ATS Resume Analysis Report", title_style))
        content.append(HRFlowable(width="100%", color=colors.HexColor('#6c63ff')))
        content.append(Spacer(1, 0.2*inch))

        # Info section
        content.append(Paragraph(f"<b>Analyzed by:</b> {username}", normal_style))
        content.append(Paragraph(f"<b>Date:</b> {analysis['created_at'][:10]}", normal_style))
        content.append(Paragraph(f"<b>Resume File:</b> {analysis['resume_filename']}", normal_style))
        content.append(Spacer(1, 0.2*inch))

        # ATS Score (big number)
        score_color = '#22c55e' if analysis['ats_score'] >= 60 else '#f59e0b' if analysis['ats_score'] >= 30 else '#ef4444'
        score_style = ParagraphStyle(
            'Score',
            parent=styles['Normal'],
            fontSize=40,
            textColor=colors.HexColor(score_color),
            alignment=TA_CENTER
        )
        content.append(Paragraph(f"{analysis['ats_score']}%", score_style))
        content.append(Paragraph("ATS Score", ParagraphStyle(
            'ScoreLabel', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)))
        content.append(Spacer(1, 0.3*inch))

        # Matched Skills
        content.append(HRFlowable(width="100%", color=colors.lightgrey))
        content.append(Spacer(1, 0.1*inch))
        content.append(Paragraph("✅ Matched Skills", header_style))
        if matched_skills:
            skills_text = ", ".join(matched_skills)
            content.append(Paragraph(skills_text, normal_style))
        else:
            content.append(Paragraph("No matching skills found.", normal_style))
        content.append(Spacer(1, 0.2*inch))

        # Missing Skills
        content.append(Paragraph("❌ Missing Skills (Skill Gap)", header_style))
        if missing_skills:
            skills_text = ", ".join(missing_skills)
            content.append(Paragraph(skills_text, normal_style))
        else:
            content.append(Paragraph("No missing skills — great match!", normal_style))
        content.append(Spacer(1, 0.2*inch))

        # Recommendations
        content.append(Paragraph("💡 Recommendations", header_style))
        recs = [
            "Tailor your resume keywords to match the job description.",
            "Quantify your achievements with numbers and percentages.",
            "Add links to GitHub, portfolio, or LinkedIn profile.",
            "Keep resume to 1-2 pages with clean formatting.",
            "Learn the missing skills via online courses (Coursera, Udemy)."
        ]
        for rec in recs:
            content.append(Paragraph(f"• {rec}", normal_style))

        content.append(Spacer(1, 0.3*inch))
        content.append(HRFlowable(width="100%", color=colors.HexColor('#6c63ff')))
        content.append(Paragraph(
            "Generated by AI Resume Skill Matcher | Advanced Career Intelligence System",
            ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER,
                           fontSize=9, textColor=colors.grey)
        ))

        # Build the PDF
        doc.build(content)
        return filepath

    except ImportError:
        # If reportlab is not installed, create a simple text file instead
        reports_folder = 'static/reports'
        os.makedirs(reports_folder, exist_ok=True)
        filepath = os.path.join(reports_folder, f"report_{analysis['id']}.txt")
        with open(filepath, 'w') as f:
            f.write(f"ATS Resume Report\n")
            f.write(f"Score: {analysis['ats_score']}%\n")
            f.write(f"Install reportlab for PDF: pip install reportlab\n")
        return filepath
