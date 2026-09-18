from app.blocks import extract_text_blocks
from app.cleaner import clean_text


pdf_path = "documents/sample.pdf"

blocks = extract_text_blocks(
    pdf_path,
    page_number=3
)

for block in blocks:

    if block["block_number"] in [10, 12, 14, 16]:

        print("\nRAW:")
        print(repr(block["text"]))

        cleaned = clean_text(block["text"])

        print("\nCLEANED:")
        print(repr(cleaned))