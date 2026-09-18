def prepare_retrieval_units(document_units):
    """
    Convert semantic document units into records suitable
    for embedding and retrieval.
    """

    retrieval_units = []

    for index, unit in enumerate(
        document_units,
        start=1
    ):

        section = unit.get(
            "section"
        )

        topic = unit.get(
            "topic"
        )

        question = unit.get(
            "question"
        )

        content_type = unit.get(
            "content_type",
            "text"
        )

        page_start = unit.get(
            "page_start"
        )

        page_end = unit.get(
            "page_end"
        )

        text = unit.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        # Build a searchable representation that includes
        # structural metadata without replacing the content.
        parts = []

        if section:
            parts.append(
                f"Section: {section}"
            )

        if topic:
            parts.append(
                f"Topic: {topic}"
            )

        if question:
            parts.append(
                f"Question: {question}"
            )

        parts.append(
            f"Content: {text}"
        )

        searchable_text = "\n".join(
            parts
        )

        retrieval_units.append({
            "id": index,
            "section": section,
            "topic": topic,
            "question": question,
            "content_type": content_type,
            "page_start": page_start,
            "page_end": page_end,
            "text": text,
            "searchable_text": searchable_text
        })

    return retrieval_units