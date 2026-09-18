import re


def clean_text(text):
    """Perform conservative cleaning of extracted PDF text."""

    # Join words split by a hyphen followed by whitespace.
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)

    # Join words split across an actual line break.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Replace multiple spaces/tabs with a single space.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove long runs of dots, often found in tables of contents.
    text = re.sub(r"\.{5,}", " ", text)

    # Clean leading/trailing whitespace on each line.
    lines = [line.strip() for line in text.splitlines()]

    # Preserve line structure.
    text = "\n".join(lines)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()