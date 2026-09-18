from app.blocks import extract_text_blocks
from app.elements import classify_element
from app.layout import analyze_layout


pdf_path = "documents/sample.pdf"

blocks = extract_text_blocks(
    pdf_path,
    page_number=3
)


for block in blocks:

    block["element_type"] = classify_element(
        block
    )


blocks = analyze_layout(
    blocks
)


print(
    f"Total blocks: {len(blocks)}"
)


for block in blocks:

    print("\n------------------------------")

    print(
        "ELEMENT:",
        block["element_type"]
    )

    print(
        "LAYOUT:",
        block["layout_type"]
    )

    print(
        "TEXT:",
        block["text"]
    )

    print(
        "FONT SIZE:",
        block["max_font_size"]
    )

    print(
        "BBOX:",
        block["bbox"]
    )