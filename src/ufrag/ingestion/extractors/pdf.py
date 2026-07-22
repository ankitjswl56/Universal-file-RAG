import statistics

import fitz

from ufrag.models import Section

MIN_TEXT_CHARS_PER_PAGE = 20
HEADING_SIZE_RATIO = 1.15
MAX_HEADING_LINE_CHARS = 120


def extract_pdf(path) -> tuple[list[Section], list[str], list[int]]:
    """Returns (sections, page_texts, scanned_pages).

    page_texts is the raw per-page text, used as the fallback source for
    per-page chunking when the document doesn't clear the structure gate.
    scanned_pages lists 1-indexed pages with next to no extractable text
    (likely image-only) — OCR for these lands in a later phase; for now
    they're just surfaced as ingestion warnings.
    """
    doc = fitz.open(path)
    try:
        page_texts = [page.get_text("text") for page in doc]
        scanned_pages = [
            i + 1 for i, text in enumerate(page_texts) if len(text.strip()) < MIN_TEXT_CHARS_PER_PAGE
        ]

        toc = doc.get_toc()
        sections = _sections_from_toc(toc, page_texts) if toc else _sections_from_font_headings(doc)
        return sections, page_texts, scanned_pages
    finally:
        doc.close()


def _sections_from_toc(toc: list, page_texts: list[str]) -> list[Section]:
    sections = []
    for idx, (level, title, page_num) in enumerate(toc):
        start_page = max(page_num, 1)
        end_page = toc[idx + 1][2] if idx + 1 < len(toc) else len(page_texts)
        end_page = max(end_page, start_page)
        content = "\n".join(page_texts[start_page - 1 : end_page])
        sections.append(
            Section(
                level=level,
                title=title.strip(),
                content=content,
                location={"page_start": start_page, "page_end": end_page},
            )
        )
    return sections


def _sections_from_font_headings(doc) -> list[Section]:
    lines: list[tuple[int, str, float]] = []
    for page_num, page in enumerate(doc, start=1):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if not text:
                    continue
                size = max(span["size"] for span in line["spans"])
                lines.append((page_num, text, size))

    if not lines:
        return [
            Section(
                level=0,
                title="(untitled)",
                content="",
                location={"page_start": 1, "page_end": max(doc.page_count, 1)},
            )
        ]

    body_size = statistics.median(size for _, _, size in lines)
    threshold = body_size * HEADING_SIZE_RATIO
    heading_indices = [
        i
        for i, (_, text, size) in enumerate(lines)
        if size >= threshold and len(text) < MAX_HEADING_LINE_CHARS
    ]

    if not heading_indices:
        full_text = "\n".join(text for _, text, _ in lines)
        pages = [p for p, _, _ in lines]
        return [
            Section(
                level=0,
                title="(untitled)",
                content=full_text,
                location={"page_start": min(pages), "page_end": max(pages)},
            )
        ]

    unique_heading_sizes = sorted({lines[i][2] for i in heading_indices}, reverse=True)
    size_to_level = {size: level + 1 for level, size in enumerate(unique_heading_sizes)}

    sections = []
    for idx, start_i in enumerate(heading_indices):
        end_i = heading_indices[idx + 1] if idx + 1 < len(heading_indices) else len(lines)
        content_lines = lines[start_i:end_i]
        pages_in_section = [p for p, _, _ in content_lines]
        sections.append(
            Section(
                level=size_to_level[lines[start_i][2]],
                title=lines[start_i][1],
                content="\n".join(t for _, t, _ in content_lines),
                location={
                    "page_start": min(pages_in_section),
                    "page_end": max(pages_in_section),
                },
            )
        )
    return sections
