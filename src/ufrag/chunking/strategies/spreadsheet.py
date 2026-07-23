from ufrag.ingestion.extractors.spreadsheet import SheetData
from ufrag.models import Chunk, Citation

MAX_ROW_CHUNKS_PER_SHEET = 200


def chunk_spreadsheet(
    file_id: str, filename: str, sheets: list[SheetData]
) -> tuple[list[Chunk], list[str]]:
    """Spreadsheets never go through the outline/hierarchy path — there's no

    prose heading structure to build a tree from. Instead each sheet produces
    a schema chunk, one chunk per formula cell (with the formula string and
    its evaluated value, never just the flattened value), and one chunk per
    data row when the sheet is small enough. Aggregate/arithmetic questions
    (e.g. "what's the sum of column D") are intentionally out of scope here —
    that needs a structured compute path, not chunk retrieval, and isn't
    built yet.
    """
    chunks: list[Chunk] = []
    warnings: list[str] = []
    chunk_index = 0

    def add_chunk(text: str, sheet_name: str, cell: str | None = None) -> None:
        nonlocal chunk_index
        location = {"sheet": sheet_name}
        if cell is not None:
            location["cell"] = cell
        citation = Citation(
            file_id=file_id, filename=filename, section_path=sheet_name, location=location
        )
        chunks.append(
            Chunk(
                chunk_id=f"{file_id}:chunk:{chunk_index}",
                file_id=file_id,
                chunk_index=chunk_index,
                text=text,
                citation=citation,
                node_id=None,
            )
        )
        chunk_index += 1

    for sheet in sheets:
        if not sheet.headers:
            continue

        add_chunk(
            f"Sheet '{sheet.name}' has {len(sheet.rows)} data row(s) and columns: "
            f"{', '.join(sheet.headers)}.",
            sheet.name,
        )

        for coord, formula, value in sheet.formulas:
            add_chunk(
                f"Cell {sheet.name}!{coord} contains the formula {formula}, which "
                f"evaluates to {value!r}.",
                sheet.name,
                cell=coord,
            )

        if len(sheet.rows) > MAX_ROW_CHUNKS_PER_SHEET:
            warnings.append(
                f"sheet '{sheet.name}' has {len(sheet.rows)} rows, over the "
                f"{MAX_ROW_CHUNKS_PER_SHEET}-row chunking cap — only the sheet schema "
                "and formula cells were indexed, not individual rows"
            )
            continue

        for i, row in enumerate(sheet.rows, start=2):  # row 1 is the header
            pairs = ", ".join(f"{h}={v!r}" for h, v in zip(sheet.headers, row))
            add_chunk(f"Row {i} in sheet '{sheet.name}': {pairs}", sheet.name, cell=f"row {i}")

    return chunks, warnings
