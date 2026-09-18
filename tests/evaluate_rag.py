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


TEST_CASES = [
    {
        "question": "Why do pigs need energy?",
        "expected_section": "Nutrient Sources",
        "expected_topic": "Energy",
    },
    {
        "question": "What are sources of energy for pigs?",
        "expected_section": "Nutrient Sources",
        "expected_topic": "Energy",
    },
    {
        "question": "What is bioavailability?",
        "expected_section": "Bioavailability",
        "expected_topic": None,
    },
    {
        "question": "Why is water important for pigs?",
        "expected_section": "Water",
        "expected_topic": None,
    },
    {
        "question": "What factors affect feed intake?",
        "expected_section": "Feed Intake",
        "expected_topic": None,
    },
]


TOP_K = 5


print("=" * 70)
print("RAG RETRIEVAL EVALUATION")
print("=" * 70)


print("\nBuilding document...")


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


total_tests = len(
    TEST_CASES
)

section_hits = 0
topic_hits = 0
top1_hits = 0
topk_hits = 0


print("\n")


for test_number, test_case in enumerate(
    TEST_CASES,
    start=1
):

    question = test_case[
        "question"
    ]

    expected_section = test_case[
        "expected_section"
    ]

    expected_topic = test_case[
        "expected_topic"
    ]

    print("=" * 70)
    print(
        f"TEST {test_number}/{total_tests}"
    )
    print("=" * 70)

    print(
        "Question:",
        question
    )

    print(
        "Expected section:",
        expected_section
    )

    print(
        "Expected topic:",
        expected_topic
    )

    results = retrieve(
        question,
        document_units,
        top_k=TOP_K
    )

    if not results:

        print(
            "\nNO RESULTS ❌"
        )

        continue

    # --------------------------------------------------
    # Evaluate section and topic across top-k.
    # --------------------------------------------------

    section_match_rank = None
    topic_match_rank = None

    for rank, result in enumerate(
        results,
        start=1
    ):

        result_section = result.get(
            "section"
        )

        result_topic = result.get(
            "topic"
        )

        section_matches = (
            result_section
            == expected_section
        )

        if section_matches and section_match_rank is None:

            section_match_rank = rank

        if expected_topic is None:

            topic_matches = True

        else:

            topic_matches = (
                result_topic
                == expected_topic
            )

        if (
            section_matches
            and topic_matches
            and topic_match_rank is None
        ):

            topic_match_rank = rank

    # --------------------------------------------------
    # Metrics.
    # --------------------------------------------------

    if section_match_rank == 1:

        section_hits += 1

    if (
        expected_topic is not None
        and topic_match_rank == 1
    ):

        topic_hits += 1

    elif expected_topic is None and section_match_rank == 1:

        topic_hits += 1

    if topic_match_rank == 1:

        top1_hits += 1

    if topic_match_rank is not None:

        topk_hits += 1

    # --------------------------------------------------
    # Print results.
    # --------------------------------------------------

    print("\nRetrieved results:")

    for rank, result in enumerate(
        results,
        start=1
    ):

        section = result.get(
            "section"
        )

        topic = result.get(
            "topic"
        )

        score = result.get(
            "score",
            0.0
        )

        question_match = result.get(
            "question_match_score",
            0.0
        )

        print(
            f"\n[{rank}] "
            f"Score: {score:.4f}"
        )

        print(
            "Section:",
            section
        )

        print(
            "Topic:",
            topic
        )

        print(
            "Question:",
            result.get("question")
        )

        print(
            "Question match:",
            f"{question_match:.4f}"
        )

        print(
            "Text:",
            result.get(
                "text",
                ""
            )[:250]
        )

    print("\nEvaluation:")

    if section_match_rank is not None:

        print(
            "Section hit at rank:",
            section_match_rank,
            "✅"
        )

    else:

        print(
            "Section hit:",
            "NOT FOUND ❌"
        )

    if topic_match_rank is not None:

        print(
            "Correct section/topic at rank:",
            topic_match_rank,
            "✅"
        )

    else:

        print(
            "Correct section/topic:",
            "NOT FOUND ❌"
        )


# ------------------------------------------------------
# Summary
# ------------------------------------------------------

print("\n")
print("=" * 70)
print("EVALUATION SUMMARY")
print("=" * 70)


section_accuracy = (
    section_hits / total_tests
    if total_tests
    else 0
)

top1_accuracy = (
    top1_hits / total_tests
    if total_tests
    else 0
)

topk_accuracy = (
    topk_hits / total_tests
    if total_tests
    else 0
)


print(
    f"Section accuracy: "
    f"{section_hits}/{total_tests} "
    f"({section_accuracy:.1%})"
)

print(
    f"Correct section/topic @1: "
    f"{top1_hits}/{total_tests} "
    f"({top1_accuracy:.1%})"
)

print(
    f"Correct section/topic @{TOP_K}: "
    f"{topk_hits}/{total_tests} "
    f"({topk_accuracy:.1%})"
)


print("\nDone.")