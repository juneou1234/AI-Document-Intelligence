import pymupdf
from app.structure import is_heading_span


pdf_path = "documents/sample.pdf"

document = pymupdf.open(pdf_path)

page = document[2]  # Page 3

blocks = page.get_text("dict")["blocks"]

print(f"========== PAGE {page.number + 1} ==========")

for block_number, block in enumerate(blocks, start=1):

    if "lines" not in block:
        continue

    for line in block["lines"]:

        for span in line["spans"]:

            if is_heading_span(span):
                print(
                    f"HEADING | "
                    f"size={span['size']:.1f} | "
                    f"font={span['font']} | "
                    f"text={span['text']!r}"
                )

document.close()