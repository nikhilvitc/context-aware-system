from typing import List, Literal, Optional, Any
from pydantic import BaseModel, Field


class OCRItem(BaseModel):
    text: str
    bbox: List[List[float]]
    confidence: float = 1.0
    line_index: Optional[int] = None
    relations: Optional[List[dict]] = None
    score: Optional[float] = None


class PageResult(BaseModel):
    page_number: int
    width: int
    height: int
    source: Literal["ocr", "text_layer"]
    results: List[OCRItem]
    objects: List[dict] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    doc_type: Literal["image", "pdf"]
    page_count: int
    pages: List[PageResult]
    mode: Optional[str] = None
    rhyme_id: Optional[str] = None


class ContextRequest(BaseModel):
    document_id: str
    page: int = 0
    x: int
    y: int
    mode: Literal["default", "rhyme_kids"] = "default"


class RelationScore(BaseModel):
    code: str
    score: float


class ContextResponse(BaseModel):
    selected_text: Optional[str]
    selected_type: Optional[Literal["text", "object"]] = None
    bbox: Optional[List[List[float]]]
    context: List[OCRItem]
    relations: List[dict] = Field(default_factory=list)
    object_meta: Optional[dict] = None


class ExplainResponse(BaseModel):
    selected_text: str
    selected_type: Literal["text", "object"] = "text"
    context: List[OCRItem]
    explanation: str


class RhymeSummary(BaseModel):
    rhyme_id: str
    title: str
    page_count: int
