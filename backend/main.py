import os
import uuid

import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image

from models.schemas import (
    DocumentResponse,
    ContextRequest,
    ContextResponse,
    ExplainResponse,
    RhymeSummary,
)
from services.ocr_service import OCRService
from services.document_service import DocumentStore
from services.context import find_context
from services.relations import find_tap_target, score_relations
from services.rhyme_store import RhymeStore
from services.explain import (
    generate_explanation,
    generate_rhyme_kids_explanation,
    fallback_rhyme_kids_explanation,
    fallback_text_explanation,
    ExplanationServiceUnavailable,
)

app = FastAPI(
    title="Tap2Explain Backend",
    description="Backend for tap-guided contextual educational understanding.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
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

ocr_service = OCRService()
document_store = DocumentStore(ocr_service, UPLOAD_DIR)
rhyme_store = RhymeStore()


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
        "mode": document.get("mode"),
        "rhyme_id": document.get("rhyme_id"),
        "pages": [
            {
                "page_number": page["page_number"],
                "width": page["width"],
                "height": page["height"],
                "source": page["source"],
                "results": page["results"],
                "objects": page.get("objects", []),
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
        document = document_store.ingest_image(
            document_id, file.filename, extension, contents
        )

    return _serialize_document(document_id, document)


@app.get("/api/document/{document_id}/page/{page_number}")
def get_document_page(document_id: str, page_number: int):
    page = document_store.get_page(document_id, page_number)

    if page is None:
        raise HTTPException(status_code=404, detail="Page not found.")

    return FileResponse(page["path"], media_type=page["content_type"])


@app.get("/api/rhymes", response_model=list[RhymeSummary])
def list_rhymes():
    return rhyme_store.list_rhymes()


@app.post("/api/rhymes/{rhyme_id}/open", response_model=DocumentResponse)
def open_rhyme(rhyme_id: str):
    document = rhyme_store.load_rhyme_document(rhyme_id)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Rhyme not found. Build the dataset with research/build_dataset.py first.",
        )
    document_id = document.pop("document_id")
    document_store.register_document(document_id, document)
    return _serialize_document(document_id, document)


def _load_page_image(page: dict):
    try:
        with Image.open(page["path"]) as img:
            return np.array(img.convert("RGB"))
    except Exception:
        return None


def _resolve_selection(page: dict, x: int, y: int, mode: str):
    objects = page.get("objects") or []
    if mode == "rhyme_kids":
        selected, selected_type = find_tap_target(page["results"], objects, x, y)
        if selected is None:
            return None, "text", [], None
        image = _load_page_image(page)
        # Neighbor pool: OCR tokens + object labels as pseudo-tokens
        neighbors = list(page["results"])
        for obj in objects:
            neighbors.append(
                {
                    "text": obj["label"],
                    "bbox": obj["bbox"],
                    "confidence": 1.0,
                    "line_index": None,
                }
            )
        context = score_relations(
            selected,
            neighbors,
            image,
            page["width"],
            page["height"],
        )
        object_meta = None
        if selected_type == "object":
            object_meta = {
                "label": selected.get("label") or selected.get("text"),
                "attributes": selected.get("attributes", {}),
                "relation_hint": selected.get("relation_hint"),
            }
        return selected, selected_type, context, object_meta

    selected, context = find_context(page["results"], x, y)
    return selected, "text", context or [], None


@app.post("/api/context", response_model=ContextResponse)
def get_context(request: ContextRequest):
    page = document_store.get_page(request.document_id, request.page)

    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    selected, selected_type, context, object_meta = _resolve_selection(
        page, request.x, request.y, request.mode
    )

    if selected is None:
        return {
            "selected_text": None,
            "selected_type": None,
            "bbox": None,
            "context": [],
            "relations": [],
            "object_meta": None,
        }

    relations = []
    for item in context:
        for rel in item.get("relations") or []:
            relations.append(
                {
                    "neighbor": item.get("text"),
                    "code": rel["code"],
                    "score": rel["score"],
                }
            )

    return {
        "selected_text": selected.get("text") or selected.get("label"),
        "selected_type": selected_type,
        "bbox": selected["bbox"],
        "context": context,
        "relations": relations,
        "object_meta": object_meta,
    }


@app.post("/api/explain", response_model=ExplainResponse)
def explain_context(request: ContextRequest):
    page = document_store.get_page(request.document_id, request.page)

    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    selected, selected_type, context, object_meta = _resolve_selection(
        page, request.x, request.y, request.mode
    )

    if selected is None:
        raise HTTPException(
            status_code=404,
            detail="No text or object found near the selected location.",
        )

    selected_text = selected.get("text") or selected.get("label")

    try:
        if request.mode == "rhyme_kids":
            explanation = generate_rhyme_kids_explanation(
                selected_text=selected_text,
                selected_type=selected_type,
                context=context,
                rhyme_title=page.get("rhyme_title"),
                rhyme_text=page.get("rhyme_text"),
                object_meta=object_meta,
            )
        else:
            explanation = generate_explanation(
                selected_text=selected_text,
                context=context,
            )
    except (ExplanationServiceUnavailable, Exception):
        # Never block the UI — always return a usable local explanation.
        if request.mode == "rhyme_kids":
            explanation = fallback_rhyme_kids_explanation(
                selected_text=selected_text,
                selected_type=selected_type,
                object_meta=object_meta,
                rhyme_title=page.get("rhyme_title"),
            )
        else:
            explanation = fallback_text_explanation(selected_text, context)

    return {
        "selected_text": selected_text,
        "selected_type": selected_type,
        "context": context,
        "explanation": explanation,
    }
