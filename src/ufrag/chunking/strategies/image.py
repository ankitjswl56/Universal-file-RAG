from ufrag.models import Chunk, Citation


def chunk_image(file_id: str, filename: str, ocr_text: str | None, caption: str) -> list[Chunk]:
    chunks = []
    chunk_index = 0

    def add(text: str, section_path: str) -> None:
        nonlocal chunk_index
        citation = Citation(file_id=file_id, filename=filename, section_path=section_path, location={})
        chunks.append(
            Chunk(
                chunk_id=f"{file_id}:chunk:{chunk_index}",
                file_id=file_id,
                chunk_index=chunk_index,
                text=text,
                citation=citation,
                node_id=None,
            )
        )
        chunk_index += 1

    if ocr_text:
        add(ocr_text, "OCR text")
    if caption:
        add(caption, "Visual description")
    return chunks
