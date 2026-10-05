from typing import List, Literal, Optional
from pydantic import BaseModel


class OCRItem(BaseModel):
    text: str
    bbox: List[List[int]]
    confidence: float


class PageResult(BaseModel):
    page_number: int
    width: int
    height: int
    source: Literal["ocr", "text_layer"]
    results: List[OCRItem]


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    doc_type: Literal["image", "pdf"]
    page_count: int
    pages: List[PageResult]


class ContextRequest(BaseModel):
    document_id: str
    page: int = 0
    x: int
    y: int


class ContextResponse(BaseModel):
    selected_text: Optional[str]
    bbox: Optional[List[List[int]]]
    context: List[OCRItem]


class ExplainResponse(BaseModel):
    selected_text: str
    context: List[OCRItem]
    explanation: str
