import re


STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "for",
    "of",
    "to",
    "in",
    "on",
    "and",
    "or",
    "why",
    "what",
    "how",
    "when",
    "where",
    "can",
    "may",
    "with",
    "from",
}


def normalize_words(text):
    """Return normalized words from text."""
    return re.findall(
        r"\b[a-zA-Z]+\b",
        text.lower()
    )


def keyword_overlap(query, text):
    """Measure content-word overlap."""

    query_words = {
        word
        for word in normalize_words(query)
        if word not in STOP_WORDS
    }

    text_words = set(
        normalize_words(text)
    )

    if not query_words:
        return 0.0

    return len(
        query_words.intersection(text_words)
    ) / len(query_words)


def question_type(query):
    """Identify basic question intent."""

    query = query.lower().strip()

    if query.startswith("why"):
        return "explanation"

    if query.startswith("what is"):
        return "definition"

    if query.startswith("what are"):
        return "list"

    if (
        query.startswith("how much")
        or query.startswith("how many")
        or "percentage" in query
    ):
        return "quantity"

    return "general"


def quality_score(query, result):
    """Calculate local reranking score."""

    semantic_score = result.get(
        "score",
        0.0
    )

    text = result.get(
        "text",
        ""
    )

    text_lower = text.lower()

    overlap_score = keyword_overlap(
        query,
        text
    )

    intent = question_type(query)

    score = semantic_score * 0.75
    score += overlap_score * 0.15

    content_type = result.get(
        "content_type",
        "text"
    )

    if intent in {
        "explanation",
        "definition",
        "list",
    }:

        if content_type == "text":
            score += 0.08

        elif content_type == "table":
            score -= 0.05

    elif intent == "quantity":

        if content_type == "table":
            score += 0.08

        elif content_type == "text":
            score += 0.02

    if intent == "definition":

        definition_phrases = [
            "is said to be",
            "is defined as",
            "refers to",
            "means",
            "is the",
        ]

        if any(
            phrase in text_lower
            for phrase in definition_phrases
        ):
            score += 0.08

    if text.endswith(
        (".", "?", "!")
    ):
        score += 0.02

    return score


def rerank(query, results, top_k=3):
    """Rerank retrieved candidates locally."""

    reranked = []

    for result in results:

        semantic_score = result.get(
            "score",
            0.0
        )

        updated = result.copy()

        updated["original_score"] = (
            semantic_score
        )

        updated["keyword_score"] = (
            keyword_overlap(
                query,
                result.get("text", "")
            )
        )

        updated["rerank_score"] = (
            quality_score(
                query,
                result
            )
        )

        reranked.append(updated)

    reranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return reranked[:top_k]