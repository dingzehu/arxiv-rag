from google import genai
from google.genai import types
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

def embed_document(text: str) -> list[float]:
    """Return a 768-float embedding vector for a document chunk.
    
    Uses task_type RETRIEVAL_DOCUMENT — call this during ingestion.
    """
    result = _client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    vector = result.embeddings[0].values  # list of 768 floats
    return vector

def embed_query(text: str) -> list[float]:
    """Return a 768-float embedding vector for a search query.
    
    Uses task_type RETRIEVAL_QUERY — call this during search
    """
    result = _client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    vector = result.embeddings[0].values  # list of 768 floats
    return vector