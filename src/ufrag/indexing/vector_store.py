import uuid

from qdrant_client import QdrantClient, models

from ufrag.gemini_client import EMBEDDING_DIM
from ufrag.models import Chunk

COLLECTION = "chunks"


class VectorStore:
    def __init__(self, host: str, port: int):
        self._client = QdrantClient(host=host, port=port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self._client.collection_exists(COLLECTION):
            self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIM, distance=models.Distance.COSINE
                ),
            )

    def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        points = [
            models.PointStruct(
                id=_point_id(chunk.chunk_id),
                vector=vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "file_id": chunk.file_id,
                    "node_id": chunk.node_id,
                    "text": chunk.text,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self._client.upsert(collection_name=COLLECTION, points=points)

    def search(
        self, query_vector: list[float], file_ids: list[str] | None = None, top_k: int = 8
    ) -> list[models.ScoredPoint]:
        query_filter = None
        if file_ids:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_id", match=models.MatchAny(any=file_ids)
                    )
                ]
            )
        result = self._client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return result.points


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
