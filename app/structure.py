def is_figure_block(block):
    """Detect blocks that likely belong to a figure."""

    text = block["text"].strip()

    if not text:
        return False

    y = block["y_center"]
    page_height = block["page_height"]
    font_size = block["max_font_size"]

    fonts = [
        font.lower()
        for font in block["fonts"]
    ]

    is_bold = any("bold" in font for font in fonts)

    # This is a first-pass rule for the figure region
    # observed in the sample document.
    if (
        13 <= font_size <= 15
        and is_bold
        and page_height * 0.45 < y < page_height * 0.90
    ):
        return True

    return False


def is_table_block(block):
    """Detect blocks that appear to begin a table."""

    text = block["text"].strip()

    if not text:
        return False

    if text.lower().startswith("table "):
        return True

    return False


def classify_block(block, next_block=None):
    """Classify a prepared PDF text block."""

    text = block["text"].strip()

    if not text:
        return "empty"

    font_size = block["max_font_size"]
    y_center = block["y_center"]
    page_height = block["page_height"]

    fonts = [
        font.lower()
        for font in block["fonts"]
    ]

    is_bold = any("bold" in font for font in fonts)
    is_italic = any("italic" in font for font in fonts)

    # Footer / page number.
    if y_center > page_height * 0.95:
        return "footer"

    # Figure content.
    if is_figure_block(block):
        return "figure"

    # Table heading/content marker.
    if is_table_block(block):
        return "table"

    # Major section heading.
    if font_size >= 17 and is_bold:
        return "major_heading"

    # Subsection heading.
    if (
        13 <= font_size < 17
        and (is_bold or is_italic)
        and len(text.split()) <= 5
    ):
        if next_block is not None:

            next_text = next_block["text"].strip()
            next_font_size = next_block["max_font_size"]
            next_y = next_block["y_center"]

            vertical_gap = next_y - y_center

            next_is_body_sized = next_font_size <= 11
            next_is_close = 0 < vertical_gap < 50

            if next_text and next_is_body_sized and next_is_close:
                return "subheading"

    return "body"