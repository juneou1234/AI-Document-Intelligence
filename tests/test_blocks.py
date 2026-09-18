from app.blocks import extract_text_blocks
from app.structure import classify_block


pdf_path = "documents/sample.pdf"

blocks = extract_text_blocks(
    pdf_path,
    page_number=3
)

for index, block in enumerate(blocks):

    next_block = None

    if index + 1 < len(blocks):
        next_block = blocks[index + 1]

    classification = classify_block(
        block,
        next_block
    )

    print(
        f"\nBLOCK {block['block_number']}"
        f"\nTYPE: {classification}"
        f"\nTEXT: {block['text'][:120]}"
        f"\nX CENTER: {block['x_center']:.1f}"
        f"\nY CENTER: {block['y_center']:.1f}"
    )