import pymupdf


pdf_path = "documents/sample.pdf"

document = pymupdf.open(pdf_path)

page = document[2]  # Page 3

blocks = page.get_text("dict")["blocks"]

print(f"========== PAGE {page.number + 1} ==========")

for block_number, block in enumerate(blocks, start=1):

    if "lines" not in block:
        continue

    text_parts = []

    for line in block["lines"]:
        for span in line["spans"]:
            text = span["text"].strip()

            if text:
                text_parts.append(text)

    text = " ".join(text_parts)

    x0, y0, x1, y1 = block["bbox"]

    print(
        f"\nBLOCK {block_number}"
        f"\nBBOX: ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})"
        f"\nTEXT: {text[:150]}"
    )

document.close()