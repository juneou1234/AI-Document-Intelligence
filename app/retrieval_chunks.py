def create_retrieval_chunks(
    sections,
    max_words=200
):
    """
    Create retrieval units that preserve whole text blocks
    whenever possible.

    Long text is split only when it exceeds max_words.
    """

    chunks = []

    for section in sections:

        section_name = (
            section.get("section") or ""
        ).strip()

        text = (
            section.get("text") or ""
        ).strip()

        if not text:
            continue

        # Skip navigation material.
        if section_name.lower() == "table of contents":
            continue

        if (
            not section_name
            and text.lower() == "table of contents"
        ):
            continue

        content_type = section.get(
            "content_type",
            "text"
        )

        words = text.split()

        # Keep short/normal passages intact.
        if len(words) <= max_words:

            chunks.append({
                "section": section.get("section"),
                "subsection": section.get("subsection"),
                "page_start": section.get("page_start"),
                "page_end": section.get("page_end"),
                "content_type": content_type,
                "text": text
            })

            continue

        # Split only long passages.
        start = 0

        while start < len(words):

            end = min(
                start + max_words,
                len(words)
            )

            chunk_text = " ".join(
                words[start:end]
            )

            chunks.append({
                "section": section.get("section"),
                "subsection": section.get("subsection"),
                "page_start": section.get("page_start"),
                "page_end": section.get("page_end"),
                "content_type": content_type,
                "text": chunk_text
            })

            start = end

    return chunks