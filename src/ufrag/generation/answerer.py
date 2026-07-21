import json
from dataclasses import dataclass

from ufrag.gemini_client import GeminiClient
from ufrag.models import Chunk


@dataclass
class CitedAnswer:
    answer: str
    citations: list[dict]
    confidence: str  # "answered" | "partial" | "not_found"


def generate_answer(question: str, chunks: list[Chunk], client: GeminiClient) -> CitedAnswer:
    if not chunks:
        return CitedAnswer(
            answer="I don't have any ingested content relevant to this question.",
            citations=[],
            confidence="not_found",
        )

    context = "\n\n".join(
        f"[{i}] (file: {c.citation.filename}, section: {c.citation.section_path}, "
        f"lines: {c.citation.line_start}-{c.citation.line_end})\n{c.text}"
        for i, c in enumerate(chunks)
    )

    prompt = (
        "Answer the question using ONLY the numbered source excerpts below. Do not use "
        "outside knowledge. If the excerpts don't contain enough information to answer, "
        "say so honestly instead of guessing. If excerpts disagree with each other, point "
        "out the disagreement explicitly rather than picking one silently.\n\n"
        f"Question: {question}\n\n"
        f"Source excerpts:\n{context}\n\n"
        "Respond with ONLY a JSON object of this shape, no other text:\n"
        '{"answer": "...", "used_excerpt_indices": [0, 2], '
        '"confidence": "answered" | "partial" | "not_found"}'
    )
    raw = client.generate(prompt).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
        confidence = parsed.get("confidence", "answered")
        used_indices = (
            []
            if confidence == "not_found"
            else [
                i
                for i in parsed.get("used_excerpt_indices", [])
                if isinstance(i, int) and 0 <= i < len(chunks)
            ]
        )
        return CitedAnswer(
            answer=parsed["answer"],
            citations=[_citation_dict(chunks[i]) for i in used_indices],
            confidence=confidence,
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return CitedAnswer(answer=raw, citations=[], confidence="answered")


def _citation_dict(chunk: Chunk) -> dict:
    c = chunk.citation
    return {
        "file_id": c.file_id,
        "filename": c.filename,
        "section_path": c.section_path,
        "line_start": c.line_start,
        "line_end": c.line_end,
    }
