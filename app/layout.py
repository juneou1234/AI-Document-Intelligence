def _is_footer(block):
    """Detect an obvious page-number/footer block."""

    if block.get("element_type") == "footer":
        return True

    text = block.get(
        "text",
        ""
    ).strip()

    if len(text.split()) <= 2:

        page_height = block.get(
            "page_height",
            0
        )

        if page_height:

            return (
                block["bbox"][1]
                > page_height * 0.90
            )

    return False


def analyze_layout(blocks):
    """
    Keep layout analysis intentionally conservative.

    We remove obvious footers and mark figure captions,
    while preserving the PDF's native block order.

    More advanced reading-order handling can be added
    later as a specialized strategy.
    """

    if not blocks:
        return []

    ordered = []

    for block in blocks:

        element_type = block.get(
            "element_type",
            "text"
        )

        if _is_footer(block):

            block["layout_type"] = "ignored"
            continue

        if element_type == "figure_caption":

            block["layout_type"] = "caption"
            continue

        block["layout_type"] = "flow"

        ordered.append(block)

    for index, block in enumerate(
        ordered,
        start=1
    ):

        block["reading_order"] = index

    return ordered