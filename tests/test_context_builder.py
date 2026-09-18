from app.document_elements import (
    extract_all_document_elements
)

from app.document_builder import (
    build_document_units
)

from app.retriever import (
    retrieve
)

from app.context_builder import (
    build_context
)


PDF_PATH = "documents/sample.pdf"


elements = extract_all_document_elements(
    PDF_PATH
)

units = build_document_units(
    elements
)


question = "Why do pigs need energy?"


results = retrieve(
    question,
    units,
    top_k=3
)


print("=" * 70)
print("RETRIEVED RESULTS")
print("=" * 70)


for result in results:

    print(
        "\nScore:",
        f"{result['score']:.4f}"
    )

    print(
        "Section:",
        result.get("section")
    )

    print(
        "Topic:",
        result.get("topic")
    )

    print(
        "Question:",
        result.get("question")
    )

    print(
        "Pages:",
        result.get("page_start"),
        "-",
        result.get("page_end")
    )

    print(
        "Text:",
        result.get("text")
    )


print("\n")
print("=" * 70)
print("EXPANDED CONTEXT")
print("=" * 70)


context = build_context(
    results[:1],
    units,
    max_neighbors=3,
    max_units=5
)
print(
    context
)