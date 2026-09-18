import re

import numpy as np

from app.embedder import embed_texts


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def _normalize_text(text):
    """Normalize text for lexical matching."""

    if text is None:
        return ""

    text = str(
        text
    ).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =========================================================
# SEARCHABLE RESULT TEXT
# =========================================================

def _searchable_result_text(
    chunk
):
    """
    Build a searchable representation containing both
    semantic metadata and document text.
    """

    parts = [
        chunk.get(
            "section",
            ""
        ),
        chunk.get(
            "topic",
            ""
        ),
        chunk.get(
            "question",
            ""
        ),
        chunk.get(
            "text",
            ""
        ),
    ]

    return " ".join(
        str(part)
        for part in parts
        if part is not None
        and str(part).strip()
    )


# =========================================================
# QUERY TERMS
# =========================================================

def _query_terms(
    query
):
    """
    Return meaningful content words from a query.
    """

    stop_words = {
        "what",
        "is",
        "are",
        "the",
        "a",
        "an",
        "of",
        "for",
        "do",
        "does",
        "why",
        "how",
        "can",
        "could",
        "would",
        "to",
        "in",
        "on",
        "and",
        "or",
        "with",
        "this",
        "that",
        "these",
        "those",
        "pigs",
        "pig",
    }

    words = _normalize_text(
        query
    ).split()

    return [
        word
        for word in words
        if word not in stop_words
    ]


# =========================================================
# EXACT TERM SCORE
# =========================================================

def _exact_term_score(
    query,
    chunk
):
    """
    Reward exact query terms occurring in the document
    text or metadata.
    """

    terms = _query_terms(
        query
    )

    if not terms:
        return 0.0

    searchable = _normalize_text(
        _searchable_result_text(
            chunk
        )
    )

    if not searchable:
        return 0.0

    matched = 0

    for term in terms:

        if re.search(
            rf"\b{re.escape(term)}\b",
            searchable
        ):

            matched += 1

    return (
        matched
        / len(terms)
    )


# =========================================================
# KEYWORD SCORE
# =========================================================

