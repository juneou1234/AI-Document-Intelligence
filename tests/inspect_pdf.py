from app.pdf_reader import extract_pages_from_pdf


pdf_path = "documents/sample.pdf"

pages = extract_pages_from_pdf(pdf_path)

for page in pages[:3]:
    print(f"\n========== PAGE {page['page_number']} ==========")

    for line_number, line in enumerate(page["text"].splitlines(), start=1):
        print(f"{line_number:03}: {line}")