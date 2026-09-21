import re


# =========================================================
# CONFIGURATION
# =========================================================

MIN_RESULT_SCORE = 0.45

MIN_TEXT_CHARS = 120

MAX_SINGLE_RESULT_CHARS = 1800

DEFAULT_MAX_CONTEXT_CHARS = 7000


# =========================================================
# TEXT CLEANING
# =========================================================

def _clean_context_text(text):
    """Clean text before sending it to the LLM."""

    if not text:
        return ""

    # Repair words split across line breaks.
    text = re.sub(
        r"(?<=\w)-\s+(?=\w)",
        "",
        text
    )

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =========================================================
# RESULT FORMATTING
# =========================================================

def _format_result(
    result,
    text_override=None,
    source_number=None
):
    """Format one retrieval result for the LLM."""

    text = (
        text_override
        if text_override is not None
        else result.get(
            "text",
            ""
        )
    )

    text = _clean_context_text(
        text
    )

    header = ""

    if source_number is not None:

        header = (
            f"Source [{source_number}]\n"
        )

    return (
        f"{header}"
        f"Section: {result.get('section')}\n"
        f"Topic: {result.get('topic')}\n"
        f"Question: {result.get('question')}\n"
        f"Pages: "
        f"{result.get('page_start')}-"
        f"{result.get('page_end')}\n"
        f"Content type: "
        f"{result.get('content_type')}\n"
        f"Text: {text}"
    )


# =========================================================
# TRUNCATION
# =========================================================

def _truncate_text(
    text,
    max_chars
):
    """
    Truncate text while trying to preserve complete
    sentences and useful endings.
    """

    text = _clean_context_text(
        text
    )

    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    shortened = text[
        :max_chars
    ]

    sentence_boundaries = [
        shortened.rfind("."),
        shortened.rfind("?"),
        shortened.rfind("!"),
        shortened.rfind(";"),
    ]

    sentence_end = max(
        sentence_boundaries
    )

    # Don't create an unnecessarily tiny chunk.
    if (
        sentence_end >=
        max_chars * 0.55
    ):

        return shortened[
            :sentence_end + 1
        ].strip()

    # Try a word boundary.
    last_space = shortened.rfind(
        " "
    )

    if (
        last_space >=
        max_chars * 0.70
    ):

        return (
            shortened[
                :last_space
            ].strip()
            + "..."
        )

    return (
        shortened.rstrip()
        + "..."
    )


# =========================================================
# RESULT IDENTITY
# =========================================================

def _result_key(result):
    """Build a stable key for deduplication."""

    return (
        result.get("section"),
        result.get("topic"),
        result.get("question"),
        result.get("page_start"),
        result.get("page_end"),
        result.get("content_type"),
        result.get("text"),
    )


# =========================================================
# RESULT QUALITY
# =========================================================

def _result_score(result):
    """
    Return the best available retrieval score.
    """

    return float(
        result.get(
            "score",
            result.get(
                "semantic_score",
                0.0
            )
        )
        or 0.0
    )


def _result_relevance_bonus(result):
    """
    Give small bonuses to explicit question matches,
    topic matches, and repeated query coverage.
    """

    bonus = 0.0

    bonus += (
        0.20
        * float(
            result.get(
                "question_match_score",
                0.0
            )
            or 0.0
        )
    )

    bonus += (
        0.05
        * float(
            result.get(
                "keyword_score",
                0.0
            )
            or 0.0
        )
    )

    coverage = int(
        result.get(
            "coverage_count",
            1
        )
        or 1
    )

    if coverage > 1:

        bonus += min(
            0.10,
            0.03
            * (
                coverage
                - 1
            )
        )

    return bonus


# =========================================================
# CONTEXT SELECTION
# =========================================================

def _prepare_results(results):
    """
    Deduplicate and rank retrieval results for context.
    """

    unique = {}

    for result in results:

        if not result.get(
            "text"
        ):
            continue

        key = _result_key(
            result
        )

        if key not in unique:

            unique[key] = result

        else:

            existing = unique[
                key
            ]

            if (
                _result_score(
                    result
                )
                >
                _result_score(
                    existing
                )
            ):

                unique[key] = result

    prepared = []

    for result in unique.values():

        score = _result_score(
            result
        )

        relevance = (
            score
            + _result_relevance_bonus(
                result
            )
        )

        result_copy = result.copy()

        result_copy[
            "_context_relevance"
        ] = relevance

        prepared.append(
            result_copy
        )

    prepared.sort(
        key=lambda item:
        item[
            "_context_relevance"
        ],
        reverse=True
    )

    return prepared


