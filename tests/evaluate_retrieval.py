from app.process_document import process_pdf
from app.retrieval_chunks import create_retrieval_chunks
from app.retriever import retrieve
from app.reranker import rerank


PDF_PATH = "documents/sample.pdf"


QUESTIONS = [
    "Why do pigs need energy?",
    "What are sources of energy for pigs?",
    "What is bioavailability?",
    "Why is water important for pigs?",
    "What factors affect feed intake?",
]


sections = process_pdf(PDF_PATH)

chunks = create_retrieval_chunks(
    sections,
    max_words=80
)


for question in QUESTIONS:

    print("\n")
    print("=" * 70)
    print("QUESTION:")
    print(question)
    print("=" * 70)

    # Retrieve more candidates than we ultimately need.
    candidates = retrieve(
        question,
        chunks,
        top_k=10
    )

    results = rerank(
        question,
        candidates,
        top_k=3
    )

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nRESULT {rank}"
        )

        print(
            f"Original score: "
            f"{result['original_score']:.4f}"
        )

        print(
            f"Keyword score: "
            f"{result['keyword_score']:.4f}"
        )

        print(
            f"Rerank score: "
            f"{result['rerank_score']:.4f}"
        )

        print(
            f"Section: "
            f"{result['section']}"
        )

        print(
            f"Subsection: "
            f"{result['subsection']}"
        )

        print(
            f"Pages: "
            f"{result['page_start']}-"
            f"{result['page_end']}"
        )

        print(
            f"Content type: "
            f"{result['content_type']}"
        )

        print(
            f"Text: "
            f"{result['text'][:400]}"
        )