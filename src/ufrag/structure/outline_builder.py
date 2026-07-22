import json

from ufrag.gemini_client import GeminiClient
from ufrag.models import OutlineNode, Section

SUMMARY_CONTENT_PREVIEW_CHARS = 500


def build_outline(
    file_id: str, sections: list[Section], client: GeminiClient
) -> list[OutlineNode]:
    summaries = _summarize_sections(sections, client)

    nodes: list[OutlineNode] = []
    stack: list[tuple[int, str]] = []  # (level, node_id)
    for ordinal, (section, summary) in enumerate(zip(sections, summaries)):
        node_id = f"{file_id}:node:{ordinal}"
        level = section.level if section.level > 0 else 1
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent_id = stack[-1][1] if stack else None
        nodes.append(
            OutlineNode(
                node_id=node_id,
                file_id=file_id,
                parent_id=parent_id,
                title=section.title,
                summary=summary,
                level=level,
                ordinal=ordinal,
                location=section.location,
            )
        )
        stack.append((level, node_id))
    return nodes


def _summarize_sections(sections: list[Section], client: GeminiClient) -> list[str]:
    numbered = "\n\n".join(
        f"[{i}] Heading: {s.title}\n{s.content[:SUMMARY_CONTENT_PREVIEW_CHARS]}"
        for i, s in enumerate(sections)
    )
    prompt = (
        "For each numbered section below, write a one-sentence summary of what it covers.\n"
        "Respond with ONLY a JSON array of strings, one per section, in the same order, "
        "with no other text or markdown formatting.\n\n" + numbered
    )
    raw = client.generate(prompt).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        summaries = json.loads(raw)
        if not isinstance(summaries, list) or len(summaries) != len(sections):
            raise ValueError("summary count mismatch")
        return [str(s) for s in summaries]
    except (json.JSONDecodeError, ValueError):
        return [s.content.strip().splitlines()[0][:200] if s.content.strip() else s.title for s in sections]
