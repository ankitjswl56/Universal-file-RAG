import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ufrag.models import OutlineNode

SCHEMA = """
CREATE TABLE IF NOT EXISTS outline_nodes (
    node_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    parent_id TEXT REFERENCES outline_nodes(node_id),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    level INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    location_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outline_file_id ON outline_nodes(file_id);
CREATE INDEX IF NOT EXISTS idx_outline_parent_id ON outline_nodes(parent_id);
"""


class OutlineStore:
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

    def add_nodes(self, nodes: list[OutlineNode]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO outline_nodes "
                "(node_id, file_id, parent_id, title, summary, level, ordinal, location_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        n.node_id,
                        n.file_id,
                        n.parent_id,
                        n.title,
                        n.summary,
                        n.level,
                        n.ordinal,
                        json.dumps(n.location),
                    )
                    for n in nodes
                ],
            )

    def has_tree(self, file_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM outline_nodes WHERE file_id = ? LIMIT 1", (file_id,)
            ).fetchone()
        return row is not None

    def get_tree(self, file_id: str) -> list[OutlineNode]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM outline_nodes WHERE file_id = ? ORDER BY ordinal", (file_id,)
            ).fetchall()
        return [
            OutlineNode(
                node_id=r["node_id"],
                file_id=r["file_id"],
                parent_id=r["parent_id"],
                title=r["title"],
                summary=r["summary"],
                level=r["level"],
                ordinal=r["ordinal"],
                location=json.loads(r["location_json"]),
            )
            for r in rows
        ]
