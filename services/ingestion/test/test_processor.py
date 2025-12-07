from unittest.mock import patch, MagicMock
from services.ingestion.processor import (
    recursive_character_chunking,
    extract_metadata_grobid,
    create_chunks,
)


# --- recursive_character_chunking Tests ---
def test_recursive_character_chunking_simple():
    text = "Hello world. " * 10
    chunks = recursive_character_chunking(text, chunk_size=50, overlap=10)
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk) <= 50


def test_recursive_character_chunking_overlap():
    text = "0123456789" * 5  # 50 chars
    # chunk_size=20, overlap=5
    # Expected: "01234567890123456789" (20), next starts at 15 "56789..."
    chunks = recursive_character_chunking(text, chunk_size=20, overlap=5)
    assert len(chunks) > 0
    assert chunks[0] == "01234567890123456789"
    assert chunks[1].startswith("56789")


# --- extract_metadata_grobid Tests ---
@patch("services.ingestion.processor.requests.post")
def test_extract_metadata_grobid_success(mock_post):
    # Mock successful Grobid response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <TEI>
        <teiHeader>
            <titleStmt>
                <title type="main">Test Paper Title</title>
            </titleStmt>
            <sourceDesc>
                <biblStruct>
                    <idno type="DOI">10.1234/test</idno>
                    <analytic>
                        <author>
                            <persName>
                                <forename>John</forename>
                                <surname>Doe</surname>
                            </persName>
                        </author>
                    </analytic>
                </biblStruct>
            </sourceDesc>
        </teiHeader>
    </TEI>
    """
    mock_post.return_value = mock_response

    metadata = extract_metadata_grobid(b"dummy pdf content", "test.pdf")

    assert metadata["title"] == "Test Paper Title"
    assert metadata["doi"] == "10.1234/test"
    assert "John Doe" in metadata["authors"]


@patch("services.ingestion.processor.requests.post")
def test_extract_metadata_grobid_failure(mock_post):
    # Mock failed Grobid response
    mock_post.side_effect = Exception("Grobid down")

    # It should fallback to filename as title
    metadata = extract_metadata_grobid(b"dummy pdf content", "fallback.pdf")

    assert metadata["title"] == "fallback.pdf"
    assert metadata["doi"] is None


# --- create_chunks Tests ---
def test_create_chunks():
    pages_content = [
        {"page": 1, "text": "Page 1 content."},
        {"page": 2, "text": "Page 2 content."},
    ]
    metadata = {"title": "Test", "doi": "10.1000/1", "authors": ["Me"]}

    chunks = create_chunks(pages_content, metadata)

    assert len(chunks) == 2
    assert chunks[0]["metadata"]["page"] == 1
    assert chunks[0]["metadata"]["title"] == "Test"
    assert chunks[1]["metadata"]["page"] == 2
    assert chunks[1]["text"] == "Page 2 content."
    assert "id" in chunks[0]
