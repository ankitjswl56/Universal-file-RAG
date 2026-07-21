import sqlite3
from contextlib import contextmanager
from pathlib import Path

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
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    citation_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outline_nodes (
    node_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(file_id),
    parent_id TEXT REFERENCES outline_nodes(node_id),
    title TEXT NOT NULL,
    summary TEXT,
    ordinal INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_outline_file_id ON outline_nodes(file_id);
"""


class MetadataStore:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
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
            conn.execute(
                "UPDATE files SET status = ? WHERE file_id = ?", (status, file_id)
            )

    def get_file(self, file_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM files WHERE file_id = ?", (file_id,)
            ).fetchone()

    def list_files(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM files").fetchall()
