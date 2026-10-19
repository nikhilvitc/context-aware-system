"""Load RhymeTextVQA pages from the research SQLite DB into the live API."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "rhyme_textvqa.db"
DATA_ROOT = ROOT / "data"


class RhymeStore:
    def __init__(self, db_path: Path = DEFAULT_DB):
        self.db_path = db_path

    def available(self) -> bool:
        return self.db_path.exists()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def list_rhymes(self) -> list[dict[str, Any]]:
        if not self.available():
            return []
        conn = self._connect()
        rows = conn.execute(
            """
            SELECT r.rhyme_id, r.title, COUNT(p.page_id) AS page_count
            FROM rhymes r
            LEFT JOIN pages p ON p.rhyme_id = r.rhyme_id
            GROUP BY r.rhyme_id
            ORDER BY r.title
            """
        ).fetchall()
        conn.close()
        return [
            {
                "rhyme_id": r["rhyme_id"],
                "title": r["title"],
                "page_count": r["page_count"],
            }
            for r in rows
        ]

    def load_rhyme_document(self, rhyme_id: str) -> Optional[dict[str, Any]]:
        if not self.available():
            return None
        conn = self._connect()
        rhyme = conn.execute(
            "SELECT * FROM rhymes WHERE rhyme_id = ?",
            (rhyme_id,),
        ).fetchone()
        if rhyme is None:
            conn.close()
            return None

        pages_rows = conn.execute(
            """
            SELECT * FROM pages WHERE rhyme_id = ?
            ORDER BY page_index
            """,
            (rhyme_id,),
        ).fetchall()

        pages = []
        for page in pages_rows:
            tokens = conn.execute(
                """
                SELECT text, x1, y1, x2, y2, confidence, line_index
                FROM ocr_tokens WHERE page_id = ? ORDER BY token_index
                """,
                (page["page_id"],),
            ).fetchall()
            objects = conn.execute(
                """
                SELECT label, x1, y1, x2, y2, attributes_json, relation_hint
                FROM objects WHERE page_id = ?
                """,
                (page["page_id"],),
            ).fetchall()

            results = []
            for t in tokens:
                results.append(
                    {
                        "text": t["text"],
                        "bbox": [
                            [t["x1"], t["y1"]],
                            [t["x2"], t["y1"]],
                            [t["x2"], t["y2"]],
                            [t["x1"], t["y2"]],
                        ],
                        "confidence": t["confidence"],
                        "line_index": t["line_index"],
                    }
                )

            obj_list = []
            for o in objects:
                obj_list.append(
                    {
                        "label": o["label"],
                        "bbox": [
                            [o["x1"], o["y1"]],
                            [o["x2"], o["y1"]],
                            [o["x2"], o["y2"]],
                            [o["x1"], o["y2"]],
                        ],
                        "attributes": json.loads(o["attributes_json"] or "{}"),
                        "relation_hint": o["relation_hint"],
                    }
                )

            abs_path = DATA_ROOT / page["image_path"]
            pages.append(
                {
                    "page_number": page["page_index"],
                    "width": page["width"],
                    "height": page["height"],
                    "source": "text_layer",
                    "path": str(abs_path),
                    "content_type": "image/png",
                    "results": results,
                    "objects": obj_list,
                    "rhyme_title": rhyme["title"],
                    "rhyme_text": rhyme["full_text"],
                }
            )

        conn.close()
        document_id = f"rhyme-{rhyme_id}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": document_id,
            "filename": f"{rhyme['title']}.png",
            "doc_type": "image",
            "mode": "rhyme_kids",
            "rhyme_id": rhyme_id,
            "pages": pages,
        }
