from google import genai
from google.genai import types

GENERATION_MODEL = "gemini-3.1-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072

OCR_PROMPT = (
    "Transcribe every piece of readable text in this image, in reading order. "
    "If part of it is illegible or you're not confident, wrap just that part in "
    "[unclear: ...] rather than guessing at it. If there is no text anywhere in "
    "the image, respond with exactly: NO_TEXT_FOUND"
)
CAPTION_PROMPT = (
    "Describe what this image shows in 2-3 sentences, focused on concrete "
    "details someone could later search for (objects, people, setting, any "
    "visible text or diagrams), not subjective or aesthetic commentary."
)
TRANSCRIPTION_PROMPT = (
    "Transcribe this audio. Split the transcript into natural segments by topic "
    "or pause, not word-by-word or sentence-by-sentence. For each segment, "
    "estimate its start and end time in the audio as MM:SS (your best estimate "
    "from pacing and content — exact frame-accuracy isn't expected or needed), "
    "and label the speaker if multiple speakers are distinguishable (use "
    "'Speaker 1', 'Speaker 2', etc. if you can't tell real names; omit the "
    "speaker field entirely if there's clearly just one speaker).\n\n"
    "Respond with ONLY a JSON array, no other text, shaped like:\n"
    '[{"start": "MM:SS", "end": "MM:SS", "speaker": "...", "text": "..."}, ...]'
)


class GeminiClient:
    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
        return [e.values for e in resp.embeddings]

    def generate(self, prompt: str) -> str:
        resp = self._client.models.generate_content(model=GENERATION_MODEL, contents=prompt)
        return resp.text

    def ocr_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        return self._multimodal(image_bytes, mime_type, OCR_PROMPT)

    def caption_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        return self._multimodal(image_bytes, mime_type, CAPTION_PROMPT)

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> str:
        return self._multimodal(audio_bytes, mime_type, TRANSCRIPTION_PROMPT)

    def _multimodal(self, data: bytes, mime_type: str, prompt: str) -> str:
        resp = self._client.models.generate_content(
            model=GENERATION_MODEL,
            contents=[
                types.Part.from_bytes(data=data, mime_type=mime_type),
                prompt,
            ],
        )
        return resp.text
