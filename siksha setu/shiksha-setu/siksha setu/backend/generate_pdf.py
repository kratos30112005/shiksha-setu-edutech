from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import os

def create_project_vision_pdf(filename="ShikshaSetu_Project_Vision_and_Architecture.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, parent=styles['Normal'], fontSize=11, leading=14))
    styles.add(ParagraphStyle(name='TitleStyle', alignment=TA_CENTER, parent=styles['Heading1'], fontSize=24, spaceAfter=20))
    styles.add(ParagraphStyle(name='SubtitleStyle', alignment=TA_CENTER, parent=styles['Heading2'], fontSize=16, spaceAfter=30))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=14, spaceBefore=20, spaceAfter=10, textColor="#1a202c"))

    story = []
    
    # 1. Title Page Elements
    story.append(Paragraph("ShikshaSetu", styles['TitleStyle']))
    story.append(Paragraph("Project Vision & Technical Approach", styles['SubtitleStyle']))
    story.append(Spacer(1, 40))
    
    # 2. Executive Vision
    story.append(Paragraph("1. Executive Vision", styles['SectionHeader']))
    vision_text = """ShikshaSetu is built on the belief that "Quality Education should be Accessible." The platform acts as a bridge between a student's aspirations and their reality by providing a personalized AI-powered learning environment. Moving away from generic mass-marketed study materials, ShikshaSetu adapts to the unique cognitive profile of every individual student, enabling them to "Study Smarter, Not Harder"."""
    story.append(Paragraph(vision_text, styles['Justify']))
    story.append(Spacer(1, 10))

    # 3. Core Features & Working Principles
    story.append(Paragraph("2. Core Features & Working Mechanisms", styles['SectionHeader']))
    
    features = [
        "<b>Saarthi AI Tutor:</b> A dedicated cognitive AI assistant. Users upload their syllabus (PDF), and Saarthi provides contextually accurate explanations tailored to the user's comprehension level.",
        "<b>Cognitive Profiling:</b> An engine tracking learning accuracy, problem-solving speed, and difficulty level across modules. The cognitive score influences content delivery globally across the platform.",
        "<b>Smart Study Planner:</b> AI parses syllabus documents and generates an optimized 7-day roadmap, prioritizing weak topics for efficient preparation.",
        "<b>Adaptive Mock Tests & Fun Quizzes:</b> Solo and multiplayer battle modes that adjust difficulty dynamically. The engine learns from incorrect answers to refine the student's learning profile.",
        "<b>Smart Revision:</b> Data-driven revision schedules that highlight topics needing the most attention to combat the forgetting curve."
    ]
    
    for feature in features:
        story.append(Paragraph(f"• {feature}", styles['Justify']))
        story.append(Spacer(1, 8))

    # 4. Technical Architecture
    story.append(Paragraph("3. Technical Architecture", styles['SectionHeader']))
    
    arch_intro = "The platform is built using a lightweight, performant stack emphasizing speed, responsive UI, and modular AI processing:"
    story.append(Paragraph(arch_intro, styles['Justify']))
    story.append(Spacer(1, 8))
    
    tech_stack = [
        "<b>Frontend (Presentation Layer):</b> Built with raw HTML5, CSS3, and Vanilla JavaScript. It leverages modern CSS capabilities (Grid, Flexbox, custom variables) to enforce a premium, dark glassmorphic design system seamlessly. Animations provide a highly interactive, responsive experience without heavy frontend framework bloat.",
        "<b>Backend (Logic & API Layer):</b> Powered by a Flask (Python) server handling HTTP requests and RESTful APIs. It implements robust session management and data processing endpoints. Logic modules encapsulate PDF extraction (PyPDF2), keyword processing, and AI simulation logic.",
        "<b>Storage & Authentication:</b> User data is persisted using SQLite (`shikshasetu.db`) ensuring lightweight, serverless relational data storage for users, encrypted passwords (Werkzeug security), and persistent JSON profiles across sessions.",
        "<b>Machine Learning Subsystem:</b> A custom `profile_engine.py` manages a heuristic-based cognitive learning algorithm. It computes performance vectors (accuracy, speed) dynamically post-evaluation."
    ]
    
    for tech in tech_stack:
        story.append(Paragraph(f"• {tech}", styles['Justify']))
        story.append(Spacer(1, 8))

    # 5. Future Roadmap
    story.append(Paragraph("4. Future Roadmap", styles['SectionHeader']))
    future_text = "Future iterations will expand multiplayer battle modes, introduce comprehensive OCR for handwritten notes processing, and integrate deep learning models (LLMs) natively for conversational context-awareness replacing the heuristic reply logic."
    story.append(Paragraph(future_text, styles['Justify']))

    # Build PDF
    doc.build(story)
    return os.path.abspath(filename)

if __name__ == "__main__":
    pdf_path = create_project_vision_pdf()
    print(f"PDF generated successfully at: {pdf_path}")
