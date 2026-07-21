import typer
from qdrant_client import QdrantClient

from ufrag.config import load_settings
from ufrag.indexing.metadata_store import MetadataStore

app = typer.Typer()


@app.callback()
def main():
    """Universal File RAG CLI."""


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


if __name__ == "__main__":
    app()
