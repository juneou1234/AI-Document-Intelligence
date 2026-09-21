# =========================================================
# DOCUMENT OVERVIEW HELPERS
# =========================================================


def build_section_outline(
    units,
    max_sections=12
):
    """
    Return unique section names in document order.
    """

    outline = []
    seen = set()

    for unit in units or []:

        section = unit.get(
            "section"
        )

        if not section:
            continue

        section = str(
            section
        ).strip()

        if not section:
            continue

        key = section.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        outline.append(
            section
        )

        if len(outline) >= max_sections:
            break

    return outline


def build_suggested_questions(
    units,
    max_questions=6
):
    """
    Turn document questions into clickable suggestions.
    """

    suggestions = []
    seen = set()

    for unit in units or []:

        question = unit.get(
            "question"
        )

        if not question:
            continue

        question = str(
            question
        ).strip()

        if len(question) < 12:
            continue

        if not question.endswith(
            "?"
        ):

            question = (
                question.rstrip(
                    " ."
                )
                + "?"
            )

        key = question.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        suggestions.append(
            question
        )

        if len(suggestions) >= max_questions:
            break

    return suggestions


def count_pages(
    units
):
    """Return the highest page number found in the units."""

    page_end = 0

    for unit in units or []:

        value = unit.get(
            "page_end"
        )

        if value is None:

            value = unit.get(
                "page_start"
            )

        try:

            page_end = max(
                page_end,
                int(value)
            )

        except (
            TypeError,
            ValueError
        ):

            continue

    return page_end
