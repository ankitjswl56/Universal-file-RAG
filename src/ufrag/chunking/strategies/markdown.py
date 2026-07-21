from ufrag.chunking.base import split_text
from ufrag.ingestion.extractors.markdown import MarkdownSection
from ufrag.models import Chunk, Citation, OutlineNode

MAX_CHUNK_CHARS = 3200
PARAGRAPH_MAX_CHARS = 1200  # smaller chunks for unstructured content, no boundaries to lean on


def chunk_structured(
    file_id: str, filename: str, sections: list[MarkdownSection], nodes: list[OutlineNode]
) -> list[Chunk]:
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
                line_start=section.line_start,
                line_end=section.line_end,
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


def chunk_unstructured(file_id: str, filename: str, text: str) -> list[Chunk]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    chunk_index = 0
    line_cursor = 1
    for paragraph in paragraphs:
        line_count = paragraph.count("\n") + 1
        for part in split_text(paragraph, PARAGRAPH_MAX_CHARS):
            citation = Citation(
                file_id=file_id,
                filename=filename,
                section_path="(no section structure)",
                line_start=line_cursor,
                line_end=line_cursor + line_count - 1,
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
        line_cursor += line_count + 1
    return chunks
