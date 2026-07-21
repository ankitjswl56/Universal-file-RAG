from dataclasses import dataclass

from ufrag.ingestion.extractors.markdown import MarkdownSection

# Rough chars-per-token proxy (~4 chars/token) since no tokenizer is wired up yet.
LENGTH_GATE_CHARS = 6000
MIN_HEADINGS = 2


@dataclass
class StructureDecision:
    is_structured: bool
    reason: str


def score_markdown(sections: list[MarkdownSection], total_length: int) -> StructureDecision:
    if total_length < LENGTH_GATE_CHARS:
        return StructureDecision(
            is_structured=False,
            reason=f"content is {total_length} chars, below the {LENGTH_GATE_CHARS}-char length gate",
        )

    heading_sections = [s for s in sections if s.level > 0]
    if len(heading_sections) >= MIN_HEADINGS:
        return StructureDecision(
            is_structured=True,
            reason=f"found {len(heading_sections)} headings, building hierarchical outline",
        )

    return StructureDecision(
        is_structured=False,
        reason="no meaningful heading structure detected",
    )
