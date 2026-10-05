# Tap2Explain Backend

CPU-friendly first version of the Tap2Explain backend.

## Features

- FastAPI API
- CPU-only EasyOCR
- Image and PDF upload (multi-page)
- OCR text + bounding boxes, or native PDF text-layer extraction when available
- Per-document/page result caching (OCR/text-layer only runs once per page)
- Tap-coordinate based context selection
- Gemini-backed explanation service

## Setup

Create and activate a virtual environment:

### Windows

    python -m venv venv
    venv\Scripts\activate

### Linux/macOS

    python -m venv venv
    source venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

Run:

    uvicorn main:app --reload

Open:

    http://127.0.0.1:8000/docs

## Current API

### GET /

Health-style root endpoint.

### GET /health

Returns:

    {"status": "ok"}

### POST /api/document

Upload a JPG, PNG, or PDF file (multipart field `file`). Returns a
`document_id`, `doc_type` (`image` or `pdf`), `page_count`, and per-page OCR
(or native PDF text-layer) results with bounding boxes. Results are cached
in memory per document/page.

### GET /api/document/{document_id}/page/{page_number}

Returns the rendered page as a PNG/JPEG, so the frontend can display PDF
pages without doing any PDF rendering itself.

### POST /api/context

Send:

    {
      "document_id": "...",
      "page": 0,
      "x": 420,
      "y": 280
    }

The endpoint identifies the tapped OCR/text item on that page and returns
nearby context, using the cached results (no re-parsing the file).

### POST /api/explain

Same request shape as `/api/context`. Returns the selected text, its
context, and a Gemini-generated explanation.

## Next steps

1. Persist the document cache (currently in-memory, lost on restart).
2. Add image cropping around the tapped region.
3. Support `.docx` — likely via a text-only mode (no spatial layout) rather
   than full page rendering, since that needs a conversion dependency like
   LibreOffice.
