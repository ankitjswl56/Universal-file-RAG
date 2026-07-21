from dataclasses import dataclass

from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.outline_store import OutlineStore
from ufrag.indexing.vector_store import VectorStore
from ufrag.models import Chunk
from ufrag.retrieval.hierarchical_search import hierarchical_search
from ufrag.retrieval.vector_search import vector_search


@dataclass
class RetrievalTraceEntry:
    file_id: str
    filename: str
    strategy_used: str
    reason: str


@dataclass
class RetrievalResult:
    chunks: list[Chunk]
    trace: list[RetrievalTraceEntry]


def retrieve(
    question: str,
    file_ids: list[str] | None,
    client: GeminiClient,
    metadata_store: MetadataStore,
    outline_store: OutlineStore,
    vector_store: VectorStore,
    top_k: int = 8,
) -> RetrievalResult:
    scope_files = file_ids or [row["file_id"] for row in metadata_store.list_files()]

    merged = vector_search(
        question, scope_files, client, vector_store, metadata_store, top_k=top_k
    )
    seen_chunk_ids = {c.chunk_id for c in merged}

    trace = []
    for file_id in scope_files:
        file_row = metadata_store.get_file(file_id)
        if file_row is None:
            continue

        if outline_store.has_tree(file_id):
            tree_chunks = hierarchical_search(
                question, file_id, client, outline_store, metadata_store
            )
            new_chunks = [c for c in tree_chunks if c.chunk_id not in seen_chunk_ids]
            merged.extend(new_chunks)
            seen_chunk_ids.update(c.chunk_id for c in new_chunks)
            trace.append(
                RetrievalTraceEntry(
                    file_id=file_id,
                    filename=file_row["filename"],
                    strategy_used="hierarchical+vector",
                    reason=(
                        f"file has a hierarchical outline; navigated tree "
                        f"({len(tree_chunks)} candidate node match(es)) and merged with vector search"
                    ),
                )
            )
        else:
            trace.append(
                RetrievalTraceEntry(
                    file_id=file_id,
                    filename=file_row["filename"],
                    strategy_used="vector_only",
                    reason="file has no hierarchical outline (unstructured or below the length gate); vector search only",
                )
            )

    return RetrievalResult(chunks=merged, trace=trace)
