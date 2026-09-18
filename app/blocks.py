import pymupdf


def extract_text_blocks(pdf_path, page_number):
    """
    Extract text blocks from one PDF page while preserving
    useful layout metadata.

    page_number is 1-based.
    """

    document = pymupdf.open(pdf_path)

    try:
        page = document[page_number - 1]

        page_width = page.rect.width
        page_height = page.rect.height

        raw_blocks = page.get_text("dict")["blocks"]

        blocks = []

        block_number = 0

        for raw_block in raw_blocks:

            # Ignore image-only blocks for now.
            if "lines" not in raw_block:
                continue

            block_text_parts = []
            font_sizes = []
            fonts = []

            for line in raw_block["lines"]:

                for span in line["spans"]:

                    text = span.get("text", "")

                    if not text:
                        continue

                    block_text_parts.append(text)

                    font_sizes.append(
                        span.get("size", 0)
                    )

                    fonts.append(
                        span.get("font", "")
                    )

            text = " ".join(
                block_text_parts
            ).strip()

            if not text:
                continue

            bbox = raw_block.get(
                "bbox",
                (0, 0, 0, 0)
            )

            x0, y0, x1, y1 = bbox

            block_number += 1

            blocks.append({
                "block_number": block_number,
                "page_number": page_number,

                "text": text,

                "bbox": (
                    x0,
                    y0,
                    x1,
                    y1
                ),

                "x_center": (
                    x0 + x1
                ) / 2,

                "y_center": (
                    y0 + y1
                ) / 2,

                "width": x1 - x0,
                "height": y1 - y0,

                "max_font_size": (
                    max(font_sizes)
                    if font_sizes
                    else 0
                ),

                "min_font_size": (
                    min(font_sizes)
                    if font_sizes
                    else 0
                ),

                "fonts": fonts,

                "page_width": page_width,
                "page_height": page_height,
            })

        return blocks

    finally:
        document.close()