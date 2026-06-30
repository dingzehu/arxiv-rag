from app.services.chunker import chunk_text

def test_chunk_text_yields_chunks_for_long_text():
    result = list(chunk_text("word " * 500))
    assert len(result) > 0
    assert all(isinstance(c, str) for c in result)

def test_chunk_text_overlap():
    result = list(chunk_text(" ".join(str(i) for i in range(500))))

    for i in range(len(result)-1):
        assert result[i].split()[-80:] == result[i+1].split()[:80]

def test_chunk_text_discards_short_final_chunk():
    result = list(chunk_text("word " * 30))
    assert result == []

def test_chunk_text_empty_string():
    result = list(chunk_text("word " * 0))
    assert result == []
