from app.document_elements import (
    extract_all_document_elements
)


PDF_PATH = "documents/swine_diet.pdf"


print("=" * 70)
print("RAW ELEMENT DIAGNOSTIC")
print("=" * 70)

print(
    "\nPDF:",
    PDF_PATH
)


elements = extract_all_document_elements(
    PDF_PATH
)


print(
    "\nTotal elements:",
    len(elements)
)


for index, element in enumerate(
    elements,
    start=1
):

    print("\n")
    print("-" * 70)
    print(
        f"ELEMENT {index}"
    )
    print("-" * 70)

    print(
        "Type:",
        element.get(
            "element_type"
        )
    )

    print(
        "Layout:",
        element.get(
            "layout"
        )
    )

    print(
        "Page:",
        element.get(
            "page_number"
        )
    )

    print(
        "X:",
        element.get(
            "x"
        )
    )

    print(
        "Y:",
        element.get(
            "y"
        )
    )

    print(
        "Text:"
    )

    print(
        element.get(
            "text",
            ""
        )
    )


print("\nDone.")