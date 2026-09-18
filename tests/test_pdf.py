from app.pdf_reader import extract_pages_from_pdf


pdf_path = "documents/sample.pdf"

pages = extract_pages_from_pdf(pdf_path)

print(f"Total pages: {len(pages)}")

for page in pages[:3]:
    print(f"\n--- Page {page['page_number']} ---")
    print(page["text"][:1000])