"""
DOI Resolution Utility

This module provides functionality to resolve DOI identifiers to paper metadata
using the CrossRef API and DOI.org resolver.
"""

import httpx
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


class DOIResolver:
    """Resolves DOI to paper metadata and URLs."""
    
    CROSSREF_API = "https://api.crossref.org/works/"
    DOI_ORG_RESOLVER = "https://doi.org/"
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
    
    async def resolve(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a DOI to metadata.
        
        Args:
            doi: DOI identifier (e.g., "10.1234/5678")
        
        Returns:
            Dictionary containing:
            - title: Paper title
            - authors: List of author names
            - published_date: Publication date
            - publisher: Publisher name
            - url: DOI resolver URL (always works)
            - pdf_url: Direct PDF URL (if available)
            - abstract: Abstract (if available)
        """
        if not doi or doi == "N/A":
            return None
        
        # Clean DOI (remove "doi:" prefix if present)
        clean_doi = doi.replace("doi:", "").strip()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Query CrossRef API
                response = await client.get(
                    f"{self.CROSSREF_API}{clean_doi}",
                    headers={"User-Agent": "MyRAG/1.0 (mailto:research@example.com)"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", {})
                    
                    # Extract metadata
                    metadata = {
                        "doi": clean_doi,
                        "title": self._extract_title(message),
                        "authors": self._extract_authors(message),
                        "published_date": self._extract_date(message),
                        "publisher": message.get("publisher", ""),
                        "url": f"{self.DOI_ORG_RESOLVER}{clean_doi}",
                        "pdf_url": self._extract_pdf_url(message),
                        "abstract": message.get("abstract", ""),
                        "journal": message.get("container-title", [""])[0] if message.get("container-title") else "",
                    }
                    
                    logger.info("doi_resolved", doi=clean_doi, title=metadata["title"])
                    return metadata
                else:
                    logger.warning("doi_resolution_failed", doi=clean_doi, status=response.status_code)
                    # Return minimal metadata with DOI resolver URL
                    return {
                        "doi": clean_doi,
                        "url": f"{self.DOI_ORG_RESOLVER}{clean_doi}",
                    }
                    
        except Exception as e:
            logger.error("doi_resolution_error", doi=clean_doi, error=str(e))
            # Return minimal metadata
            return {
                "doi": clean_doi,
                "url": f"{self.DOI_ORG_RESOLVER}{clean_doi}",
            }
    
    def _extract_title(self, message: dict) -> str:
        """Extract title from CrossRef response."""
        titles = message.get("title", [])
        return titles[0] if titles else ""
    
    def _extract_authors(self, message: dict) -> list:
        """Extract author names from CrossRef response."""
        authors = message.get("author", [])
        return [
            f"{author.get('given', '')} {author.get('family', '')}".strip()
            for author in authors
        ]
    
    def _extract_date(self, message: dict) -> str:
        """Extract publication date from CrossRef response."""
        date_parts = message.get("published-print", {}).get("date-parts", [[]])
        if not date_parts or not date_parts[0]:
            date_parts = message.get("published-online", {}).get("date-parts", [[]])
        
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            if len(parts) >= 1:
                year = parts[0]
                month = parts[1] if len(parts) >= 2 else 1
                day = parts[2] if len(parts) >= 3 else 1
                return f"{year}-{month:02d}-{day:02d}"
        return ""
    
    def _extract_pdf_url(self, message: dict) -> Optional[str]:
        """
        Extract PDF URL from CrossRef response.
        Note: This is often not available. Users should use the DOI URL instead.
        """
        links = message.get("link", [])
        for link in links:
            if link.get("content-type") == "application/pdf":
                return link.get("URL")
        return None
