from ufrag.chunking.base import split_text
from ufrag.models import Chunk, Citation

GROUP_MAX_CHARS = 1200  # smaller chunks for unstructured content, no boundaries to lean on


def chunk_unstructured(file_id: str, filename: str, paragraphs: list[str]) -> list[Chunk]:
    chunks = []
    chunk_index = 0
    group: list[str] = []
    group_start = 0

    def flush(end_idx: int):
        nonlocal chunk_index
        text = "\n".join(group).strip()
        if not text:
            return
        for part in split_text(text, GROUP_MAX_CHARS):
            citation = Citation(
                file_id=file_id,
                filename=filename,
                section_path="(no section structure)",
                location={"para_start": group_start, "para_end": end_idx},
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

    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        if not group:
            group_start = i
        group.append(para)
        if sum(len(p) for p in group) >= GROUP_MAX_CHARS:
            flush(i)
            group = []

    if group:
        flush(len(paragraphs) - 1)

    return chunks
