from ufrag.chunking.base import split_text
from ufrag.models import Chunk, Citation

MAX_CHUNK_CHARS = 3200


def chunk_unstructured(file_id: str, filename: str, page_texts: list[str]) -> list[Chunk]:
    """Per-page chunking for PDFs with no usable heading structure.

    Page is the natural boundary for PDFs regardless of structure, so chunks
    never span across a page even in the unstructured fallback.
    """
    chunks = []
    chunk_index = 0
    for page_num, text in enumerate(page_texts, start=1):
        stripped = text.strip()
        if not stripped:
            continue
        for part in split_text(stripped, MAX_CHUNK_CHARS):
            citation = Citation(
                file_id=file_id,
                filename=filename,
                section_path="(no section structure)",
                location={"page_start": page_num, "page_end": page_num},
            )
            chunks.append(
                Chunk(
                    chunk_id=f"{file_id}:chunk:{chunk_index}",
                    file_id=file_id,
                    chunk_index=chunk_index,
                    text=part,
                    citation=citation,
                    node_id=None,
                )
            )
            chunk_index += 1
    return chunks
