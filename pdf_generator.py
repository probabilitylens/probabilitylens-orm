from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

def generate_pdf(filename, data):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("PROBABILITYLENS — OIL RISK MONITOR", styles["Title"]))

    elements.append(Paragraph("EXECUTIVE SUMMARY", styles["Heading2"]))
    elements.append(Paragraph(data.get("summary", ""), styles["BodyText"]))

    table_data = [["Factor", "Score", "Contribution", "Interpretation"]]

    for row in data.get("signals", []):
        table_data.append(list(row.values()))

    elements.append(Table(table_data))

    doc.build(elements)
