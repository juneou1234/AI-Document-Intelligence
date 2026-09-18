from app.blocks import extract_text_blocks
from app.structure import classify_block
from app.chunker import create_sections


pdf_path = "documents/sample.pdf"

blocks = extract_text_blocks(
    pdf_path,
    page_number=3
)

classified_blocks = []

for index, block in enumerate(blocks):

    next_block = None

    if index + 1 < len(blocks):
        next_block = blocks[index + 1]

    block["type"] = classify_block(
        block,
        next_block
    )

    classified_blocks.append(block)


sections = create_sections(classified_blocks)

print(f"Total sections: {len(sections)}")

for index, section in enumerate(sections, start=1):

    print(f"\n========== SECTION {index} ==========")
    print(f"Section: {section['section']}")
    print(f"Subsection: {section['subsection']}")
    print(f"Text: {section['text'][:500]}")