import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ufrag.models import Chunk, Citation

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    structure_type TEXT NOT NULL DEFAULT 'unknown',
    content_hash TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(file_id),
    node_id TEXT,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    citation_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id);
"""


class MetadataStore:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def register_file(
        self,
        file_id: str,
        filename: str,
        file_type: str,
        content_hash: str,
        ingested_at: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO files (file_id, filename, file_type, content_hash, ingested_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (file_id, filename, file_type, content_hash, ingested_at),
            )

    def set_file_status(self, file_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE files SET status = ? WHERE file_id = ?", (status, file_id))

    def set_structure_type(self, file_id: str, structure_type: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE files SET structure_type = ? WHERE file_id = ?",
                (structure_type, file_id),
            )

    def get_file(self, file_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()

    def list_files(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM files").fetchall()

    def add_chunks(self, chunks: list[Chunk]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO chunks (chunk_id, file_id, node_id, chunk_index, text, citation_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        c.chunk_id,
                        c.file_id,
                        c.node_id,
                        c.chunk_index,
                        c.text,
                        json.dumps(c.citation.__dict__),
                    )
                    for c in chunks
                ],
            )

    def get_chunks_by_file(self, file_id: str) -> list[Chunk]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE file_id = ? ORDER BY chunk_index", (file_id,)
            ).fetchall()
        return [self._row_to_chunk(row) for row in rows]

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        if not chunk_ids:
            return []
        placeholders = ",".join("?" for _ in chunk_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})", chunk_ids
            ).fetchall()
        return [self._row_to_chunk(row) for row in rows]

    def get_chunks_by_node_ids(self, node_ids: list[str]) -> list[Chunk]:
        if not node_ids:
            return []
        placeholders = ",".join("?" for _ in node_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM chunks WHERE node_id IN ({placeholders})", node_ids
            ).fetchall()
        return [self._row_to_chunk(row) for row in rows]

    @staticmethod
    def _row_to_chunk(row: sqlite3.Row) -> Chunk:
        citation = Citation(**json.loads(row["citation_json"]))
        return Chunk(
            chunk_id=row["chunk_id"],
            file_id=row["file_id"],
            chunk_index=row["chunk_index"],
            text=row["text"],
            citation=citation,
            node_id=row["node_id"],
        )
