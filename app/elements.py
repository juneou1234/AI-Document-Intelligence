import re


def _is_bold(block):
    """Return True when a block contains a bold font."""

    return any(
        "bold" in font.lower()
        for font in block.get("fonts", [])
    )


def _is_italic(block):
    """Return True when a block contains an italic font."""

    return any(
        "italic" in font.lower()
        for font in block.get("fonts", [])
    )


def _word_count(text):
    """Return number of words."""

    return len(
        text.split()
    )


def _looks_like_page_number(block):
    """Detect simple footer/page-number blocks."""

    text = block.get(
        "text",
        ""
    ).strip()

    if not re.fullmatch(
        r"[\dIVXivx]+",
        text
    ):
        return False

    page_height = block.get(
        "page_height",
        0
    )

    return (
        _word_count(text) <= 2
        and page_height > 0
        and block.get("bbox", (0, 0, 0, 0))[1]
        > page_height * 0.90
    )


def _looks_like_figure_caption(text):
    """Detect figure captions."""

    return re.match(
        r"^figure\s+\d+",
        text.strip(),
        re.IGNORECASE
    ) is not None


def _looks_like_table_label(text):
    """Detect table labels."""

    return re.match(
        r"^table\s+\d+",
        text.strip(),
        re.IGNORECASE
    ) is not None


def classify_element(block):
    """
    Conservative document-element classifier.

    Classification is based on broad layout and textual
    signals and is intentionally not tied to a specific PDF.
    """

    text = block.get(
        "text",
        ""
    ).strip()

    if not text:
        return "empty"

    font_size = block.get(
        "max_font_size",
        0
    )

    bold = _is_bold(block)
    italic = _is_italic(block)

    if _looks_like_page_number(block):
        return "footer"

    if _looks_like_figure_caption(text):
        return "figure_caption"

    if _looks_like_table_label(text):
        return "table"

    # High-confidence main heading.
    if (
        font_size >= 17
        and bold
        and _word_count(text) <= 12
    ):
        return "heading"

    # Question heading.
    if (
        text.endswith("?")
        and _word_count(text) <= 20
        and (bold or italic)
    ):
        return "question"

    # Conservative topic/subheading.
    if (
        font_size >= 13
        and (bold or italic)
        and _word_count(text) <= 5
    ):
        return "subheading"

    return "text"