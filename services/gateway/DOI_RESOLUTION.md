# DOI Resolution Feature

## Overview
This feature enriches citation information by resolving DOI identifiers to full paper metadata using the CrossRef API. Users can now click links to access paper homepages and download PDFs directly from the chat interface.

## Implementation

### Backend (Gateway Service)

#### New Module: `doi_resolver.py`
- **Purpose**: Fetch paper metadata from CrossRef API
- **API Used**: `https://api.crossref.org/works/{doi}`
- **Fallback**: Always provides DOI resolver URL (`https://doi.org/{doi}`)
- **Metadata Extracted**:
  - Title
  - Authors
  - Journal name
  - Publication date
  - Publisher
  - DOI resolver URL (always available)
  - Direct PDF URL (if available from publisher)
  - Abstract

#### Enhanced Citation Model
```python
class Citation(BaseModel):
    doi: str
    pages: List[int]
    title: Optional[str] = None
    url: Optional[str] = None  # DOI resolver URL
    pdf_url: Optional[str] = None  # Direct PDF URL
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    published_date: Optional[str] = None
```

#### Integration in Chat Endpoint
1. After retrieving search results, collect unique DOIs
2. For each DOI, call `doi_resolver.resolve(doi)`
3. Merge web metadata with local metadata (pages from search results)
4. Return enriched Citation objects

### Frontend

#### Enhanced Citation Display
- **Visual Hierarchy**: Title → Authors → Journal → DOI + Pages
- **Interactive Links**:
  - 🔗 **View Paper**: Opens DOI resolver URL (redirects to publisher page)
  - 📄 **Download PDF**: Direct PDF link (if available)
- **Styling**: Card-based layout with hover effects

#### Example Output
```
📚 Sources:

┌─────────────────────────────────────────────────────┐
│ A Novel Approach to Machine Learning (2023-05-15)  │
│ John Doe, Jane Smith                                │
│ Journal of Machine Learning Research               │
│ DOI: 10.1234/5678 | Pages: 3, 5, 7                 │
│ [🔗 View Paper] [📄 Download PDF]                   │
└─────────────────────────────────────────────────────┘
```

## User Benefits

1. **Easy Access**: One-click access to paper homepages
2. **PDF Download**: Direct PDF links when available
3. **Full Context**: See authors, journal, and publication date
4. **Page Numbers**: Know exactly which pages contain relevant information
5. **Verification**: Can verify citations by visiting the source

## API Rate Limits

CrossRef API is free and does not require authentication, but:
- **Polite Pool**: Include User-Agent header (already implemented)
- **Rate Limit**: ~50 requests/second (more than sufficient for our use case)
- **Best Practice**: Results could be cached in the future

## Future Enhancements

1. **Caching**: Cache DOI metadata in database to reduce API calls
2. **Semantic Scholar Integration**: Alternative API for more metadata
3. **Citation Export**: Export citations in BibTeX/RIS format
4. **PDF Preview**: Inline PDF viewer in the UI
