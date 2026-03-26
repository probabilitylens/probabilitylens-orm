from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def render_pdf(report):
    doc=SimpleDocTemplate("report.pdf")
    s=getSampleStyleSheet()
    doc.build([Paragraph(str(report),s["BodyText"])])
    return "report.pdf"
