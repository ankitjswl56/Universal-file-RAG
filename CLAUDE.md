# Universal File RAG

Personal portfolio project. A system that ingests heterogeneous file types,
indexes them with a hybrid strategy, and answers questions about their
content with exact source citations — refusing to answer rather than
hallucinating when the content isn't there.

## Model / provider

This project uses **only Gemini**, specifically `gemini-3.1-flash-lite`, for
every generation, vision/OCR, and audio-transcription task, plus the Gemini
embeddings API (`text-embedding-004` or current equivalent) for the vector
layer. This is a deliberate choice, not a placeholder — Google's free tier
makes this project runnable at zero cost. Do not introduce Anthropic/OpenAI
clients or other model providers without being asked.

The API key is read from `.env` as `GEMINI_API_KEY` (gitignored, never
committed). Call Gemini via the `google-genai` SDK directly — no LiteLLM or
other abstraction layer unless explicitly requested.

## Architecture

Five stages, each independently testable:

```
Ingestion → Structure Analysis → Chunking → Indexing → Retrieval → Answer Generation
```

The core design rule: **vector embeddings are built for every file, no
exceptions** — this is the substrate that makes cross-file queries possible.
The **hierarchical/outline index is additive and per-file** — built only for
files whose `structure_score` clears a threshold (contracts, manuals, code,
anything with real heading/section structure). A file without one isn't
"vector-less instead of hierarchical" — it just has the always-present
vector layer and nothing extra. The router picks which layer(s) to use per
query, and every query response must include a `retrieval_trace` explaining
which strategy was used per file and why — this explainability is a
first-class requirement, not a debug feature.

An MCP server layer wraps the finished pipeline as tools; it is built last,
against a working system, not designed in parallel with it.

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python |
| Orchestration | Hand-rolled — no LangChain/LlamaIndex. The whole point of this project is that the hybrid routing logic is visible and explainable, which a framework retriever abstraction would bury |
| Generation / vision-OCR / transcription | `gemini-3.1-flash-lite` via `google-genai` |
| Embeddings | Gemini embeddings API (`gemini-embedding-001`, 3072-dim — `text-embedding-004` is not available on the current API version/key) |
| Vector DB | Qdrant (local, via docker-compose) — chosen for native payload filtering and hybrid sparse+dense search |
| Metadata / outline store | SQLite |
| PDF parsing | PyMuPDF (`fitz`) — text + page position, detects scanned (no text layer) pages |
| DOCX | `python-docx` |
| Spreadsheets | `openpyxl` (formulas + cached values) + pandas |
| Code | `tree-sitter` |
| MCP | official `mcp` Python SDK |

## Hybrid retrieval decision (structure_score)

Computed once per file, no LLM call needed:

1. Native structural markers (PDF bookmarks/TOC, DOCX heading styles, Markdown `#`, code AST) — strong positive signal
2. Heading/style density relative to content length
3. OCR/vision-confidence veto — if the model flags text as illegible/uncertain, treat structure as unreliable even if headings were detected
4. Length gate — below ~1,500 tokens, skip hierarchical indexing regardless of other signals
5. Formatting uniformity — mostly similar-length, marker-free paragraphs implies unstructured prose

Above threshold → build a hierarchical outline tree (our own algorithm,
modeled on PageIndex's approach of LLM-guided navigation over node
summaries rather than embedding similarity — not the PageIndex library
itself) *in addition to* embedding leaf chunks. Below → vector-only.

At retrieval time, tree-guided navigation is attempted for **every** query
against a file that has a tree — it is never gated on the query containing
an explicit anchor phrase like "section 3," since the LLM judges relevance
against node summaries semantically, not by keyword match. Vector search
also always runs. What an explicit anchor phrase changes is only how much
the tree path is trusted to short-circuit: with a clear anchor, resolve
straight to that node and skip broad vector search over the rest of the
file; without one, run both paths and merge their candidate chunks before
ranking. So a file's tree can surface relevant content even when the
question never names a section — it is only excluded from a query's
candidate pool when the file has no tree at all.

## Chunking rules

Golden rule: never let overlap cross a structural boundary (page, section,
function, sheet) — that's where citations become wrong.

`Section`, `OutlineNode`, and `Citation` (in `models.py`) are shared across
every file type — none of them hardcode line numbers or pages. Each carries
a generic `location: dict` whose keys are whatever's appropriate for that
source (`{"line_start", "line_end"}` for markdown, `{"page_start",
"page_end"}` for PDF; a future spreadsheet extractor would use
`{"sheet", "cell"}`, audio would use `{"start_s", "end_s"}`). `structure_scorer`
and `outline_builder` are fully generic over `Section` and never branch on
file type. `chunking/base.py:chunk_structured` is likewise shared by every
type that has an outline tree. Only two things are ever type-specific: the
extractor (raw file → `Section` list) and the unstructured/no-tree chunker
(since the natural chunk boundary differs — paragraphs for text, pages for
PDF, rows for spreadsheets, etc.). Adding a new file type should mean
writing an extractor and, if needed, an unstructured chunker — not touching
retrieval, indexing, or answer generation.

