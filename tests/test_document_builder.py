from app.document_elements import (
    extract_all_document_elements
)

from app.document_builder import (
    build_document_units
)


pdf_path = "documents/sample.pdf"


elements = extract_all_document_elements(
    pdf_path
)


units = build_document_units(
    elements
)


print(
    "Total elements:",
    len(elements)
)

print(
    "Total document units:",
    len(units)
)


for index, unit in enumerate(
    units[:20],
    start=1
):

    print(
        "\n========================================"
    )

    print(
        f"UNIT {index}"
    )

    print(
        "========================================"
    )

    print(
        "Section:",
        unit.get("section")
    )

    print(
        "Topic:",
        unit.get("topic")
    )

    print(
        "Question:",
        unit.get("question")
    )

    print(
        "Content type:",
        unit.get("content_type")
    )

    print(
        "Pages:",
        unit.get("page_start"),
        "-",
        unit.get("page_end")
    )

    print(
        "Text:",
        unit.get("text", "")[:700]
    )