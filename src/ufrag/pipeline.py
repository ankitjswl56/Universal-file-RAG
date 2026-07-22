import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ufrag.chunking.base import chunk_structured
from ufrag.chunking.strategies import markdown as markdown_chunking
from ufrag.chunking.strategies import pdf as pdf_chunking
from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.outline_store import OutlineStore
from ufrag.indexing.vector_store import VectorStore
from ufrag.ingestion.detector import detect_file_type
from ufrag.ingestion.extractors.markdown import extract_markdown
from ufrag.ingestion.extractors.pdf import extract_pdf
from ufrag.structure.outline_builder import build_outline
from ufrag.structure.structure_scorer import score_structure


@dataclass
class Stores:
    metadata: MetadataStore
    outline: OutlineStore
    vector: VectorStore
    client: GeminiClient


def ingest_file(path: Path, stores: Stores) -> dict:
    file_type = detect_file_type(path)
    filename = path.name
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    file_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path.resolve()}:{content_hash}"))

    stores.metadata.register_file(
        file_id=file_id,
        filename=filename,
        file_type=file_type,
        content_hash=content_hash,
        ingested_at=datetime.now(UTC).isoformat(),
    )

    warnings: list[str] = []

    if file_type == "markdown":
        text = path.read_text(encoding="utf-8")
        sections = extract_markdown(text)
        total_length = len(text)
        unstructured_fallback = text
        unstructured_chunker = markdown_chunking.chunk_unstructured
    elif file_type == "pdf":
        sections, page_texts, scanned_pages = extract_pdf(path)
        total_length = sum(len(t) for t in page_texts)
        unstructured_fallback = page_texts
        unstructured_chunker = pdf_chunking.chunk_unstructured
        warnings.extend(
            f"page {p} has little to no extractable text (likely scanned); "
            "OCR support isn't wired up yet, so this page's content is not indexed"
            for p in scanned_pages
        )
    else:
        raise ValueError(f"unhandled file type: {file_type!r}")

    decision = score_structure(sections, total_length)

    if decision.is_structured:
        nodes = build_outline(file_id, sections, stores.client)
        stores.outline.add_nodes(nodes)
        chunks = chunk_structured(file_id, filename, sections, nodes)
        structure_type = "hierarchical"
    else:
        chunks = unstructured_chunker(file_id, filename, unstructured_fallback)
        structure_type = "vector_only"

    stores.metadata.set_structure_type(file_id, structure_type)
    stores.metadata.add_chunks(chunks)

    if chunks:
        vectors = stores.client.embed([c.text for c in chunks])
        stores.vector.upsert_chunks(chunks, vectors)

    stores.metadata.set_file_status(file_id, "ready")

    return {
        "file_id": file_id,
        "filename": filename,
        "file_type": file_type,
        "structure_type": structure_type,
        "structure_reason": decision.reason,
        "chunk_count": len(chunks),
        "warnings": warnings,
    }
