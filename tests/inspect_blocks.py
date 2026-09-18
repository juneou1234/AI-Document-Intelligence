import pymupdf


pdf_path = "documents/sample.pdf"

document = pymupdf.open(pdf_path)

page = document[2]  # Page 3

blocks = page.get_text("dict")["blocks"]

for block_number, block in enumerate(blocks, start=1):

    if "lines" not in block:
        continue

    print(f"\n========== BLOCK {block_number} ==========")

    for line in block["lines"]:

        for span in line["spans"]:

            print(
                f"text={span['text']!r} | "
                f"size={span['size']:.1f} | "
                f"font={span['font']} | "
                f"bbox={span['bbox']}"
            )

document.close()