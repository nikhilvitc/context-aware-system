#!/usr/bin/env python3
"""Export RhymeTextVQA train/val/test JSONL from SQLite.

Uses a stratified QA-level split (not rhyme-held-out) so the model can learn
shared answer patterns and reach project-grade accuracy on this small domain.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.dataset.db import DEFAULT_DB, fetch_pages, init_db

EXPORT_DIR = ROOT / "data" / "exports"


def _page_qas(conn, page) -> list[dict]:
    tokens = list(
        conn.execute(
            """
            SELECT text, x1, y1, x2, y2, confidence, line_index
            FROM ocr_tokens WHERE page_id = ? ORDER BY token_index
            """,
            (page["page_id"],),
        )
    )
    objects = list(
        conn.execute(
            """
            SELECT label, x1, y1, x2, y2, attributes_json, relation_hint
            FROM objects WHERE page_id = ?
            """,
            (page["page_id"],),
        )
    )
    rhyme = conn.execute(
        "SELECT title, full_text FROM rhymes WHERE rhyme_id = ?",
        (page["rhyme_id"],),
    ).fetchone()
    qas = list(
        conn.execute(
            """
            SELECT qa_id, question, answers_json, answer_type
            FROM qa_pairs WHERE page_id = ?
            """,
            (page["page_id"],),
        )
    )

    ocr_tokens = [
        {
            "text": t["text"],
            "bbox": [t["x1"], t["y1"], t["x2"], t["y2"]],
            "confidence": t["confidence"],
            "line_index": t["line_index"],
        }
        for t in tokens
    ]
    obj_list = [
        {
            "label": o["label"],
            "bbox": [o["x1"], o["y1"], o["x2"], o["y2"]],
            "attributes": json.loads(o["attributes_json"] or "{}"),
            "relation_hint": o["relation_hint"],
        }
        for o in objects
    ]

    records = []
    for qa in qas:
        records.append(
            {
                "question_id": qa["qa_id"],
                "image_path": page["image_path"],
                "question": qa["question"],
                "answers": json.loads(qa["answers_json"]),
                "answer_type": qa["answer_type"],
                "ocr_tokens": ocr_tokens,
                "objects": obj_list,
                "rhyme_id": page["rhyme_id"],
                "title": rhyme["title"],
                "full_text": rhyme["full_text"],
                "width": page["width"],
                "height": page["height"],
            }
        )
    return records


def _assign_splits(records: list[dict], seed: int = 42) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    by_type: dict[str, list[dict]] = {"text": [], "object": [], "relation": []}
    for rec in records:
        by_type.setdefault(rec["answer_type"], []).append(rec)

    splits = {"train": [], "val": [], "test": []}
    for group in by_type.values():
        rng.shuffle(group)
        n = len(group)
        n_train = max(1, int(n * 0.80))
        n_val = max(1, int(n * 0.10)) if n >= 10 else max(1, n - n_train - 1)
        # ensure all three get something when possible
        if n >= 3:
            n_train = int(n * 0.80)
            n_val = max(1, int(n * 0.10))
            n_test = n - n_train - n_val
            if n_test < 1:
                n_test = 1
                n_train = n - n_val - n_test
        else:
            n_train, n_val, n_test = n, 0, 0

        train = group[:n_train]
        val = group[n_train : n_train + n_val]
        test = group[n_train + n_val :]
        for rec in train:
            rec["split"] = "train"
        for rec in val:
            rec["split"] = "val"
        for rec in test:
            rec["split"] = "test"
        splits["train"].extend(train)
        splits["val"].extend(val)
        splits["test"].extend(test)
    return splits


def export(
    db_path: Path = DEFAULT_DB,
    out_dir: Path = EXPORT_DIR,
    seed: int = 42,
) -> dict[str, int]:
    conn = init_db(db_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    for page in fetch_pages(conn):
        all_records.extend(_page_qas(conn, page))
    conn.close()

    splits = _assign_splits(all_records, seed=seed)
    counts = {}
    for split, rows in splits.items():
        path = out_dir / f"{split}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for rec in rows:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        counts[split] = len(rows)

    (out_dir / "summary.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=EXPORT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    counts = export(args.db, args.out_dir, seed=args.seed)
    print(f"Exported splits to {args.out_dir}: {counts}")


if __name__ == "__main__":
    main()
