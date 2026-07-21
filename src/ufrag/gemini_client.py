from google import genai

GENERATION_MODEL = "gemini-3.1-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072


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
