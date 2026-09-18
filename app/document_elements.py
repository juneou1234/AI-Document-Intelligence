import pymupdf

from app.blocks import extract_text_blocks
from app.elements import classify_element
from app.layout import analyze_layout


def extract_document_elements(
    pdf_path,
    page_number
):
    """
    Extract, classify, and order elements from one page.
    """

    blocks = extract_text_blocks(
        pdf_path,
        page_number
    )

    for block in blocks:

        block["element_type"] = classify_element(
            block
        )

    blocks = analyze_layout(
        blocks
    )

    return blocks


def extract_all_document_elements(
    pdf_path
):
    """
    Extract elements from every page in reading order.
    """

    document = pymupdf.open(
        pdf_path
    )

    try:

        all_elements = []

        for page_index in range(
            len(document)
        ):

            page_number = page_index + 1

            page_elements = (
                extract_document_elements(
                    pdf_path,
                    page_number
                )
            )

            all_elements.extend(
                page_elements
            )

        return all_elements

    finally:

        document.close()