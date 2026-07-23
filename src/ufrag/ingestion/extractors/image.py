from pathlib import Path

from ufrag.gemini_client import GeminiClient

MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def extract_image(path: Path, client: GeminiClient) -> tuple[str | None, str]:
    """Returns (ocr_text_or_None, caption). Images have no parseable structure of

    their own, so unlike every other extractor this one needs the Gemini client
    directly — OCR and captioning are themselves the "extraction" here, not a
    separate downstream step.
    """
    image_bytes = path.read_bytes()
    mime_type = MIME_TYPES.get(path.suffix.lower(), "image/png")

    ocr_raw = client.ocr_image(image_bytes, mime_type).strip()
    ocr_text = None if ocr_raw == "NO_TEXT_FOUND" else ocr_raw

    caption = client.caption_image(image_bytes, mime_type).strip()
    return ocr_text, caption
