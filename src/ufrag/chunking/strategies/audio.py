from ufrag.ingestion.extractors.audio import AudioSegment
from ufrag.models import Chunk, Citation


def chunk_audio(file_id: str, filename: str, segments: list[AudioSegment]) -> list[Chunk]:
    chunks = []
    for i, seg in enumerate(segments):
        citation = Citation(
            file_id=file_id,
            filename=filename,
            section_path=seg.speaker if seg.speaker else "(transcript)",
            location={"start_s": seg.start_s, "end_s": seg.end_s},
        )
        chunks.append(
            Chunk(
                chunk_id=f"{file_id}:chunk:{i}",
                file_id=file_id,
                chunk_index=i,
                text=seg.text,
                citation=citation,
                node_id=None,
            )
        )
    return chunks
