from app.process_document import process_pdf
from app.retrieval_chunks import create_retrieval_chunks
from app.retriever import retrieve


pdf_path = "documents/sample.pdf"

sections = process_pdf(pdf_path)

chunks = create_retrieval_chunks(
    sections,
    max_words=200
)

question = "Why do pigs need energy?"

results = retrieve(
    question,
    chunks,
    top_k=5
)

print(f"Total chunks: {len(chunks)}")

print("\n========================================")
print("QUESTION:")
print(question)
print("========================================")

for rank, result in enumerate(results, start=1):

    print(
        f"\n========== RESULT {rank} =========="
    )

    print(
        f"Score: {result['score']:.4f}"
    )

    print(
        f"Section: {result['section']}"
    )

    print(
        f"Subsection: {result['subsection']}"
    )

    print(
        f"Pages: "
        f"{result['page_start']} - "
        f"{result['page_end']}"
    )

    print(
        f"Content type: "
        f"{result['content_type']}"
    )

    print(
        f"Text: {result['text']}"
    )