def _keyword_score(
    query,
    chunk
):
    """
    Calculate lexical overlap between the query and
    the combined searchable chunk representation.
    """

    query_tokens = set(
        _normalize_text(
            query
        ).split()
    )

    text_tokens = set(
        _normalize_text(
            _searchable_result_text(
                chunk
            )
        ).split()
    )

    if not query_tokens:
        return 0.0

    overlap = (
        query_tokens
        & text_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


# =========================================================
# METADATA SCORE
# =========================================================

def _metadata_keyword_score(
    query,
    chunk
):
    """
    Calculate lexical overlap against semantic metadata:

        section
        topic
        question
    """

    query_tokens = set(
        _normalize_text(
            query
        ).split()
    )

    if not query_tokens:
        return 0.0

    metadata_parts = [
        chunk.get(
            "section",
            ""
        ),
        chunk.get(
            "topic",
            ""
        ),
        chunk.get(
            "question",
            ""
        ),
    ]

    metadata_text = " ".join(
        str(part)
        for part in metadata_parts
        if part is not None
        and str(part).strip()
    )

    metadata_tokens = set(
        _normalize_text(
            metadata_text
        ).split()
    )

    overlap = (
        query_tokens
        & metadata_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


# =========================================================
# QUESTION MATCH SCORE
# =========================================================

def _question_match_score(
    query,
    chunk_question
):
    """
    Score similarity to an explicit question stored in
    the source document.
    """

    if not chunk_question:
        return 0.0

    query_norm = _normalize_text(
        query
    )

    question_norm = _normalize_text(
        chunk_question
    )

    if not query_norm or not question_norm:
        return 0.0

    if query_norm == question_norm:
        return 1.0

    query_tokens = set(
        query_norm.split()
    )

    question_tokens = set(
        question_norm.split()
    )

    if not query_tokens:
        return 0.0

    overlap = (
        query_tokens
        & question_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


# =========================================================
# DEFINITION QUESTION DETECTION
# =========================================================

def _is_definition_query(
    query
):
    """
    Detect common definition-style questions.

    Examples:

        What is bioavailability?
        What is digestibility?
        What does ideal protein mean?
        Define bioavailability.
    """

    normalized = _normalize_text(
        query
    )

    patterns = [
        r"^what\s+is\s+.+",
        r"^what\s+are\s+.+",
        r"^what\s+does\s+.+\s+mean$",
        r"^define\s+.+",
        r"^definition\s+of\s+.+",
    ]

    return any(
        re.match(
            pattern,
            normalized
        )
        for pattern in patterns
    )


# =========================================================
# DEFINITION TERM EXTRACTION
# =========================================================

def _definition_terms(
    query
):
    """
    Extract the likely subject term from a definition-style
    question.
    """

    normalized = _normalize_text(
        query
    )

    patterns = [
        r"^what\s+is\s+(.+)$",
        r"^what\s+are\s+(.+)$",
        r"^what\s+does\s+(.+)\s+mean$",
        r"^define\s+(.+)$",
        r"^definition\s+of\s+(.+)$",
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            normalized
        )

        if match:

            subject = match.group(
                1
            ).strip()

            if subject:

                return subject

    return ""


# =========================================================
# DEFINITION STRUCTURE SCORE
# =========================================================

def _definition_structure_score(
    query,
    chunk
):
    """
    Reward chunks whose section/topic heading matches the
    subject of a definition-style question.

    This prevents an incidental mention in a footnote from
    outranking the actual section devoted to the concept.
    """

    if not _is_definition_query(
        query
    ):

        return 0.0

    subject = _definition_terms(
        query
    )

    if not subject:
        return 0.0

    subject_tokens = set(
        _normalize_text(
            subject
        ).split()
    )

    if not subject_tokens:
        return 0.0

    section = _normalize_text(
        chunk.get(
            "section",
            ""
        )
    )

    topic = _normalize_text(
        chunk.get(
            "topic",
            ""
        )
    )

    question = _normalize_text(
        chunk.get(
            "question",
            ""
        )
    )

    section_tokens = set(
        section.split()
    )

    topic_tokens = set(
        topic.split()
    )

    question_tokens = set(
        question.split()
    )

    # -----------------------------------------------------
    # Strongest signal: section contains the subject.
    # -----------------------------------------------------

    if subject_tokens.issubset(
        section_tokens
    ):

        return 1.0

    # -----------------------------------------------------
    # Next strongest: topic contains the subject.
    # -----------------------------------------------------

    if subject_tokens.issubset(
        topic_tokens
    ):

        return 0.85

    # -----------------------------------------------------
    # Explicit document question.
    # -----------------------------------------------------

    if subject_tokens.issubset(
        question_tokens
    ):

        return 0.75

    # -----------------------------------------------------
    # Partial token overlap for multi-word subjects.
    # -----------------------------------------------------

    metadata_tokens = (
        section_tokens
        | topic_tokens
        | question_tokens
    )

    overlap = (
        subject_tokens
        & metadata_tokens
    )

    if overlap:

        return (
            len(overlap)
            / len(subject_tokens)
        ) * 0.60

    return 0.0


# =========================================================
# COSINE SIMILARITY
# =========================================================

def cosine_similarity(
    query_vector,
    document_vectors
):
    """Calculate similarity between one query and documents."""

    query_vector = np.asarray(
        query_vector
    )

    document_vectors = np.asarray(
        document_vectors
    )

    return (
        document_vectors
        @ query_vector
    )


# =========================================================
# DOCUMENT EMBEDDINGS
# =========================================================

def build_document_embeddings(
    chunks
):
    """
    Embed every document unit exactly once.
    """

    if not chunks:

        return np.empty(
            (0, 0),
            dtype=np.float32
        )

    texts = [
        chunk.get(
            "text",
            ""
        )
        for chunk in chunks
    ]

    embeddings = embed_texts(
        texts
    )

    return np.asarray(
        embeddings
    )


# =========================================================
# SINGLE QUERY RETRIEVAL
# =========================================================

def _retrieve_with_embeddings(
    query,
    chunks,
    document_embeddings,
    top_k=5
):
    """
    Retrieve the strongest semantic units.

    Ranking combines:

        semantic similarity
        lexical overlap
        exact term matching
        metadata overlap
        explicit source-question matching
        definition-structure matching
    """

    if not chunks:
        return []

    if len(
        document_embeddings
    ) != len(chunks):

        raise ValueError(
            "Document embeddings count does not "
            "match document chunk count."
        )

    query_embedding = embed_texts(
        [query]
    )[0]

    semantic_scores = cosine_similarity(
        query_embedding,
        document_embeddings
    )

    ranked = []

    for index, chunk in enumerate(
        chunks
    ):

        semantic_score = float(
            semantic_scores[index]
        )

        keyword_score = (
            _keyword_score(
                query,
                chunk
            )
        )

        exact_term_score = (
            _exact_term_score(
                query,
                chunk
            )
        )

        metadata_score = (
            _metadata_keyword_score(
                query,
                chunk
            )
        )

        question_score = (
            _question_match_score(
                query,
                chunk.get(
                    "question"
                )
            )
        )

        definition_structure_score = (
            _definition_structure_score(
                query,
                chunk
            )
        )

        # -------------------------------------------------
        # Final score
        # -------------------------------------------------

        final_score = (
            semantic_score
            + (
                0.05
                * keyword_score
            )
            + (
                0.12
                * exact_term_score
            )
            + (
                0.10
                * metadata_score
            )
            + (
                0.20
                * question_score
            )
            + (
                0.20
                * definition_structure_score
            )
        )

        result = chunk.copy()

        result["score"] = (
            final_score
        )

        result["semantic_score"] = (
            semantic_score
        )

        result["keyword_score"] = (
            keyword_score
        )

        result["exact_term_score"] = (
            exact_term_score
        )

        result["metadata_score"] = (
            metadata_score
        )

        result["question_match_score"] = (
            question_score
        )

        result["definition_structure_score"] = (
            definition_structure_score
        )

        result["retrieval_query"] = (
            query
        )

        ranked.append(
            result
        )

    ranked.sort(
        key=lambda item:
        item["score"],
        reverse=True
    )

    return ranked[
        :top_k
    ]


# =========================================================
# STANDARD RETRIEVAL
# =========================================================

def retrieve(
    query,
    chunks,
    top_k=5,
    document_embeddings=None
):
    """
    Retrieve document units using precomputed embeddings
    whenever available.
    """

    if not chunks:
        return []

    if document_embeddings is None:

        document_embeddings = (
            build_document_embeddings(
                chunks
            )
        )

    return _retrieve_with_embeddings(
        query,
        chunks,
        document_embeddings,
        top_k=top_k
    )


# =========================================================
# MULTI-QUERY RETRIEVAL
# =========================================================

def retrieve_multi_query(
    query,
    chunks,
    sub_queries,
    top_k_per_query=3,
    final_top_k=8,
    document_embeddings=None
):
    """
    Retrieve evidence for multiple focused queries.

    Document embeddings are reused for all sub-queries.
    """

    if not chunks:
        return []

    if document_embeddings is None:

        document_embeddings = (
            build_document_embeddings(
                chunks
            )
        )

    if not sub_queries:

        sub_queries = [
            query
        ]

    merged = {}

    query_results = {}

    # -----------------------------------------------------
    # Retrieve each sub-query.
    # -----------------------------------------------------

    for sub_query in sub_queries:

        results = _retrieve_with_embeddings(
            sub_query,
            chunks,
            document_embeddings,
            top_k=top_k_per_query
        )

        query_results[
            sub_query
        ] = results

        for result in results:

            key = (
                result.get(
                    "section"
                ),
                result.get(
                    "topic"
                ),
                result.get(
                    "question"
                ),
                result.get(
                    "page_start"
                ),
                result.get(
                    "page_end"
                ),
                result.get(
                    "content_type"
                ),
                result.get(
                    "text"
                ),
            )

            if key not in merged:

                merged[key] = result

            else:

                if (
                    result["score"]
                    >
                    merged[key]["score"]
                ):

                    merged[key] = result

    # -----------------------------------------------------
    # Coverage bonus.
    # -----------------------------------------------------

    query_counts = {}

    for results in (
        query_results.values()
    ):

        for result in results:

            key = (
                result.get(
                    "section"
                ),
                result.get(
                    "topic"
                ),
                result.get(
                    "question"
                ),
                result.get(
                    "page_start"
                ),
                result.get(
                    "page_end"
                ),
                result.get(
                    "content_type"
                ),
                result.get(
                    "text"
                ),
            )

            query_counts[key] = (
                query_counts.get(
                    key,
                    0
                )
                + 1
            )

    # -----------------------------------------------------
    # Apply coverage bonus.
    # -----------------------------------------------------

    final_results = []

    for key, result in (
        merged.items()
    ):

        coverage = (
            query_counts.get(
                key,
                1
            )
        )

        result["coverage_count"] = (
            coverage
        )

        if coverage > 1:

            result["score"] += (
                0.03
                * (
                    coverage
                    - 1
                )
            )

        final_results.append(
            result
        )

    # -----------------------------------------------------
    # Final ranking.
    # -----------------------------------------------------

    final_results.sort(
        key=lambda item:
        item["score"],
        reverse=True
    )

    final_results = final_results[
        :final_top_k
    ]

    for rank, result in enumerate(
        final_results,
        start=1
    ):

        result["rank"] = (
            rank
        )

    return final_results