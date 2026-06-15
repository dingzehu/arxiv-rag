from collections.abc import Generator

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
MIN_CHUNK_WORDS = 50

def chunk_text(text: str) -> Generator[str, None, None]:
    """Yield overlapping word-window chunks from a plain-text string.

    Uses a sliding window of CHUNK_SIZE words, advancing by
    (CHUNK_SIZE - CHUNK_OVERLAP) words each step.
    Chunks shorter than MIN_CHUNK_WORDS are discarded.
    """
    words = text.split()
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk = words[i : i + CHUNK_SIZE]
        if len(chunk) >= MIN_CHUNK_WORDS:
            yield " ".join(chunk)