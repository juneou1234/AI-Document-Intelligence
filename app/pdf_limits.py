import pymupdf


# =========================================================
# LIMITS
# =========================================================

MAX_PDF_MB = 25
MAX_PDF_BYTES = MAX_PDF_MB * 1024 * 1024
MAX_PDF_PAGES = 80


class PdfTooLargeError(ValueError):
    """Raised when a PDF is too large to index safely."""


def _size_in_mb(
    pdf_bytes
):
    """Return the file size in megabytes."""

    return len(
        pdf_bytes
    ) / (
        1024 * 1024
    )


def count_pdf_pages(
    pdf_bytes
):
    """
    Count pages quickly without extracting text.

    This should finish in about a second even for
    large files, unlike full indexing.
    """

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    try:

        return len(
            document
        )

    finally:

        document.close()


def check_pdf_can_be_indexed(
    pdf_bytes,
    filename
):
    """
    Reject oversized PDFs before slow indexing starts.

    Checks file size first, then page count.
    """

    display_name = filename or "This PDF"

    size_mb = _size_in_mb(
        pdf_bytes
    )

    if len(pdf_bytes) > MAX_PDF_BYTES:

        raise PdfTooLargeError(
            f'"{display_name}" is too large '
            f"({size_mb:.1f} MB). "
            f"Please upload a PDF of at most "
            f"{MAX_PDF_MB} MB."
        )

    try:

        page_count = count_pdf_pages(
            pdf_bytes
        )

    except PdfTooLargeError:

        raise

    except Exception as error:

        raise ValueError(
            f'"{display_name}" could not be opened as a PDF.'
        ) from error

    if page_count < 1:

        raise ValueError(
            f'"{display_name}" has no pages to read.'
        )

    if page_count > MAX_PDF_PAGES:

        raise PdfTooLargeError(
            f'"{display_name}" is too large '
            f"({page_count} pages). "
            f"Please upload a PDF with at most "
            f"{MAX_PDF_PAGES} pages."
        )

    return page_count
