from collections.abc import Generator
from app.config import settings

MIN_CHUNK_WORDS = 50

def chunk_text(text: str) -> Generator[str, None, None]:
    """Yield overlapping word-window chunks from a plain-text string.

    Uses a sliding window of CHUNK_SIZE words, advancing by
    (settings.chunk_size - settings.chunk_overlap) words each step.
    Chunks shorter than MIN_CHUNK_WORDS are discarded.
    """
    words = text.split()
    step = settings.chunk_size - settings.chunk_overlap
    for i in range(0, len(words), step):
        chunk = words[i : i + settings.chunk_size]
        if len(chunk) >= MIN_CHUNK_WORDS:
            yield " ".join(chunk)