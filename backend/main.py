import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models.schemas import DocumentResponse, ContextRequest, ContextResponse, ExplainResponse
from services.ocr_service import OCRService
from services.document_service import DocumentStore
from services.context import find_context
from services.explain import generate_explanation, ExplanationServiceUnavailable

app = FastAPI(
    title="Tap2Explain Backend",
    description="Backend for tap-guided contextual educational understanding.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}

# Load OCR once when the server starts.
ocr_service = OCRService()
document_store = DocumentStore(ocr_service, UPLOAD_DIR)


@app.get("/")
def root():
    return {"message": "Tap2Explain backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


def _serialize_document(document_id: str, document: dict) -> dict:
    return {
        "document_id": document_id,
        "filename": document["filename"],
        "doc_type": document["doc_type"],
        "page_count": len(document["pages"]),
        "pages": [
            {
                "page_number": page["page_number"],
                "width": page["width"],
                "height": page["height"],
                "source": page["source"],
                "results": page["results"],
            }
            for page in document["pages"]
        ],
    }


@app.post("/api/document", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, and PDF files are supported.",
        )

    document_id = str(uuid.uuid4())
    contents = await file.read()

    if file.content_type == "application/pdf":
        document = document_store.ingest_pdf(document_id, file.filename, contents)
    else:
        extension = ALLOWED_CONTENT_TYPES[file.content_type]
        document = document_store.ingest_image(document_id, file.filename, extension, contents)

    return _serialize_document(document_id, document)


@app.get("/api/document/{document_id}/page/{page_number}")
def get_document_page(document_id: str, page_number: int):
    page = document_store.get_page(document_id, page_number)

    if page is None:
        raise HTTPException(status_code=404, detail="Page not found.")

    return FileResponse(page["path"], media_type=page["content_type"])


@app.post("/api/context", response_model=ContextResponse)
def get_context(request: ContextRequest):
    page = document_store.get_page(request.document_id, request.page)

    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    selected, context = find_context(page["results"], request.x, request.y)

    if selected is None:
        return {"selected_text": None, "bbox": None, "context": []}

    return {
        "selected_text": selected["text"],
        "bbox": selected["bbox"],
        "context": context,
    }


@app.post("/api/explain", response_model=ExplainResponse)
def explain_context(request: ContextRequest):
    page = document_store.get_page(request.document_id, request.page)

    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    selected, context = find_context(page["results"], request.x, request.y)

    if selected is None:
        raise HTTPException(
            status_code=404,
            detail="No text found near the selected location.",
        )

    try:
        explanation = generate_explanation(
            selected_text=selected["text"],
            context=context,
        )
    except ExplanationServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "selected_text": selected["text"],
        "context": context,
        "explanation": explanation,
    }