- Structured PDF/DOCX/Markdown: chunk by section from the outline, ~500–800 tokens, overlap only within a section
- Scanned PDF/images: OCR via Gemini vision, chunked per page (never merged across pages), confidence is model-self-reported, not a numeric score
- Spreadsheets (implemented — `ingestion/extractors/spreadsheet.py`, `chunking/strategies/spreadsheet.py`): never flatten to plain text. One schema chunk per sheet; formula cells indexed individually with cell ref + formula + evaluated value; row-level chunks (capped at 200 rows/sheet, else schema+formulas only) when rows are clearly one-entity-each. Skips the outline/hierarchy path entirely — no prose headings to build a tree from, always `vector_only`. **Not yet implemented**: routing aggregate/arithmetic questions ("what's the sum of column D") to a structured-query (pandas) path — these currently just go through normal RAG retrieval same as anything else, which works if the answer is a single cell/row but won't correctly answer true aggregate questions over many rows
- Code: chunk per function/class via tree-sitter AST boundaries; a separate non-vector import/call graph answers structural questions ("what calls this")
- Audio: transcribed directly by Gemini (no Whisper), chunked by topic/pause boundary; timestamps are model-estimated, not frame-exact — say so in citations, don't overstate precision

Every chunk, regardless of type, carries a `citation` object with
type-specific fields (page / section_path / sheet+cell / line_range /
timestamp_range) so answer generation always has something renderable.

## Answer generation rules

- Must cite exact location per the chunk's citation object
- Must say "I don't know" / not-found honestly rather than filling gaps
- Must detect and surface conflicting facts across retrieved chunks (present both with citations) rather than silently picking one

## MCP tool interface (build last)

```
ingest_file(path_or_url, tags?) → {file_id, file_type, status, structure_summary, warnings}
list_files() → [{file_id, filename, type, ingested_at, structure_type}]
query_documents(question, file_ids?, top_k?, mode?) → {answer, citations, retrieval_trace, confidence}
get_file_outline(file_id) → hierarchical tree
get_chunk(file_id, chunk_id) → raw chunk text + citation
delete_file(file_id)
```

## Folder structure

```
src/ufrag/
├── ingestion/        # detector.py, extractors/{pdf,docx,markdown,spreadsheet,code,image,audio}.py
├── structure/        # outline_builder.py, structure_scorer.py, code_graph.py
├── chunking/         # base.py, strategies/
├── indexing/         # vector_store.py, outline_store.py, metadata_store.py
├── retrieval/         # router.py, vector_search.py, hierarchical_search.py, reranker.py
├── generation/       # answerer.py, groundedness.py
├── mcp_server/       # server.py, tools.py
└── api/              # optional thin demo API
tests/fixtures/        # one sample file per supported type
scripts/demo_cli.py
```

## Build order (simplest working version first)

1. Skeleton — repo scaffold, SQLite, Qdrant via docker-compose, no MCP
2. Markdown only, end-to-end (proves the whole pipeline on the simplest structured case)
3. Add text-based PDF (introduces real outline-building + structure_score)
4. Add unstructured `.txt` (confirms vector-only fallback + ships `retrieval_trace`)
5. Multi-file querying (merge/re-rank across files, conflict detection)
6. DOCX + spreadsheets (formula-aware chunking, structured-query sub-path)
7. OCR path — scanned PDFs + images via Gemini vision
8. Audio via Gemini transcription
9. Code repositories — tree-sitter, import graph
10. MCP server — wrap the proven internals as tools
11. Polish — groundedness hardening, edge cases, optional demo UI

Do not skip ahead to later phases before earlier ones work end-to-end with
real fixture files — the hybrid decision logic (this project's core
differentiator) has to be validated on simple cases (phases 2–4) before
building out the bespoke per-type extractors.

## Known constraints to design around

- Gemini free-tier rate limits (RPM/RPD) apply across generation, vision, and
  transcription since they're all the same model — ingestion needs
  throttling/backoff from the start, not bolted on later
- No word-level audio timestamps or numeric OCR confidence (traded away by
  going Gemini-only instead of Whisper/Tesseract) — citations for audio/OCR
  content should reflect that this is approximate, not exact
- Spreadsheet formula cells only have a cached value if the file was actually
  opened/saved by a real spreadsheet app (Excel, Sheets, LibreOffice) at
  least once — openpyxl doesn't evaluate formulas itself. Files generated
  straight from a script (pandas/openpyxl exports, our own test fixtures)
  have no cached value at all. `ingestion/extractors/spreadsheet.py` falls
  back to evaluating exactly two patterns itself (`SUM` over a same-column
  range, and a single binary op between two cell refs) when no cached value
  exists; anything more complex is left as `None` rather than guessed at —
  this is a narrow fallback, not a general formula engine
