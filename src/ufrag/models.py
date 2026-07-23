from dataclasses import dataclass


def _format_timestamp(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


@dataclass
class Citation:
    file_id: str
    filename: str
    section_path: str
    # type-specific location, e.g. {"line_start": 1, "line_end": 10} for text/markdown
    # or {"page_start": 3, "page_end": 3} for PDF. Only the relevant keys are present.
    location: dict

    def label(self) -> str:
        loc = self.location
        if "page_start" in loc:
            p1, p2 = loc["page_start"], loc["page_end"]
            page_str = f"page {p1}" if p1 == p2 else f"pages {p1}-{p2}"
            return f"{self.filename} → {self.section_path} ({page_str})"
        if "para_start" in loc:
            p1, p2 = loc["para_start"], loc["para_end"]
            para_str = f"paragraph {p1}" if p1 == p2 else f"paragraphs {p1}-{p2}"
            return f"{self.filename} → {self.section_path} ({para_str})"
        if "cell" in loc:
            return f"{self.filename} → {loc['sheet']}!{loc['cell']}"
        if "sheet" in loc:
            return f"{self.filename} → sheet '{loc['sheet']}'"
        if "start_s" in loc:
            t1, t2 = _format_timestamp(loc["start_s"]), _format_timestamp(loc["end_s"])
            return f"{self.filename} → {self.section_path} (~{t1}-{t2})"
        if "line_start" in loc:
            l1, l2 = loc["line_start"], loc["line_end"]
            return f"{self.filename} → {self.section_path} (lines {l1}-{l2})"
        return f"{self.filename} → {self.section_path}"


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
