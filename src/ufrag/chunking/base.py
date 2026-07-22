from ufrag.models import Chunk, Citation, OutlineNode, Section

MAX_CHUNK_CHARS = 3200


def split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts = []
    start = 0
    while start < len(text):
        parts.append(text[start : start + max_chars])
        start += max_chars
    return parts


def chunk_structured(
    file_id: str, filename: str, sections: list[Section], nodes: list[OutlineNode]
) -> list[Chunk]:
    """Shared across file types: chunk sections that already have a built outline tree.

    Works for any extractor's output since Section/OutlineNode carry a generic
    `location` dict (line-based, page-based, etc.) rather than type-specific fields.
    """
    chunks = []
    chunk_index = 0
    for section, node in zip(sections, nodes):
        text = section.content.strip()
        if not text:
            continue
        for part in split_text(text, MAX_CHUNK_CHARS):
            citation = Citation(
                file_id=file_id,
                filename=filename,
                section_path=node.title,
                location=section.location,
            )
            chunks.append(
                Chunk(
                    chunk_id=f"{file_id}:chunk:{chunk_index}",
                    file_id=file_id,
                    chunk_index=chunk_index,
                    text=part,
                    citation=citation,
                    node_id=node.node_id,
                )
            )
            chunk_index += 1
    return chunks
