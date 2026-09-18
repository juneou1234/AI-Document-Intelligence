from app.document_elements import (
    extract_document_elements
)


pdf_path = "documents/sample.pdf"

blocks = extract_document_elements(
    pdf_path,
    page_number=3
)


print(
    f"Total elements: {len(blocks)}"
)


for block in blocks:

    print("\n------------------------------")

    print(
        "ORDER:",
        block.get("reading_order")
    )

    print(
        "ELEMENT:",
        block.get("element_type")
    )

    print(
        "LAYOUT:",
        block.get("layout_type")
    )

    print(
        "TEXT:",
        block.get("text")
    )

    print(
        "X:",
        block.get("x_center")
    )

    print(
        "Y:",
        block.get("y_center")
    )