"""Regenerates the scanned-PDF and standalone-image test fixtures under
tests/fixtures/. These are built by rendering real text to a rasterized
image and embedding *only* the image (no text layer) — genuinely testing
the OCR path rather than PyMuPDF's normal text extraction.

Run from the repo root: .venv/bin/python scripts/generate_ocr_fixtures.py
"""

import fitz

NOTICE_TEXT = (
    "FACILITIES NOTICE\n\n"
    "Emergency contact: Dr. Amara Okonkwo, reachable at extension 4471 "
    "during business hours.\n\n"
    "The freight elevator on the east side of the building is out of "
    "service until further notice. Use the main lobby elevator instead."
)


def render_text_to_image(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 400, 300), text, fontsize=16, fontname="helv")
    clip = fitz.Rect(0, 0, 420, 320)
    pix = page.get_pixmap(dpi=100, clip=clip)
    jpg_bytes = pix.tobytes("jpg", jpg_quality=60)
    doc.close()
    return jpg_bytes


def make_scanned_pdf(path: str, image_bytes: bytes) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=image_bytes)
    doc.save(path)
    doc.close()


if __name__ == "__main__":
    image_bytes = render_text_to_image(NOTICE_TEXT)

    with open("tests/fixtures/sample_notice.jpg", "wb") as f:
        f.write(image_bytes)

    make_scanned_pdf("tests/fixtures/sample_scanned.pdf", image_bytes)

    print("done")
