from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.vector_store import VectorStore
from ufrag.models import Chunk


def vector_search(
    question: str,
    file_ids: list[str],
    client: GeminiClient,
    vector_store: VectorStore,
    metadata_store: MetadataStore,
    top_k: int = 8,
) -> list[Chunk]:
    query_vector = client.embed([question])[0]
    points = vector_store.search(query_vector, file_ids=file_ids, top_k=top_k)
    chunk_ids = [p.payload["chunk_id"] for p in points]

    chunks = metadata_store.get_chunks_by_ids(chunk_ids)
    order = {cid: i for i, cid in enumerate(chunk_ids)}
    chunks.sort(key=lambda c: order[c.chunk_id])
    return chunks
