import os
import io
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
import uuid
from .logger import setup_logger

logger = setup_logger("ingestion_processor")

# Configuration
GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")


def extract_metadata_grobid(file_content: bytes, filename: str) -> dict:
    """
    Extracts metadata (title, doi, authors) using Grobid.
    Falls back to basic metadata if Grobid fails.
    """
    metadata = {"title": filename, "doi": None, "authors": []}  # Default fallback

    try:
        files = {"input": (filename, io.BytesIO(file_content), "application/pdf")}
        # processHeaderDocument is faster than fullText
        response = requests.post(
            f"{GROBID_URL}/api/processHeaderDocument", files=files, timeout=5
        )

        if response.status_code == 200:
            xml_content = response.text
            soup = BeautifulSoup(xml_content, "xml")

            # Extract Title
            title_node = soup.find("title", type="main")
            if title_node and title_node.text:
                metadata["title"] = title_node.text.strip()

            # Extract DOI
            idno_node = soup.find("idno", type="DOI")
            if idno_node and idno_node.text:
                metadata["doi"] = idno_node.text.strip()

            # Extract Authors (simplified)
            author_nodes = soup.find_all("author")
            authors = []
            for author in author_nodes:
                persName = author.find("persName")
                if persName:
                    forename = persName.find("forename")
                    surname = persName.find("surname")
                    name_parts = []
                    if forename:
                        name_parts.append(forename.text)
                    if surname:
                        name_parts.append(surname.text)
                    if name_parts:
                        authors.append(" ".join(name_parts))
            metadata["authors"] = authors

    except Exception as e:
        logger.error(f"Grobid extraction failed: {e}")
        # Basic PDF metadata fallback
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            if doc.metadata.get("title"):
                metadata["title"] = doc.metadata["title"]
        except Exception:
            pass

    return metadata


def extract_text_from_pdf(file_content: bytes) -> list:
    """
    Extracts text from PDF page by page.
    Returns a list of dicts: {'page': int, 'text': str}
    """
    pages_content = []
    doc = fitz.open(stream=file_content, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            pages_content.append({"page": page_num + 1, "text": text})

    return pages_content


def recursive_character_chunking(
    text: str, chunk_size: int = 4000, overlap: int = 200
) -> list:
    """
    Simple recursive character splitter.
    Prioritizes splitting by \n\n, then \n, then space.
    Approximating 1000 tokens ~ 4000 characters.
    """
    separators = ["\n\n", "\n", " ", ""]
    chunks = []

    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            # Try to find a separator to break at (searching backwards from 'end')
            for sep in separators:
                if sep == "":
                    continue  # Default fallback

                # Search for separator in the overlap area effectively
                # actually, we want to split *closest* to the end, but before it.
                # Let's search in the last `overlap` + extra chars of the chunk

                # Simple approach: find rfind of separator within the chunk window
                sep_pos = text.rfind(sep, start, end)
                if sep_pos != -1 and sep_pos > start + (chunk_size // 2):
                    # Only accept if it's reasonably far in the chunk, to avoid tiny chunks
                    end = sep_pos + len(sep)
                    break

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(chunk_text)

        # Move start forward, accounting for overlap
        start = end - overlap if end < len(text) else end

        # Prevent infinite loops if overlap >= chunk_size or we didn't move
        if start >= end:
            start = end

    return chunks


def create_chunks(pages_content: list, metadata: dict) -> list:
    """
    Create chunks from pages content and attach metadata.
    """
    processed_chunks = []

    # We can chunk per page or across pages.
    # Specs: "Iterate through pages... Extract text... Chunking"
    # Usually better to chunk per page to keep page citation accurate,
    # or handle the boundary carefully. Let's do strictly per page for simplicity of citation.

    for page_item in pages_content:
        raw_text = page_item["text"]
        page_num = page_item["page"]

        # Spec: "Size: 1000 tokens", "Recursive Character or Token-based".
        # 1000 tokens is roughly 3000-4000 characters.
        # I will use 3500 chars as a safe approximation for 1000 tokens if no tokenizer is present.
        text_chunks = recursive_character_chunking(
            raw_text, chunk_size=3500, overlap=500
        )

        for txt in text_chunks:
            # Create a deterministic ID
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, txt))

            chunk_data = {
                "id": chunk_id,
                "text": txt,
                "metadata": {
                    "doi": metadata.get("doi"),
                    "title": metadata.get("title"),
                    "page": page_num,
                    "authors": metadata.get("authors"),
                },
            }
            processed_chunks.append(chunk_data)

    return processed_chunks
