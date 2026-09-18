from app.document_elements import (
    extract_all_document_elements
)

from app.document_builder import (
    build_document_units
)


PDF_PATH = "documents/swine_diet.pdf"


print("=" * 70)
print("SEMANTIC CHUNKING DIAGNOSTIC")
print("=" * 70)

print(
    "\nPDF:",
    PDF_PATH
)


print(
    "\nExtracting document elements..."
)

elements = extract_all_document_elements(
    PDF_PATH
)

print(
    "Total elements:",
    len(elements)
)


print(
    "\nBuilding semantic units..."
)

units = build_document_units(
    elements
)

print(
    "Total semantic units:",
    len(units)
)


for index, unit in enumerate(
    units,
    start=1
):

    text = unit.get(
        "text",
        ""
    )

    print("\n")
    print("=" * 70)
    print(
        f"UNIT {index}"
    )
    print("=" * 70)

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
        "Characters:",
        len(text)
    )

    print(
        "Text preview:"
    )

    print(
        text[:500]
    )


print("\n")
print("=" * 70)
print("UNIT SIZE SUMMARY")
print("=" * 70)


sizes = [
    len(
        unit.get(
            "text",
            ""
        )
    )
    for unit in units
]


if sizes:

    print(
        "Smallest unit:",
        min(sizes),
        "characters"
    )

    print(
        "Largest unit:",
        max(sizes),
        "characters"
    )

    print(
        "Average unit:",
        round(
            sum(sizes) / len(sizes)
        ),
        "characters"
    )


large_units = [
    (index + 1, size)
    for index, size in enumerate(
        sizes
    )
    if size > 3000
]


print(
    "\nUnits over 3,000 characters:",
    len(large_units)
)


for index, size in large_units:

    print(
        f"UNIT {index}: "
        f"{size} characters"
    )


print("\nDone.")