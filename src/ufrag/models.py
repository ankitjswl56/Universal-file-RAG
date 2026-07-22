from dataclasses import dataclass


@dataclass
class Citation:
    file_id: str
    filename: str
    section_path: str
    # type-specific location, e.g. {"line_start": 1, "line_end": 10} for text/markdown
    # or {"page_start": 3, "page_end": 3} for PDF. Only the relevant keys are present.
    location: dict

    def label(self) -> str:
        if "page_start" in self.location:
            p1, p2 = self.location["page_start"], self.location["page_end"]
            page_str = f"page {p1}" if p1 == p2 else f"pages {p1}-{p2}"
            return f"{self.filename} → {self.section_path} ({page_str})"
        l1, l2 = self.location.get("line_start"), self.location.get("line_end")
        return f"{self.filename} → {self.section_path} (lines {l1}-{l2})"


@dataclass
class Chunk:
    chunk_id: str
    file_id: str
    chunk_index: int
    text: str
    citation: Citation
    node_id: str | None = None


@dataclass
class Section:
    level: int  # 0 = no heading/native structure detected for this section
    title: str
    content: str
    location: dict


@dataclass
class OutlineNode:
    node_id: str
    file_id: str
    parent_id: str | None
    title: str
    summary: str
    level: int
    ordinal: int
    location: dict
