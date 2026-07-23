import json
import re
from dataclasses import dataclass
from pathlib import Path

from ufrag.gemini_client import GeminiClient

MIME_TYPES = {".mp3": "audio/mpeg", ".wav": "audio/wav"}


@dataclass
class AudioSegment:
    start_s: float
    end_s: float
    speaker: str | None
    text: str


def extract_audio(path: Path, client: GeminiClient) -> list[AudioSegment]:
    """Transcription is itself the extraction here, same reasoning as images —

    there's no way to parse timestamped segments out of raw audio bytes without
    the model doing the transcribing.
    """
    audio_bytes = path.read_bytes()
    mime_type = MIME_TYPES.get(path.suffix.lower(), "audio/mpeg")

    raw = client.transcribe_audio(audio_bytes, mime_type).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("expected a JSON array")
    except (json.JSONDecodeError, ValueError):
        return []

    segments = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        start_s = _parse_timestamp(item.get("start"))
        end_s = _parse_timestamp(item.get("end"))
        text = str(item.get("text", "")).strip()
        if start_s is None or end_s is None or not text:
            continue
        segments.append(
            AudioSegment(start_s=start_s, end_s=end_s, speaker=item.get("speaker"), text=text)
        )
    return segments


def _parse_timestamp(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(\d+):(\d{2})", value.strip())
    if not match:
        return None
    minutes, seconds = match.groups()
    return float(int(minutes) * 60 + int(seconds))
