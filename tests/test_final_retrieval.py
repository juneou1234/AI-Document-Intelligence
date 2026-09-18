from app.document_elements import (
    extract_all_document_elements
)

from app.document_builder import (
    build_document_units
)

from app.retriever import (
    retrieve
)


PDF_PATH = "documents/sample.pdf"


QUESTIONS = [
    "Why do pigs need energy?",
    "What are sources of energy for pigs?",
    "What is bioavailability?",
    "Why is water important for pigs?",
    "What factors affect feed intake?",
]


print("=" * 70)
print("DOCUMENT INGESTION")
print("=" * 70)

elements = extract_all_document_elements(
    PDF_PATH
)

print(
    "Total elements:",
    len(elements)
)


document_units = build_document_units(
    elements
)

print(
    "Total semantic units:",
    len(document_units)
)


print("\n")
print("=" * 70)
print("RETRIEVAL TEST")
print("=" * 70)


for question in QUESTIONS:

    print("\n")
    print("=" * 70)

    print(
        "QUESTION:",
        question
    )

    print("=" * 70)

    results = retrieve(
        question,
        document_units,
        top_k=5
    )

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nRESULT {rank}"
        )

        print(
            "Score:",
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
            "Content type:",
            result.get("content_type")
        )

        print(
            "Pages:",
            result.get("page_start"),
            "-",
            result.get("page_end")
        )

        print(
            "Text:",
            result.get("text", "")[:700]
        )