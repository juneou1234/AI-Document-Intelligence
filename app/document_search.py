import re

from app.index_store import (
    list_indexed_documents,
    load_index,
)

from app.retriever import (
    build_document_embeddings,
    _retrieve_with_embeddings,
)


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def _normalize_text(
    text
):
    """Normalize text for simple document-level matching."""

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# DOCUMENT PROFILE
# =========================================================

def _build_document_profile(
    units,
    metadata
):
    """
    Build a lightweight text profile for one document.

    The profile contains:
        filename
        section names
        topics
        document text samples
    """

    parts = []

    filename = metadata.get(
        "filename",
        ""
    )

    if filename:
        parts.append(
            filename
        )

    sections = []

    topics = []

    for unit in units:

        section = unit.get(
            "section"
        )

        topic = unit.get(
            "topic"
        )

        if section and section not in sections:
            sections.append(
                section
            )

        if topic and topic not in topics:
            topics.append(
                topic
            )

    parts.extend(
        sections
    )

    parts.extend(
        topics
    )

    # Add a limited amount of document text so the profile
    # remains lightweight.
    for unit in units[:30]:

        text = unit.get(
            "text",
            ""
        )

        if text:
            parts.append(
                text[:500]
            )

    return " ".join(
        parts
    )


# =========================================================
# TOKEN MATCH
# =========================================================

def _token_score(
    query,
    text
):
    """Return simple query-token coverage."""

    query_tokens = set(
        _normalize_text(
            query
        ).split()
    )

    text_tokens = set(
        _normalize_text(
            text
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
# DOCUMENT DISCOVERY
# =========================================================

def rank_documents(
    query,
    documents=None
):
    """
    Rank indexed documents for a question.

    This is a lightweight first-stage filter.
    """

    if documents is None:

        documents = (
            list_indexed_documents()
        )

    ranked = []

    for document in documents:

        try:

            document_id = document.get(
                "document_id"
            )

            if not document_id:
                continue

            units, _, metadata = load_index(
                document_id
            )

            profile = _build_document_profile(
                units,
                metadata
            )

            score = _token_score(
                query,
                profile
            )

            result = document.copy()

            result["document_score"] = (
                score
            )

            ranked.append(
                result
            )

        except Exception:
            continue

    ranked.sort(
        key=lambda item:
        item.get(
            "document_score",
            0.0
        ),
        reverse=True
    )

    return ranked


# =========================================================
# DOCUMENT SEARCH
# =========================================================

def search_all_documents(
    query,
    top_documents=2,
    top_k_per_document=5
):
    """
    Search the most relevant documents and return their
    strongest chunk-level evidence.

    Returns a flat list of retrieval results.
    """

    documents = (
        rank_documents(
            query
        )
    )

    if not documents:
        return []

    selected_documents = documents[
        :top_documents
    ]

    all_results = []

    for document in selected_documents:

        document_id = document.get(
            "document_id"
        )

        if not document_id:
            continue

        try:

            (
                units,
                embeddings,
                metadata
            ) = load_index(
                document_id
            )

        except Exception:
            continue

        # -------------------------------------------------
        # Use the saved embeddings directly.
        # -------------------------------------------------

        if len(embeddings) != len(units):

            continue

        results = _retrieve_with_embeddings(
            query,
            units,
            embeddings,
            top_k=top_k_per_document
        )

        for result in results:

            result["document_id"] = (
                document_id
            )

            result["document_filename"] = (
                metadata.get(
                    "filename"
                )
            )

            result["document_score"] = (
                document.get(
                    "document_score",
                    0.0
                )
            )

            all_results.append(
                result
            )

    # -----------------------------------------------------
    # Final ranking.
    # -----------------------------------------------------

    all_results.sort(
        key=lambda item:
        (
            item.get(
                "score",
                0.0
            )
            + (
                0.05
                * item.get(
                    "document_score",
                    0.0
                )
            )
        ),
        reverse=True
    )

    return all_results