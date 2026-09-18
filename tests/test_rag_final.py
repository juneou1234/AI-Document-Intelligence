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

from app.llm import (
    generate_answer
)


PDF_PATH = "documents/sample.pdf"


QUESTIONS = [
    "Why do pigs need energy?",
    "What is bioavailability?",
    "Why is water important for pigs?",
    "What factors affect feed intake?",
]


print("=" * 70)
print("BUILDING DOCUMENT")
print("=" * 70)


elements = extract_all_document_elements(
    PDF_PATH
)

document_units = build_document_units(
    elements
)

print(
    "Total elements:",
    len(elements)
)

print(
    "Total document units:",
    len(document_units)
)


for question in QUESTIONS:

    print("\n")
    print("=" * 70)
    print("QUESTION")
    print("=" * 70)

    print(question)

    print("\nRetrieving...")

    results = retrieve(
        question,
        document_units,
        top_k=3
    )

    if not results:

        print(
            "No retrieval results found."
        )

        continue

    print(
        "Top retrieval score:",
        f"{results[0]['score']:.4f}"
    )

    print(
        "Retrieved results:",
        len(results)
    )

    print("\nTop retrieved sources:")

    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n[{index}]"
        )

        print(
            "Final score:",
            f"{result['score']:.4f}"
        )

        print(
            "Semantic score:",
            f"{result['semantic_score']:.4f}"
        )

        print(
            "Keyword score:",
            f"{result['keyword_score']:.4f}"
        )

        print(
            "Question match:",
            f"{result['question_match_score']:.4f}"
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
            result.get(
                "text",
                ""
            )[:300]
        )

    print(
        "\nBuilding context..."
    )

    context = build_context(
        results,
        document_units,
        max_chars=3000
    )

    print(
        "Context characters:",
        len(context)
    )

    print(
        "\nGenerating answer..."
    )

    answer = generate_answer(
        question,
        context
    )

    print(
        "\nANSWER"
    )

    print(
        "-" * 70
    )

    print(
        answer
    )