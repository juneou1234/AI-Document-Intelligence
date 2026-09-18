from app.cleaner import clean_text


def create_sections(blocks):
    """Group cleaned document blocks into section-aware text units."""

    sections = []

    current_section = None
    current_subsection = None
    current_text = []

    current_page_start = None
    current_page_end = None

    def save_current():
        nonlocal current_text
        nonlocal current_page_start
        nonlocal current_page_end

        if current_text and current_section:

            combined_text = " ".join(current_text)

            cleaned_text = clean_text(
                combined_text
            )

            if cleaned_text:
                sections.append({
                    "section": current_section,
                    "subsection": current_subsection,
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                    "content_type": "text",
                    "text": cleaned_text
                })

        current_text = []
        current_page_start = None
        current_page_end = None

    for block in blocks:

        block_type = block["type"]
        text = clean_text(block["text"])

        if not text:
            continue

        page_number = block.get("page_number")

        # Ignore page numbers.
        if block_type == "footer":
            continue

        # Don't mix figure content with normal sections.
        if block_type == "figure":
            continue

        # Keep tables as separate content units.
        if block_type == "table":

            save_current()

            sections.append({
                "section": current_section,
                "subsection": current_subsection,
                "page_start": page_number,
                "page_end": page_number,
                "content_type": "table",
                "text": text
            })

            continue

        # Start a new major section.
        if block_type == "major_heading":

            save_current()

            current_section = text
            current_subsection = None
            current_page_start = page_number
            current_page_end = page_number

        # Start a new subsection.
        elif block_type == "subheading":

            save_current()

            current_subsection = text
            current_page_start = page_number
            current_page_end = page_number

        # Add normal body text.
        elif block_type == "body":

            if current_section is None:
                continue

            current_text.append(text)

            if page_number is not None:

                if current_page_start is None:
                    current_page_start = page_number

                current_page_end = page_number

    save_current()

    return sections