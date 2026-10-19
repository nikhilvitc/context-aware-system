#!/usr/bin/env python3
"""Run the full RhymeTextVQA dataset pipeline end-to-end."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.dataset.annotate_auto import annotate as annotate_auto
from research.dataset.annotate_qa import annotate as annotate_qa
from research.dataset.build_pages import build as build_pages
from research.dataset.db import DEFAULT_DB
from research.dataset.export_splits import export as export_splits
from research.dataset.ingest_rhymes import ingest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--use-easyocr", action="store_true")
    parser.add_argument("--use-llm", action="store_true")
    args = parser.parse_args()

    n_rhymes = ingest(args.db)
    print(f"[1/5] ingested rhymes: {n_rhymes}")
    n_pages = build_pages(args.db)
    print(f"[2/5] built pages: {n_pages}")
    n_tokens = annotate_auto(args.db, use_easyocr=args.use_easyocr)
    print(f"[3/5] ocr tokens: {n_tokens}")
    n_qa = annotate_qa(args.db, use_llm=args.use_llm)
    print(f"[4/5] qa pairs: {n_qa}")
    counts = export_splits(args.db)
    print(f"[5/5] exported: {counts}")


if __name__ == "__main__":
    main()
