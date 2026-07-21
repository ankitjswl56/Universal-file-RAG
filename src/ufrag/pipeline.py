import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ufrag.chunking.strategies.markdown import chunk_structured, chunk_unstructured
from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.outline_store import OutlineStore
from ufrag.indexing.vector_store import VectorStore
from ufrag.ingestion.extractors.markdown import extract_markdown
from ufrag.structure.outline_builder import build_outline
from ufrag.structure.structure_scorer import score_markdown

SUPPORTED_SUFFIXES = {".md", ".markdown"}


@dataclass
class Stores:
    metadata: MetadataStore
    outline: OutlineStore
    vector: VectorStore
    client: GeminiClient


def ingest_file(path: Path, stores: Stores) -> dict:
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"unsupported file type: {path.suffix!r} (only markdown is supported in Phase 1)"
        )

    text = path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    file_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path.resolve()}:{content_hash}"))
    filename = path.name

    stores.metadata.register_file(
        file_id=file_id,
        filename=filename,
        file_type="markdown",
        content_hash=content_hash,
        ingested_at=datetime.now(UTC).isoformat(),
    )

    sections = extract_markdown(text)
    decision = score_markdown(sections, len(text))

    if decision.is_structured:
        nodes = build_outline(file_id, sections, stores.client)
        stores.outline.add_nodes(nodes)
        chunks = chunk_structured(file_id, filename, sections, nodes)
        structure_type = "hierarchical"
    else:
        chunks = chunk_unstructured(file_id, filename, text)
        structure_type = "vector_only"

    stores.metadata.set_structure_type(file_id, structure_type)
    stores.metadata.add_chunks(chunks)

    vectors = stores.client.embed([c.text for c in chunks])
    stores.vector.upsert_chunks(chunks, vectors)

    stores.metadata.set_file_status(file_id, "ready")

    return {
        "file_id": file_id,
        "filename": filename,
        "structure_type": structure_type,
        "structure_reason": decision.reason,
        "chunk_count": len(chunks),
    }
