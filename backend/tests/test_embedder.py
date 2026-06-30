from unittest.mock import patch, MagicMock
from app.services.embedder import embed_document, embed_query


def test_embed_document_returns_vector():
    with patch("app.services.embedder._client") as mock_client:
        fake_values = [0.1] * 768
        mock_embedding = MagicMock()
        mock_embedding.values = fake_values
        mock_result = MagicMock()
        mock_result.embeddings = [mock_embedding]

        mock_client.models.embed_content.return_value = mock_result

        result = embed_document("some text")

        assert isinstance(result, list)
        assert len(result) == 768

def test_embed_query_returns_vector():
    with patch("app.services.embedder._client") as mock_client:
        fake_value = [0.1] * 768
        mock_embedding = MagicMock()
        mock_embedding.values = fake_value
        mock_result = MagicMock()
        mock_result.embeddings = [mock_embedding]

        mock_client.models.embed_content.return_value = mock_result

        result = embed_query("some text")

        assert isinstance(result, list)
        assert len(result) == 768