from ai.pdf_parser import get_pdf_text

path = r"C:\Users\moosa\Documents\Djangos\Pdf Media\fyp\Technical_Report_Writing.pdf"

text = get_pdf_text(path)

print(text[:3000])