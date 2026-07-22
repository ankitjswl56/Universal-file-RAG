from ufrag.models import Section


def extract_markdown(text: str) -> list[Section]:
    lines = text.splitlines()
    headings: list[tuple[int, str, int]] = []
    in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            rest = stripped[level:]
            if 1 <= level <= 6 and (rest == "" or rest.startswith(" ")):
                headings.append((level, rest.strip(), i))

    if not headings:
        return [
            Section(
                level=0,
                title="(untitled)",
                content=text,
                location={"line_start": 1, "line_end": max(len(lines), 1)},
            )
        ]

    sections = []
    for idx, (level, title, line_idx) in enumerate(headings):
        end_line = headings[idx + 1][2] if idx + 1 < len(headings) else len(lines)
        content_lines = lines[line_idx:end_line]
        sections.append(
            Section(
                level=level,
                title=title,
                content="\n".join(content_lines),
                location={"line_start": line_idx + 1, "line_end": end_line},
            )
        )
    return sections
