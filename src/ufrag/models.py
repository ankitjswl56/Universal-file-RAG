from dataclasses import dataclass


@dataclass
class Citation:
    file_id: str
    filename: str
    section_path: str
    line_start: int
    line_end: int


@dataclass
class Chunk:
    chunk_id: str
    file_id: str
    chunk_index: int
    text: str
    citation: Citation
    node_id: str | None = None


@dataclass
class OutlineNode:
    node_id: str
    file_id: str
    parent_id: str | None
    title: str
    summary: str
    level: int
    ordinal: int
    line_start: int
    line_end: int
