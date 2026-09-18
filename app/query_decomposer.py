import re


# =========================================================
# TEXT CLEANING
# =========================================================

def _clean_query(text):
    """Clean whitespace and punctuation from a query."""

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    text = text.strip(
        " ,.;:?-"
    )

    return text


def _normalize_for_comparison(text):
    """Normalize a query for duplicate detection."""

    text = _clean_query(
        text
    ).lower()

    # Normalize plural/singular differences for simple
    # duplicate detection.
    text = re.sub(
        r"\bcarbohydrates\b",
        "carbohydrate",
        text
    )

    text = re.sub(
        r"\bfats\b",
        "fat",
        text
    )

    text = re.sub(
        r"\bamino acids\b",
        "amino acid",
        text
    )

    return text


def _add_query(
    queries,
    query
):
    """Add a query only when it is meaningfully unique."""

    query = _clean_query(
        query
    )

    if not query:
        return

    normalized = _normalize_for_comparison(
        query
    )

    for existing in queries:

        if (
            _normalize_for_comparison(
                existing
            )
            == normalized
        ):
            return

    queries.append(
        query
    )


# =========================================================
# TERM DETECTION
# =========================================================

NUTRIENT_TERMS = {
    "protein": "protein",
    "carbohydrates": "carbohydrates",
    "carbohydrate": "carbohydrates",
    "fats": "fat",
    "fat": "fat",
    "energy": "energy",
    "minerals": "minerals",
    "mineral": "minerals",
    "vitamins": "vitamins",
    "vitamin": "vitamins",
    "water": "water",
    "amino acids": "amino acids",
    "amino acid": "amino acids",
}


STAGE_PATTERNS = {
    "weaning": (
        "weaning",
        "weaned",
        "early weaning",
    ),
    "creep feeding": (
        "creep feeding",
        "creep feed",
        "creep",
        "baby pig",
        "young pig",
    ),
    "starter": (
        "starter",
        "starting pigs",
        "starting pig",
    ),
    "growing": (
        "grower",
        "growing",
        "growing pigs",
    ),
    "finishing": (
        "finisher",
        "finishing",
        "finishing pigs",
    ),
    "gestation": (
        "gestation",
        "gestating",
    ),
    "lactation": (
        "lactation",
        "lactating",
    ),
}


# =========================================================
# EXTRACTION HELPERS
# =========================================================

def _detect_nutrients(query):
    """Return nutrients explicitly mentioned by the user."""

    lowered = query.lower()

    detected = []

    # Check longer phrases first.
    for phrase, canonical in sorted(
        NUTRIENT_TERMS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):

        if phrase in lowered:

            if canonical not in detected:
                detected.append(
                    canonical
                )

    return detected


def _detect_stages(query):
    """Return production stages mentioned by the user."""

    lowered = query.lower()

    detected = []

    for stage, patterns in STAGE_PATTERNS.items():

        if any(
            pattern in lowered
            for pattern in patterns
        ):

            detected.append(
                stage
            )

    return detected


# =========================================================
# QUESTION TYPE DETECTION
# =========================================================

def _asks_about_requirements(query):
    """Detect whether the question requests quantities/levels."""

    lowered = query.lower()

    requirement_terms = (
        "how much",
        "how many",
        "amount",
        "level",
        "levels",
        "requirement",
        "requirements",
        "required",
        "needed",
        "percentage",
        "%",
        "nutrition",
        "nutritional",
    )

    return any(
        term in lowered
        for term in requirement_terms
    )


def _asks_about_sources(query):
    """Detect source-related questions."""

    lowered = query.lower()

    source_terms = (
        "source",
        "sources",
        "comes from",
        "come from",
    )

    return any(
        term in lowered
        for term in source_terms
    )


def _is_complex_query(query):
    """
    Determine whether decomposition is likely useful.

    We avoid creating multiple queries for simple questions.
    """

    nutrients = _detect_nutrients(
        query
    )

    stages = _detect_stages(
        query
    )

    conjunctions = re.findall(
        r"\b(?:and|or)\b",
        query.lower()
    )

    return (
        len(nutrients) >= 2
        or len(stages) >= 2
        or len(conjunctions) >= 2
        or _asks_about_requirements(
            query
        )
        and len(query.split()) > 12
    )


# =========================================================
# MAIN DECOMPOSER
# =========================================================

def decompose_query(query):
    """
    Decompose a complex user question into a small number
    of high-value retrieval queries.

    The original query is always preserved.

    This function is fully local and does not call an LLM.
    """

    query = _clean_query(
        query
    )

    if not query:
        return []

    queries = []

    # -----------------------------------------------------
    # Always preserve the original question.
    # -----------------------------------------------------

    _add_query(
        queries,
        query
    )

    # -----------------------------------------------------
    # Don't over-decompose simple questions.
    # -----------------------------------------------------

    if not _is_complex_query(
        query
    ):
        return queries

    nutrients = _detect_nutrients(
        query
    )

    stages = _detect_stages(
        query
    )

    requirements = _asks_about_requirements(
        query
    )

    sources = _asks_about_sources(
        query
    )

    lowered = query.lower()

    # -----------------------------------------------------
    # Multi-stage requirement question
    # -----------------------------------------------------

    if (
        len(stages) >= 2
        and requirements
    ):

        _add_query(
            queries,
            "What nutrient levels or requirements are given for "
            + ", ".join(stages)
            + " pigs?"
        )

    # -----------------------------------------------------
    # Multi-nutrient requirement question
    # -----------------------------------------------------

    if (
        len(nutrients) >= 2
        and requirements
    ):

        nutrient_list = ", ".join(
            nutrients
        )

        _add_query(
            queries,
            f"What are the {nutrient_list} "
            "requirements or levels given in the document?"
        )

    # -----------------------------------------------------
    # Individual nutrient requirements
    #
    # Only generate individual queries when they are useful.
    # Avoid creating duplicate carbohydrate/carbohydrate
    # queries.
    # -----------------------------------------------------

    if requirements:

        for nutrient in nutrients:

            _add_query(
                queries,
                f"What does the document state about "
                f"{nutrient} requirements for pigs?"
            )

    # -----------------------------------------------------
    # Nutrient source query
    # -----------------------------------------------------

    if (
        sources
        or "full nutrition" in lowered
        or "complete nutrition" in lowered
        or "main nutrients" in lowered
        or "what nutrients" in lowered
    ):

        _add_query(
            queries,
            "What are the main nutrient groups required for pigs?"
        )

    # -----------------------------------------------------
    # Energy-source query
    # -----------------------------------------------------

    if (
        "energy" in lowered
        or "carbohydrate" in lowered
        or "fat" in lowered
    ):

        _add_query(
            queries,
            "What are the sources of energy for pigs?"
        )

    # -----------------------------------------------------
    # Protein-source query
    # -----------------------------------------------------

    if "protein" in lowered:

        _add_query(
            queries,
            "What are the sources of protein for pigs?"
        )

    # -----------------------------------------------------
    # Stage-specific focused queries
    #
    # We only generate these when the user explicitly asks
    # about stages. This prevents unnecessary retrieval.
    # -----------------------------------------------------

    if len(stages) >= 2:

        for stage in stages:

            if (
                "protein" in lowered
                and requirements
            ):

                _add_query(
                    queries,
                    f"What protein level is given for {stage} pigs?"
                )

    # -----------------------------------------------------
    # Keep the query set intentionally small.
    # -----------------------------------------------------

    return queries[:6]