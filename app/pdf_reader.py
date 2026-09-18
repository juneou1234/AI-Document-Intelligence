import pymupdf


def extract_pages_from_pdf(pdf_path):
    """Extract text from a PDF page by page."""
    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text().strip()

        pages.append({
            "page_number": page_number,
            "text": text
        })

    document.close()

    return pages