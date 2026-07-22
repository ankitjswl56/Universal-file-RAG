from pathlib import Path

import typer
from qdrant_client import QdrantClient

from ufrag.config import load_settings
from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.outline_store import OutlineStore
from ufrag.indexing.vector_store import VectorStore
from ufrag.pipeline import Stores, ingest_file
from ufrag.generation.answerer import generate_answer
from ufrag.retrieval.router import retrieve

app = typer.Typer()


@app.callback()
def main():
    """Universal File RAG CLI."""


def _build_stores() -> Stores:
    settings = load_settings()
    return Stores(
        metadata=MetadataStore(settings.sqlite_path),
        outline=OutlineStore(settings.sqlite_path),
        vector=VectorStore(settings.qdrant_host, settings.qdrant_port),
        client=GeminiClient(settings.gemini_api_key),
    )


@app.command()
def status():
    """Verify config, SQLite, and Qdrant are all reachable."""
    settings = load_settings()
    typer.echo(f"Gemini API key loaded ({len(settings.gemini_api_key)} chars)")

    MetadataStore(settings.sqlite_path)
    typer.echo(f"SQLite metadata store ready at {settings.sqlite_path}")

    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    client.get_collections()
    typer.echo(f"Qdrant reachable at {settings.qdrant_host}:{settings.qdrant_port}")


@app.command()
def ingest(path: Path):
    """Ingest a file (markdown, PDF)."""
    stores = _build_stores()
    result = ingest_file(path, stores)
    typer.echo(f"file_id: {result['file_id']}")
    typer.echo(f"file_type: {result['file_type']}")
    typer.echo(f"structure_type: {result['structure_type']} ({result['structure_reason']})")
    typer.echo(f"chunks indexed: {result['chunk_count']}")
    for warning in result["warnings"]:
        typer.echo(f"warning: {warning}")


@app.command()
def query(
    question: str,
    file_id: list[str] = typer.Option(None, help="Restrict to specific file_id(s); omit for all files"),
    top_k: int = 8,
):
    """Ask a question over ingested files."""
    stores = _build_stores()
    result = retrieve(
        question,
        file_id or None,
        stores.client,
        stores.metadata,
        stores.outline,
        stores.vector,
        top_k=top_k,
    )
    answer = generate_answer(question, result.chunks, stores.client)

    typer.echo(f"\nAnswer ({answer.confidence}):\n{answer.answer}\n")

    if answer.citations:
        typer.echo("Citations:")
        for c in answer.citations:
            typer.echo(f"  - {c['label']}")

    typer.echo("\nRetrieval trace:")
    for entry in result.trace:
        typer.echo(f"  - {entry.filename}: {entry.strategy_used} — {entry.reason}")


if __name__ == "__main__":
    app()
