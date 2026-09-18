import pymupdf

from app.blocks import extract_text_blocks
from app.structure import classify_block
from app.chunker import create_sections


def process_pdf(pdf_path):
    """Process an entire PDF into section-aware document data."""

    document = pymupdf.open(pdf_path)

    all_blocks = []

    for page_number in range(1, len(document) + 1):

        blocks = extract_text_blocks(
            pdf_path,
            page_number
        )

        for index, block in enumerate(blocks):

            next_block = None

            if index + 1 < len(blocks):
                next_block = blocks[index + 1]

            block["type"] = classify_block(
                block,
                next_block
            )

            block["page_number"] = page_number

            all_blocks.append(block)

    document.close()

    sections = create_sections(all_blocks)

    return sections