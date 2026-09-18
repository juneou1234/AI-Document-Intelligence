import re


# =========================================================
# CONFIGURATION
# =========================================================

MAX_TEXT_CHARS = 2200


# =========================================================
# TEXT CLEANING
# =========================================================

def _clean_text(text):
    """Clean common PDF extraction artifacts."""

    if not text:
        return ""

    text = re.sub(
        r"(?<=\w)-\s+(?=\w)",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    replacements = {
        r"\bH\s+ow\b": "How",
        r"\bW\s+hat\b": "What",
        r"\bA\s+re\b": "Are",
        r"\bD\s+oes\b": "Does",
        r"\bC\s+an\b": "Can",
        r"\bW\s+here\b": "Where",
        r"\bW\s+hen\b": "When",
        r"\bW\s+hy\b": "Why",
        r"\bI\s+s\b": "Is",
        r"\bT\s+he\b": "The",
    }

    for pattern, replacement in replacements.items():

        text = re.sub(
            pattern,
            replacement,
            text
        )

    return _remove_simple_duplicate_phrase(
        text
    ).strip()


def _remove_simple_duplicate_phrase(text):
    """Remove simple duplicated phrases created by PDF extraction."""

    if not text:
        return ""

    words = text.split()

    if len(words) < 2:
        return text

    if len(words) % 2 != 0:
        return text

    midpoint = len(words) // 2

    first_half = words[:midpoint]
    second_half = words[midpoint:]

    if first_half == second_half:

        return " ".join(
            first_half
        )

    return text


# =========================================================
# BASIC TESTS
# =========================================================

def _ends_sentence(text):
    """Return True if text appears to end naturally."""

    if not text:
        return True

    return text.rstrip().endswith(
        (
            ".",
            "?",
            "!",
            ":",
            ";",
            '"',
            "'",
            ")",
            "]",
        )
    )


def _looks_like_question(text):
    """Detect question-style text."""

    if not text:
        return False

    cleaned = _clean_text(
        text
    )

    if cleaned.endswith("?"):
        return len(cleaned.split()) <= 35

    question_starters = (
        "how ",
        "what ",
        "why ",
        "when ",
        "where ",
        "which ",
        "who ",
        "can ",
        "does ",
        "do ",
        "are ",
        "is ",
        "should ",
        "would ",
    )

    return (
        cleaned.lower().startswith(
            question_starters
        )
        and len(cleaned.split()) <= 25
    )


# =========================================================
# TOC DETECTION
# =========================================================

def _looks_like_toc_text(text):
    """Detect likely Table of Contents text."""

    if not text:
        return False

    dot_count = text.count(".")

    page_number_matches = re.findall(
        r"(?:^|\s)\d{1,3}(?:\s|$)",
        text
    )

    return (
        dot_count >= 8
        and len(page_number_matches) >= 3
    )


def _is_toc_element(element):
    """Detect Table of Contents material."""

    text = _clean_text(
        element.get(
            "text",
            ""
        )
    )

    if not text:
        return False

    if text.lower() == "table of contents":
        return True

    return _looks_like_toc_text(
        text
    )


# =========================================================
# NUMBERED SECTION DETECTION
# =========================================================

def _parse_numbered_lead(text):
    """
    Parse a numbered lead.

    Examples:

        1. Energy -- from carbohydrates...
        2. Protein -- from soybean meal...

    Returns:
        {
            "number": 1,
            "label": "Energy",
            "remainder": "from carbohydrates..."
        }

    or None.
    """

    if not text:
        return None

    match = re.match(
        r"^\s*(\d+)\.\s+(.+?)\s+(--|–|-)\s+(.+)$",
        text
    )

    if not match:
        return None

    number = int(
        match.group(1)
    )

    label = _clean_text(
        match.group(2)
    )

    remainder = _clean_text(
        match.group(4)
    )

    if not label or not remainder:
        return None

    if len(label.split()) > 6:
        return None

    return {
        "number": number,
        "label": label,
        "remainder": remainder,
    }


def _looks_like_numbered_list_item(text):
    """
    Detect numbered prose/list items.

    Examples:

        1. Growth: Mainly...
        2. Maintenance: Energy...
        5. Fattening: Formation...
    """

    if not text:
        return False

    return bool(
        re.match(
            r"^\s*\d+\.\s+",
            text
        )
    )


def _looks_like_numbered_section(text):
    """
    A numbered section is only inferred when it has a short
    label followed by a dash-based explanation.

    This prevents numbered prose lists from becoming sections.
    """

    parsed = _parse_numbered_lead(
        text
    )

    if not parsed:
        return False

    return True


# =========================================================
# TITLE / SUBHEADING DETECTION
# =========================================================

def _has_sentence_punctuation(text):
    """Check for normal sentence-ending punctuation."""

    if not text:
        return False

    return bool(
        re.search(
            r"[.!?]$",
            text.strip()
        )
    )


def _looks_numeric_data(text):
    """Detect table-like numeric content."""

    if not text:
        return False

    words = text.split()

    if not words:
        return False

    numeric_tokens = re.findall(
        r"\d+(?:\.\d+)?%?",
        text
    )

    if (
        len(numeric_tokens) >= 2
        and len(numeric_tokens)
        >= max(
            2,
            len(words) // 2
        )
    ):
        return True

    return False


def _title_case_ratio(text):
    """Return approximate title-case ratio."""

    words = [
        word.strip(
            ".,:;()[]{}\"'"
        )
        for word in text.split()
        if word.strip(
            ".,:;()[]{}\"'"
        )
    ]

    if not words:
        return 0.0

    meaningful = [
        word
        for word in words
        if re.search(
            r"[A-Za-z]",
            word
        )
    ]

    if not meaningful:
        return 0.0

    capitalized = sum(
        word[0].isupper()
        for word in meaningful
        if word
    )

    return (
        capitalized
        / len(meaningful)
    )


def _looks_like_title(text):
    """
    Detect a short title-like line.

    Designed to work even when the PDF extractor classified
    the element simply as text.
    """

    text = _clean_text(
        text
    )

    if not text:
        return False

    words = text.split()

    if len(words) > 9:
        return False

    if _looks_numeric_data(
        text
    ):
        return False

    if _looks_like_question(
        text
    ):
        return False

    if _looks_like_numbered_section(
        text
    ):
        return True

    # Normal sentences should not become titles.
    if _has_sentence_punctuation(
        text
    ):
        return False

    # Strong title case signal.
    if _title_case_ratio(
        text
    ) >= 0.65:
        return True

    # ALL CAPS.
    letters = [
        char
        for char in text
        if char.isalpha()
    ]

    if letters:

        uppercase_ratio = (
            sum(
                char.isupper()
                for char in letters
            )
            / len(letters)
        )

        if uppercase_ratio >= 0.75:
            return True

    # Common title-like patterns such as:
    #
    # Farm Mixed Pig Rations (lbs.)
    # Energy Sources for Swine
    # Feed Protein Levels Required by Swine
    #
    title_keywords = (
        "sources",
        "rations",
        "levels",
        "requirements",
        "required",
        "nutrients",
        "feeding",
        "intake",
        "consumption",
        "mixture",
        "protein",
        "energy",
        "water",
        "vitamins",
        "minerals",
        "pig",
        "pigs",
        "swine",
    )

    lowered = text.lower()

    keyword_hits = sum(
        keyword in lowered
        for keyword in title_keywords
    )

    if (
        keyword_hits >= 1
        and len(words) <= 7
    ):
        return True

    return False


# =========================================================
# STRUCTURAL ROLE INFERENCE
# =========================================================

def _infer_element_role(element):
    """
    Infer structural role while respecting explicit
    classifications.
    """

    explicit_type = element.get(
        "element_type"
    )

    text = _clean_text(
        element.get(
            "text",
            ""
        )
    )

    if not text:
        return "empty"

    # Strong explicit classifications.
    if explicit_type in {
        "footer",
        "figure_caption",
        "table",
        "heading",
        "question",
    }:
        return explicit_type

    if _looks_like_question(
        text
    ):
        return "question"

    if _looks_like_numbered_section(
        text
    ):
        return "numbered_section"

    if (
        explicit_type == "subheading"
        or _looks_like_title(
            text
        )
    ):
        return "subheading"

    return "text"


# =========================================================
# HEADING FRAGMENTS
# =========================================================

def _vertical_gap(a, b):
    """Return vertical gap where bbox data exists."""

    a_bbox = a.get(
        "bbox"
    )

    b_bbox = b.get(
        "bbox"
    )

    if not a_bbox or not b_bbox:
        return 0

    _, ay0, _, ay1 = a_bbox
    _, by0, _, by1 = b_bbox

    if ay1 <= by0:
        return by0 - ay1

    if by1 <= ay0:
        return ay0 - by1

    return 0


def _horizontal_distance(a, b):
    """Compare left edges when bbox information exists."""

    a_bbox = a.get(
        "bbox"
    )

    b_bbox = b.get(
        "bbox"
    )

    if not a_bbox or not b_bbox:
        return 0

    return abs(
        a_bbox[0]
        - b_bbox[0]
    )


def _can_join_heading_fragments(
    previous,
    current
):
    """Join clearly fragmented heading elements."""

    previous_role = _infer_element_role(
        previous
    )

    current_role = _infer_element_role(
        current
    )

    if previous_role not in {
        "heading",
        "subheading",
    }:
        return False

    if current_role not in {
        "heading",
        "subheading",
    }:
        return False

    previous_page = previous.get(
        "page_number"
    )

    current_page = current.get(
        "page_number"
    )

    if (
        previous_page is not None
        and current_page is not None
        and previous_page != current_page
    ):
        return False

    previous_text = _clean_text(
        previous.get(
            "text",
            ""
        )
    )

    current_text = _clean_text(
        current.get(
            "text",
            ""
        )
    )

    if not previous_text or not current_text:
        return False

    if (
        _vertical_gap(
            previous,
            current
        )
        > 30
    ):
        return False

    if (
        _horizontal_distance(
            previous,
            current
        )
        > 60
    ):
        return False

    if len(
        current_text.split()
    ) > 5:
        return False

    return True


def _merge_heading_fragments(elements):
    """Merge obvious broken heading fragments."""

    merged = []

    for element in elements:

        current = element.copy()

        current["text"] = _clean_text(
            current.get(
                "text",
                ""
            )
        )

        if not current["text"]:
            continue

        if not merged:

            merged.append(
                current
            )

            continue

        previous = merged[-1]

        if _can_join_heading_fragments(
            previous,
            current
        ):

            previous["text"] = _clean_text(
                previous["text"]
                + " "
                + current["text"]
            )

            continue

        merged.append(
            current
        )

    return merged


# =========================================================
# TEXT CONTINUATION
# =========================================================

def _looks_like_continuation(text):
    """Detect likely continuation of previous prose."""

    if not text:
        return False

    match = re.match(
        r"([A-Za-z]+)",
        text.strip()
    )

    if not match:
        return False

    word = match.group(1).lower()

    continuation_words = {
        "and",
        "or",
        "but",
        "because",
        "which",
        "that",
        "while",
        "when",
        "where",
        "if",
        "than",
        "as",
        "so",
        "thus",
        "this",
        "these",
        "those",
        "the",
        "a",
        "an",
        "lactation",
    }

    return (
        word in continuation_words
        or word[0].islower()
    )


def _same_context(a, b):
    """Check semantic context compatibility."""

    return (
        a.get("section")
        == b.get("section")
        and
        a.get("topic")
        == b.get("topic")
        and
        a.get("question")
        == b.get("question")
    )


def _merge_text_blocks(blocks):
    """Merge compatible body text."""

    merged = []

    for block in blocks:

        current = block.copy()

        current["text"] = _clean_text(
            current.get(
                "text",
                ""
            )
        )

        if not current["text"]:
            continue

        if not merged:

            merged.append(
                current
            )

            continue

        previous = merged[-1]

        if not _same_context(
            previous,
            current
        ):
            merged.append(
                current
            )
            continue

        previous_text = previous[
            "text"
        ].rstrip()

        current_text = current[
            "text"
        ].lstrip()

        if (
            not _ends_sentence(
                previous_text
            )
            and _looks_like_continuation(
                current_text
            )
        ):

            previous["text"] = (
                previous_text
                + " "
                + current_text
            )

            if current.get(
                "page_end"
            ) is not None:

                previous["page_end"] = (
                    current["page_end"]
                )

            continue

        merged.append(
            current
        )

    return merged


# =========================================================
# LONG TEXT FALLBACK
# =========================================================

def _split_long_text(
    text,
    max_chars=MAX_TEXT_CHARS
):
    """
    Split oversized units using sentence boundaries.

    This is a safety fallback for PDFs that lack clear
    structural headings.
    """

    text = _clean_text(
        text
    )

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    parts = []

    current = []
    current_length = 0

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        sentence_length = len(
            sentence
        )

        separator = (
            1
            if current
            else 0
        )

        if (
            current
            and
            current_length
            + separator
            + sentence_length
            > max_chars
        ):

            parts.append(
                " ".join(
                    current
                )
            )

            current = [
                sentence
            ]

            current_length = (
                sentence_length
            )

            continue

        current.append(
            sentence
        )

        current_length += (
            separator
            + sentence_length
        )

    if current:

        parts.append(
            " ".join(
                current
            )
        )

    return parts


# =========================================================
# DOCUMENT BUILDER
# =========================================================

def build_document_units(elements):
    """
    Convert extracted document elements into retrieval units.

    The builder supports:

    - explicit headings
    - explicit questions
    - explicit tables
    - inferred headings
    - numbered semantic sections
    - title-like text
    - long-text fallback splitting

    The logic is document-agnostic and does not depend on
    any particular subject matter.
    """

    if not elements:
        return []

    # -----------------------------------------------------
    # Clean elements.
    # -----------------------------------------------------

    cleaned_elements = []

    for element in elements:

        current = element.copy()

        current["text"] = _clean_text(
            current.get(
                "text",
                ""
            )
        )

        if not current["text"]:
            continue

        cleaned_elements.append(
            current
        )

    elements = _merge_heading_fragments(
        cleaned_elements
    )

    # -----------------------------------------------------
    # Builder state.
    # -----------------------------------------------------

    units = []

    current_section = None
    current_topic = None
    current_question = None

    current_text_blocks = []

    current_page_start = None
    current_page_end = None

    # -----------------------------------------------------
    # Flush current text.
    # -----------------------------------------------------

    def save_text_unit():

        nonlocal current_text_blocks
        nonlocal current_page_start
        nonlocal current_page_end

        if not current_text_blocks:
            return

        merged = _merge_text_blocks(
            current_text_blocks
        )

        final_parts = []

        for block in merged:

            cleaned = _clean_text(
                block.get(
                    "text",
                    ""
                )
            )

            if cleaned:
                final_parts.append(
                    cleaned
                )

        final_text = " ".join(
            final_parts
        ).strip()

        if not final_text:

            current_text_blocks = []
            current_page_start = None
            current_page_end = None

            return

        pieces = _split_long_text(
            final_text
        )

        for piece in pieces:

            units.append({
                "section": current_section,
                "topic": current_topic,
                "question": current_question,
                "content_type": "text",
                "page_start": current_page_start,
                "page_end": current_page_end,
                "text": piece,
            })

        current_text_blocks = []
        current_page_start = None
        current_page_end = None

    # -----------------------------------------------------
    # Main loop.
    # -----------------------------------------------------

    for element in elements:

        explicit_type = element.get(
            "element_type",
            "text"
        )

        text = _clean_text(
            element.get(
                "text",
                ""
            )
        )

        page_number = element.get(
            "page_number"
        )

        if not text:
            continue

        # -----------------------------------------------
        # Remove obvious non-content.
        # -----------------------------------------------

        if explicit_type in {
            "footer",
            "figure_caption",
        }:
            continue

        if _is_toc_element(
            element
        ):
            continue

        # -----------------------------------------------
        # Infer role.
        # -----------------------------------------------

        role = _infer_element_role(
            element
        )

        # -----------------------------------------------
        # Numbered semantic section.
        # -----------------------------------------------

        if role == "numbered_section":

            parsed = _parse_numbered_lead(
                text
            )

            if parsed is not None:

                save_text_unit()

                current_section = (
                    parsed["label"]
                )

                current_topic = None
                current_question = None

                # Preserve the explanatory remainder as
                # actual document content.
                remainder = parsed[
                    "remainder"
                ]

                if remainder:

                    current_text_blocks.append({
                        "section": current_section,
                        "topic": current_topic,
                        "question": current_question,
                        "content_type": "text",
                        "page_number": page_number,
                        "page_start": page_number,
                        "page_end": page_number,
                        "bbox": element.get(
                            "bbox",
                            (0, 0, 0, 0)
                        ),
                        "text": remainder,
                    })

                    if page_number is not None:

                        current_page_start = (
                            page_number
                        )

                        current_page_end = (
                            page_number
                        )

                continue

        # -----------------------------------------------
        # Explicit / inferred main heading.
        # -----------------------------------------------

        if role == "heading":

            save_text_unit()

            current_section = text
            current_topic = None
            current_question = None

            continue

        # -----------------------------------------------
        # Question.
        # -----------------------------------------------

        if role == "question":

            save_text_unit()

            if current_section is None:

                current_section = "Document"

            current_question = text

            current_topic = None

            current_page_start = (
                page_number
            )

            current_page_end = (
                page_number
            )

            continue

        # -----------------------------------------------
        # Topic / subheading.
        # -----------------------------------------------

        if role == "subheading":

            # Do not treat every short line as a topic
            # before a real section exists.
            if current_section is not None:

                save_text_unit()

                current_topic = text
                current_question = None

                continue

        # -----------------------------------------------
        # Explicit table.
        # -----------------------------------------------

        if explicit_type == "table":

            save_text_unit()

            if current_section is None:

                current_section = "Document"

            units.append({
                "section": current_section,
                "topic": current_topic,
                "question": current_question,
                "content_type": "table",
                "page_start": page_number,
                "page_end": page_number,
                "text": text,
            })

            continue

        # -----------------------------------------------
        # Normal text.
        # -----------------------------------------------

        if current_section is None:

            current_section = "Document"

        current_text_blocks.append({
            "section": current_section,
            "topic": current_topic,
            "question": current_question,
            "content_type": "text",
            "page_number": page_number,
            "page_start": page_number,
            "page_end": page_number,
            "bbox": element.get(
                "bbox",
                (0, 0, 0, 0)
            ),
            "text": text,
        })

        if page_number is not None:

            if current_page_start is None:

                current_page_start = (
                    page_number
                )

            current_page_end = (
                page_number
            )

    # -----------------------------------------------------
    # Final flush.
    # -----------------------------------------------------

    save_text_unit()

    return units