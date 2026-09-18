import os

from dotenv import load_dotenv
from google import genai


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set."
    )


# =========================================================
# CLIENT
# =========================================================

client = genai.Client(
    api_key=api_key
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "gemini-3.6-flash"

MAX_OUTPUT_TOKENS = 500


# =========================================================
# ANSWER GENERATION
# =========================================================

def generate_answer(
    question,
    context
):
    """
    Generate a concise, complete, grounded answer.

    Only information contained in the supplied document
    context may be used.
    """

    if not context:
        return (
            "I could not find enough information "
            "in the document to answer this question."
        )

    prompt = f"""
Answer the user's question using ONLY the document evidence below.

Rules:
- Answer every part of the question that the document supports.
- Do not reject the whole question because one part is missing.
- Do not use outside knowledge.
- Do not invent, estimate, or calculate missing values.
- Preserve numerical values exactly as written.
- Distinguish between nutrient sources and nutrient amounts.
- If a requested value is not stated, say:
  "The document does not specify this."
- Use the terminology used by the document.
- If the user's stage name differs from the document's terminology,
  explain the document's terminology briefly instead of inventing
  an exact equivalence.
- Keep the answer complete but concise.
- Use short headings or bullets for multi-part questions.
- Finish the entire answer. Do not stop midway through a list or table.
- Do not mention retrieval, embeddings, context, prompts, or internal
  system behavior.

Question:
{question}

Document evidence:
{context}

Final answer:
"""

    try:

        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            generation_config={
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "thinking_level": "minimal",
            },
        )

    except Exception as error:

        raise RuntimeError(
            "Gemini request failed: "
            f"{error}"
        ) from error

    answer = (
        interaction.output_text
        or ""
    ).strip()

    if answer:
        return answer

    if interaction.status == "incomplete":
        return (
            "The model did not finish generating "
            "the answer. Please try the question again."
        )

    raise RuntimeError(
        "Gemini returned no answer. "
        f"Status: {interaction.status}"
    )