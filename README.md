# Universal File RAG

A personal project exploring hybrid retrieval-augmented generation over
heterogeneous file types — PDFs (text and scanned), Word docs, markdown,
spreadsheets (with formulas), code repositories, images, and audio.

Unlike naive vector-only RAG, this system decides per file whether to build
a structure-aware hierarchical index (for well-structured docs like
contracts, manuals, and code) on top of the always-present vector index
(used for cross-file semantic search and unstructured content). The
retrieval strategy chosen per file is surfaced explicitly in query
responses, not hidden.

This is a personal, non-commercial portfolio project. It uses
**`gemini-3.1-flash-lite`** (via the Gemini API) for all generation,
vision/OCR, and audio transcription, and the Gemini embeddings API for
vector search — chosen because Google offers free-tier access to these
models, which keeps this project runnable without incurring cost.

## Setup

Create a `.env` file in the project root with your Gemini API key:

```
GEMINI_API_KEY=your-key-here
```

The key is read at runtime and is never committed — `.env` is gitignored.

## Status

Architecture and build plan in progress. Implementation has not started yet.
