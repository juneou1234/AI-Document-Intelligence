from app.process_document import process_pdf


pdf_path = "documents/sample.pdf"

sections = process_pdf(pdf_path)

print(f"Total sections: {len(sections)}")

for index, section in enumerate(sections, start=1):

    print(f"\n========== SECTION {index} ==========")

    print(f"Section: {section['section']}")
    print(f"Subsection: {section['subsection']}")
    print(
        f"Pages: "
        f"{section['page_start']} - "
        f"{section['page_end']}"
    )

    print(f"Text: {section['text'][:300]}")