# =========================================================
# MAIN CONTEXT BUILDER
# =========================================================

def build_context(
    results,
    all_units=None,
    max_chars=DEFAULT_MAX_CONTEXT_CHARS
):
    """
    Build relevance-aware context.

    Important design principle:

    Retrieval has already selected relevant material.
    Context building should preserve that evidence rather
    than giving every source an equal tiny slice.

    `all_units` is retained for API compatibility with the
    rest of the project, but is not required for normal
    context construction.
    """

    if not results:
        return ""

    prepared = _prepare_results(
        results
    )

    if not prepared:
        return ""

    # -----------------------------------------------------
    # Remove obviously weak results.
    #
    # We keep at least the first result regardless of score.
    # -----------------------------------------------------

    filtered = []

    for index, result in enumerate(
        prepared
    ):

        score = _result_score(
            result
        )

        if (
            index == 0
            or score >= MIN_RESULT_SCORE
        ):

            filtered.append(
                result
            )

    if not filtered:
        filtered = [
            prepared[0]
        ]

    # -----------------------------------------------------
    # Allocate context intelligently.
    #
    # The strongest results receive substantially more
    # space than weak supporting results.
    # -----------------------------------------------------

    selected_blocks = []

    used_chars = 0

    separator_cost = 8

    for index, result in enumerate(
        filtered
    ):

        if used_chars >= max_chars:
            break

        relevance = result.get(
            "_context_relevance",
            0.0
        )

        # -----------------------------------------------
        # Budget by rank.
        # -----------------------------------------------

        if index == 0:

            desired_budget = min(
                MAX_SINGLE_RESULT_CHARS,
                2200
            )

        elif index == 1:

            desired_budget = 1500

        elif index == 2:

            desired_budget = 1200

        elif index == 3:

            desired_budget = 900

        else:

            desired_budget = 700

        # Slight bonus for strongly relevant results.
        if relevance >= 0.85:

            desired_budget += 300

        if relevance >= 1.00:

            desired_budget += 300

        remaining = (
            max_chars
            - used_chars
        )

        if (
            len(selected_blocks)
            > 0
        ):

            remaining -= separator_cost

        if remaining <= 100:
            break

        desired_budget = min(
            desired_budget,
            remaining
        )

        raw_text = _clean_context_text(
            result.get(
                "text",
                ""
            )
        )

        if not raw_text:
            continue

        # -----------------------------------------------
        # Figure out formatting overhead.
        # -----------------------------------------------

        empty_formatted = _format_result(
            result,
            text_override="",
            source_number=index + 1
        )

        formatting_overhead = len(
            empty_formatted
        )

        text_budget = max(
            MIN_TEXT_CHARS,
            desired_budget
            - formatting_overhead
        )

        if text_budget > MAX_SINGLE_RESULT_CHARS:

            text_budget = (
                MAX_SINGLE_RESULT_CHARS
            )

        text = _truncate_text(
            raw_text,
            text_budget
        )

        block = _format_result(
            result,
            text_override=text,
            source_number=index + 1
        )

        if not block:
            continue

        if (
            used_chars
            + len(block)
            + (
                separator_cost
                if selected_blocks
                else 0
            )
            > max_chars
        ):

            remaining = (
                max_chars
                - used_chars
                - (
                    separator_cost
                    if selected_blocks
                    else 0
                )
            )

            if remaining < 150:
                break

            text_budget = max(
                100,
                remaining
                - formatting_overhead
            )

            text = _truncate_text(
                raw_text,
                text_budget
            )

            block = _format_result(
                result,
                text_override=text,
                source_number=index + 1
            )

        if not block:
            continue

        selected_blocks.append(
            {
                "result": result,
                "block": block,
                "rank": index,
            }
        )

        used_chars += len(
            block
        )

        if (
            len(
                selected_blocks
            ) > 1
        ):

            used_chars += (
                separator_cost
            )

    # -----------------------------------------------------
    # Assemble final context.
    # -----------------------------------------------------

    context_parts = []

    for item in selected_blocks:

        context_parts.append(
            item["block"]
        )

    return "\n\n---\n\n".join(
        context_parts
    )