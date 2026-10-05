import os

import fitz
from PIL import Image

PDF_RENDER_ZOOM = 2.0


class DocumentStore:
    """
    Ingests images and PDFs, renders every page to a displayable PNG,
    and caches OCR / text-layer results per page so repeated taps don't
    re-run OCR or re-parse the file.
    """

    def __init__(self, ocr_service, upload_dir):
        self.ocr_service = ocr_service
        self.upload_dir = upload_dir
        self._documents = {}

    def _page_dir(self, document_id):
        path = os.path.join(self.upload_dir, document_id)
        os.makedirs(path, exist_ok=True)
        return path

    def ingest_image(self, document_id, filename, extension, contents):
        page_dir = self._page_dir(document_id)
        image_path = os.path.join(page_dir, f"page_0{extension}")

        with open(image_path, "wb") as f:
            f.write(contents)

        with Image.open(image_path) as img:
            width, height = img.size

        results = self.ocr_service.extract_text(image_path)

        document = {
            "filename": filename,
            "doc_type": "image",
            "pages": [
                {
                    "page_number": 0,
                    "path": image_path,
                    "content_type": "image/png" if extension == ".png" else "image/jpeg",
                    "width": width,
                    "height": height,
                    "source": "ocr",
                    "results": results,
                }
            ],
        }

        self._documents[document_id] = document
        return document

    def ingest_pdf(self, document_id, filename, contents):
        page_dir = self._page_dir(document_id)
        pdf = fitz.open(stream=contents, filetype="pdf")
        matrix = fitz.Matrix(PDF_RENDER_ZOOM, PDF_RENDER_ZOOM)
        pages = []

        for page_number, page in enumerate(pdf):
            pixmap = page.get_pixmap(matrix=matrix)
            image_path = os.path.join(page_dir, f"page_{page_number}.png")
            pixmap.save(image_path)

            words = page.get_text("words")

            if words:
                source = "text_layer"
                results = [
                    {
                        "text": word[4],
                        "bbox": [
                            [round(word[0] * PDF_RENDER_ZOOM), round(word[1] * PDF_RENDER_ZOOM)],
                            [round(word[2] * PDF_RENDER_ZOOM), round(word[1] * PDF_RENDER_ZOOM)],
                            [round(word[2] * PDF_RENDER_ZOOM), round(word[3] * PDF_RENDER_ZOOM)],
                            [round(word[0] * PDF_RENDER_ZOOM), round(word[3] * PDF_RENDER_ZOOM)],
                        ],
                        "confidence": 1.0,
                    }
                    for word in words
                ]
            else:
                # Scanned / image-only page: fall back to OCR.
                source = "ocr"
                results = self.ocr_service.extract_text(image_path)

            pages.append(
                {
                    "page_number": page_number,
                    "path": image_path,
                    "content_type": "image/png",
                    "width": pixmap.width,
                    "height": pixmap.height,
                    "source": source,
                    "results": results,
                }
            )

        pdf.close()

        document = {
            "filename": filename,
            "doc_type": "pdf",
            "pages": pages,
        }

        self._documents[document_id] = document
        return document

    def get(self, document_id):
        return self._documents.get(document_id)

    def get_page(self, document_id, page_number):
        document = self._documents.get(document_id)
        if document is None:
            return None
        if page_number < 0 or page_number >= len(document["pages"]):
            return None
        return document["pages"][page_number]
