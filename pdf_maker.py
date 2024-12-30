from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, darkgray

class EssayBuilder:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=letter,
                                     rightMargin=72, leftMargin=72,
                                     topMargin=72, bottomMargin=18)
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        
        # Custom style for sub-subtitle
        self.styles.add(ParagraphStyle(
            name='SubSubtitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=black,
            spaceAfter=6
        ))
        
        self.content = []

    def add_title(self, title):
        self.content.append(Paragraph(title, self.styles['Title']))
        self.content.append(Spacer(1, 16))

    def add_subtitle(self, subtitle):
        self.content.append(Paragraph(subtitle, self.styles['Heading2']))
        self.content.append(Spacer(1, 12))

    def add_sub_subtitle(self, sub_subtitle):
        self.content.append(Paragraph(sub_subtitle, self.styles['SubSubtitle']))
        self.content.append(Spacer(1, 6))

    def add_paragraph(self, text):
        self.content.append(Paragraph(text, self.styles['Justify']))
        self.content.append(Spacer(1, 12))

    def build(self):
        self.doc.build(self.content)
def main():
    # Example usage
    builder = EssayBuilder('multilevel_essay.pdf')

    # Adding content with multiple levels of headings
    builder.add_title("Comprehensive Guide to Python Programming")

    builder.add_subtitle("1. Introduction to Python")
    builder.add_paragraph("Python is a versatile and powerful programming language...")

    builder.add_sub_subtitle("1.1 History of Python")
    builder.add_paragraph("Python was created by Guido van Rossum in the late 1980s...")

    builder.add_sub_subtitle("1.2 Key Features of Python")
    builder.add_paragraph("Python is known for its simplicity and readability...")

    builder.add_subtitle("2. Basic Python Syntax")
    builder.add_paragraph("Let's dive into the fundamental syntax of Python...")

    builder.add_sub_subtitle("2.1 Variables and Data Types")
    builder.add_paragraph("In Python, you don't need to declare variable types explicitly...")

    builder.add_sub_subtitle("2.2 Control Structures")
    builder.add_paragraph("Python supports various control structures like if-else statements and loops...")

    # Build the PDF
    builder.build()

    print("Essay saved as 'multilevel_essay.pdf'")

if __name__ == "__main__":
    main()