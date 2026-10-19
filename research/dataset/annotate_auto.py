#!/usr/bin/env python3
"""Seed OCR tokens and illustration objects into the DB.

Uses layout ground-truth from build_pages by default (exact boxes).
Optionally runs EasyOCR to overwrite tokens when --use-easyocr is set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.dataset.db import (
    DEFAULT_DB,
    fetch_pages,
    init_db,
    replace_objects,
    replace_ocr_tokens,
)

PAGES_DIR = ROOT / "data" / "pages"


def _load_layout_gt(pages_dir: Path) -> dict:
    path = pages_dir / "_layout_gt.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run build_pages.py before annotate_auto.py."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _easyocr_tokens(image_path: Path) -> list[dict]:
    import easyocr
    import numpy as np
    from PIL import Image

    reader = easyocr.Reader(["en"], gpu=False)
    image = np.array(Image.open(image_path).convert("RGB"))
    detections = reader.readtext(image)
    tokens = []
    for idx, (bbox, text, conf) in enumerate(detections):
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        tokens.append(
            {
                "token_index": idx,
                "text": text,
                "x1": float(min(xs)),
                "y1": float(min(ys)),
                "x2": float(max(xs)),
                "y2": float(max(ys)),
                "confidence": float(conf),
                "line_index": None,
            }
        )
    return tokens


def annotate(db_path: Path = DEFAULT_DB, use_easyocr: bool = False) -> int:
    conn = init_db(db_path)
    layout = _load_layout_gt(PAGES_DIR)
    pages = fetch_pages(conn)
    for page in pages:
        page_id = page["page_id"]
        gt = layout[page_id]
        if use_easyocr:
            abs_image = ROOT / "data" / page["image_path"]
            tokens = _easyocr_tokens(abs_image)
        else:
            tokens = gt["tokens"]
        replace_ocr_tokens(conn, page_id, tokens)
        replace_objects(conn, page_id, gt["objects"])
    conn.commit()
    n = conn.execute("SELECT COUNT(*) AS n FROM ocr_tokens").fetchone()["n"]
    conn.close()
    return int(n)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--use-easyocr",
        action="store_true",
        help="Run EasyOCR instead of layout ground-truth tokens.",
    )
    args = parser.parse_args()
    n = annotate(args.db, use_easyocr=args.use_easyocr)
    print(f"Annotated OCR tokens: {n}")


if __name__ == "__main__":
    main()
