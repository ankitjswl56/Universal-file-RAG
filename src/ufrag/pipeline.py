import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ufrag.chunking.base import chunk_structured
from ufrag.chunking.strategies import docx as docx_chunking
from ufrag.chunking.strategies import markdown as markdown_chunking
from ufrag.chunking.strategies import pdf as pdf_chunking
from ufrag.chunking.strategies.audio import chunk_audio
from ufrag.chunking.strategies.image import chunk_image
from ufrag.chunking.strategies.spreadsheet import chunk_spreadsheet
from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.outline_store import OutlineStore
from ufrag.indexing.vector_store import VectorStore
from ufrag.ingestion.detector import detect_file_type
from ufrag.ingestion.extractors.audio import extract_audio
from ufrag.ingestion.extractors.docx import extract_docx
from ufrag.ingestion.extractors.image import extract_image
from ufrag.ingestion.extractors.markdown import extract_markdown
from ufrag.ingestion.extractors.pdf import extract_pdf, render_page_image
from ufrag.ingestion.extractors.spreadsheet import extract_spreadsheet
from ufrag.models import Chunk
from ufrag.structure.outline_builder import build_outline
from ufrag.structure.structure_scorer import score_structure

DOCUMENT_TYPES = {"markdown", "pdf", "docx"}


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

    if file_type in DOCUMENT_TYPES:
        chunks, structure_type, structure_reason, doc_warnings = _ingest_document(
            file_type, path, file_id, filename, stores
        )
        warnings.extend(doc_warnings)
    elif file_type == "spreadsheet":
        sheets = extract_spreadsheet(path)
        chunks, sheet_warnings = chunk_spreadsheet(file_id, filename, sheets)
        warnings.extend(sheet_warnings)
        structure_type = "vector_only"
        structure_reason = (
            "spreadsheets are indexed directly as schema/formula/row chunks; there's no "
            "prose heading structure to build a hierarchical outline from"
        )
    elif file_type == "image":
        ocr_text, caption = extract_image(path, stores.client)
        chunks = chunk_image(file_id, filename, ocr_text, caption)
        structure_type = "vector_only"
        structure_reason = (
            "images are indexed as OCR'd text (if any) plus a visual description; "
            "no hierarchical structure applies"
        )
        if ocr_text is None:
            warnings.append("no readable text found in the image; only the visual description was indexed")
    elif file_type == "audio":
        segments = extract_audio(path, stores.client)
        chunks = chunk_audio(file_id, filename, segments)
        structure_type = "vector_only"
        structure_reason = (
            "audio is indexed as timestamped transcript segments; no hierarchical "
            "structure applies"
        )
        if not chunks:
            warnings.append(
                "transcription produced no usable segments (check audio format/content)"
            )
    else:
        raise ValueError(f"unhandled file type: {file_type!r}")

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
        "structure_reason": structure_reason,
        "chunk_count": len(chunks),
        "warnings": warnings,
    }


def _ingest_document(
    file_type: str, path: Path, file_id: str, filename: str, stores: Stores
) -> tuple[list[Chunk], str, str, list[str]]:
    warnings: list[str] = []

    if file_type == "markdown":
        text = path.read_text(encoding="utf-8")
        sections = extract_markdown(text)
        total_length = len(text)
        unstructured_fallback = text
        unstructured_chunker = markdown_chunking.chunk_unstructured
    elif file_type == "pdf":
        sections, page_texts, scanned_pages = extract_pdf(path)
        for page_num in scanned_pages:
            image_bytes = render_page_image(path, page_num)
            ocr_text = stores.client.ocr_image(image_bytes).strip()
            if ocr_text == "NO_TEXT_FOUND":
                page_texts[page_num - 1] = ""
                warnings.append(
                    f"page {page_num} has no extractable text even via OCR "
                    "(likely blank or a non-text image)"
                )
            else:
                page_texts[page_num - 1] = ocr_text
                hedge = " (some text was flagged as unclear)" if "[unclear:" in ocr_text else ""
                warnings.append(
                    f"page {page_num} had no native text layer; transcribed via "
                    f"Gemini vision OCR{hedge}"
                )
        total_length = sum(len(t) for t in page_texts)
        unstructured_fallback = page_texts
        unstructured_chunker = pdf_chunking.chunk_unstructured
    elif file_type == "docx":
        sections, paragraphs = extract_docx(path)
        total_length = sum(len(p) for p in paragraphs)
        unstructured_fallback = paragraphs
        unstructured_chunker = docx_chunking.chunk_unstructured
    else:
        raise ValueError(f"unhandled document type: {file_type!r}")

    decision = score_structure(sections, total_length)

    if decision.is_structured:
        nodes = build_outline(file_id, sections, stores.client)
        stores.outline.add_nodes(nodes)
        chunks = chunk_structured(file_id, filename, sections, nodes)
        structure_type = "hierarchical"
    else:
        chunks = unstructured_chunker(file_id, filename, unstructured_fallback)
        structure_type = "vector_only"

    return chunks, structure_type, decision.reason, warnings
