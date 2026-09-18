from app.process_document import process_pdf
from app.retrieval_chunks import create_retrieval_chunks
from app.retriever import retrieve
from app.llm import generate_answer


pdf_path = "documents/sample.pdf"

sections = process_pdf(pdf_path)

chunks = create_retrieval_chunks(
    sections,
    max_words=80
)


question = "Why do pigs need energy?"


results = retrieve(
    question,
    chunks,
    top_k=3
)


answer = generate_answer(
    question,
    results
)


print("\n========================================")
print("QUESTION")
print("========================================")

print(question)


print("\n========================================")
print("ANSWER")
print("========================================")

print(answer)


print("\n========================================")
print("RETRIEVED SOURCES")
print("========================================")

for index, result in enumerate(results, start=1):

    print(
        f"\nSOURCE {index}"
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
        f"{result['page_start']}-"
        f"{result['page_end']}"
    )

    print(
        f"Text: {result['text']}"
    )