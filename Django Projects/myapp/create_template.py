import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def build_official_inu_template(output_path):
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=22, leading=26, alignment=1, spaceAfter=30
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=14, leading=18, alignment=1, spaceAfter=15
    )
    body_style = ParagraphStyle(
        'BodyStyle', parent=styles['Normal'], fontName='Helvetica',
        fontSize=11, leading=16, spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=14, leading=18, textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=12, spaceAfter=10
    )

    # --- PAGE 1: COVER PAGE ---
    story.append(Spacer(1, 40))
    story.append(Paragraph("FINAL YEAR PROJECT PROPOSAL", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("[INSERT PROJECT TITLE HERE]", title_style))
    story.append(Spacer(1, 40))
    story.append(Paragraph("INU", subtitle_style))
    story.append(Paragraph("Submitted By:", body_style))
    story.append(Paragraph("Student Name 1 (Registration ID)<br/>Student Name 2 (Registration ID)", body_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Session 2022-2026", subtitle_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Supervised By: [Supervisor Name Here]", body_style))
    story.append(Spacer(1, 40))
    
    institution_text = (
        "A project proposal submitted to The IQRA National University, Peshawar "
        "in partial fulfillment of the requirements for the degree of "
        "BACHELOR OF SCIENCE (BS) IN COMPUTER SCIENCE<br/><br/>"
        "SCHOOL OF COMPUTER SCIENCE<br/>"
        "IQRA NATIONAL UNIVERSITY, PESHAWAR-PAKISTAN"
    )
    story.append(Paragraph(institution_text, ParagraphStyle('Inst', parent=body_style, alignment=1)))
    story.append(PageBreak())

    # --- PAGE 2: STRUCTURAL LAYOUTS ---
    story.append(Paragraph("Table of Contents", heading_style))
    toc_data = [
        ["1. Introduction & Problem Statement", "1"],
        ["2. Objectives of Project", "1"],
        ["3. Methodology & System Architecture", "2"],
        ["4. Proposed Time Schedule (Gantt Chart)", "3"],
        ["5. Budget Description & Technical Stack", "3"],
        ["6. Undertaking & Signatures", "4"]
    ]
    t1 = Table(toc_data, colWidths=[400, 50])
    t1.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t1)
    story.append(Spacer(1, 20))

    story.append(Paragraph("List of Acronyms", heading_style))
    acronym_data = [
        ["Acronym", "Description"],
        ["INU", "IQRA National University"],
        ["AI", "Artificial Intelligence"],
        ["NLP", "Natural Language Processing"],
        ["LLM", "Large Language Model"],
        ["API", "Application Programming Interface"],
        ["UI/UX", "User Interface / User Experience"],
        ["BLE/IoT", "Bluetooth Low Energy / Internet of Things"]
    ]
    t2 = Table(acronym_data, colWidths=[120, 330])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t2)
    story.append(PageBreak())

    # --- PAGE 3 & 4: BODY TEMPLATE & UNDERTAKING ---
    story.append(Paragraph("1. Introduction & Problem Statement", heading_style))
    story.append(Paragraph("[Student introduction prose background context runs here]", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2. Objectives of Project", heading_style))
    story.append(Paragraph("• Milestone Objective Variable Target 1<br/>• Milestone Objective Variable Target 2", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("3. Methodology & System Architecture", heading_style))
    story.append(Paragraph("Core Modules:<br/>1. Authentication & Profile Integration Module<br/>2. Core Execution and Inference Pipeline<br/>3. Analytics & Reporting Layout Engine", body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("6. Undertaking & Project Declarations", heading_style))
    declaration_text = (
        "We hereby declare that this technical development proposal is our genuine work "
        "executed under supervision at IQRA National University. No portion of this engineering "
        "research layout has been submitted previously for academic credit at any alternative educational board."
    )
    story.append(Paragraph(declaration_text, body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Student 1 Signature: _______________________", body_style))
    story.append(Paragraph("Student 2 Signature: _______________________", body_style))
    story.append(PageBreak())

    # --- PAGE 5: INSTITUTIONAL LOG PANELS ---
    story.append(Paragraph("7. Institutional Review Panel Logs", heading_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Supervisor Evaluation Section:", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Supervisor Signature: _______________________", body_style))
    story.append(Paragraph("Date: ____/____/______", body_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("FYP Department Coordinator Workspace:", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Coordinator Signature: _______________________", body_style))
    story.append(Paragraph("Status: APPROVED / HOLD", body_style))

    doc.build(story)
    print(f"[✓] Template compilation complete. PDF written to: {output_path}")


if __name__ == "__main__":
    # Points cleanly inside your "Pdf Media" directory
    build_official_inu_template("Pdf Media/templates/INU_Official_FYP_Template.pdf")