import json

from ufrag.gemini_client import GeminiClient
from ufrag.indexing.metadata_store import MetadataStore
from ufrag.indexing.outline_store import OutlineStore
from ufrag.models import Chunk


def hierarchical_search(
    question: str,
    file_id: str,
    client: GeminiClient,
    outline_store: OutlineStore,
    metadata_store: MetadataStore,
) -> list[Chunk]:
    nodes = outline_store.get_tree(file_id)
    if not nodes:
        return []

    listing = "\n".join(
        f"[{n.node_id}] {'  ' * (n.level - 1)}{n.title}: {n.summary}" for n in nodes
    )
    prompt = (
        "You are navigating a document's outline to find sections relevant to a question. "
        "This is a semantic judgment over what each section covers, not a keyword match "
        "against the question's wording.\n\n"
        f"Question: {question}\n\n"
        "Outline (node_id, indentation shows nesting, title: summary):\n"
        f"{listing}\n\n"
        "Return ONLY a JSON array of the node_id strings whose content is relevant "
        "to answering the question. Return an empty array if none look relevant."
    )
    raw = client.generate(prompt).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        relevant_ids = json.loads(raw)
        if not isinstance(relevant_ids, list):
            raise ValueError("expected a JSON array")
    except (json.JSONDecodeError, ValueError):
        return []

    valid_ids = {n.node_id for n in nodes}
    relevant_ids = [nid for nid in relevant_ids if nid in valid_ids]
    return metadata_store.get_chunks_by_node_ids(relevant_ids)
