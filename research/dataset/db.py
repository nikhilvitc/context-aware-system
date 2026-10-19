"""SQLite helpers for RhymeTextVQA."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "rhyme_textvqa.db"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.sql"


def connect(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    conn = connect(db_path)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
    return conn


def upsert_license(
    conn: sqlite3.Connection,
    name: str,
    url: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    row = conn.execute(
        "SELECT license_id FROM licenses WHERE name = ?",
        (name,),
    ).fetchone()
    if row:
        return int(row["license_id"])
    cur = conn.execute(
        "INSERT INTO licenses (name, url, notes) VALUES (?, ?, ?)",
        (name, url, notes),
    )
    conn.commit()
    return int(cur.lastrowid)


def insert_rhyme(
    conn: sqlite3.Connection,
    rhyme_id: str,
    title: str,
    full_text: str,
    source_name: str,
    source_url: Optional[str],
    license_id: int,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO rhymes
        (rhyme_id, title, full_text, source_name, source_url, license_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (rhyme_id, title, full_text, source_name, source_url, license_id),
    )


def insert_page(
    conn: sqlite3.Connection,
    page_id: str,
    rhyme_id: str,
    page_index: int,
    image_path: str,
    width: int,
    height: int,
    split: str,
    illustration_prompt: Optional[str] = None,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO pages
        (page_id, rhyme_id, page_index, image_path, width, height, split, illustration_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            page_id,
            rhyme_id,
            page_index,
            image_path,
            width,
            height,
            split,
            illustration_prompt,
        ),
    )


def replace_ocr_tokens(
    conn: sqlite3.Connection,
    page_id: str,
    tokens: Iterable[dict[str, Any]],
) -> None:
    conn.execute("DELETE FROM ocr_tokens WHERE page_id = ?", (page_id,))
    for token in tokens:
        conn.execute(
            """
            INSERT INTO ocr_tokens
            (page_id, token_index, text, x1, y1, x2, y2, confidence, line_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                page_id,
                token["token_index"],
                token["text"],
                token["x1"],
                token["y1"],
                token["x2"],
                token["y2"],
                token.get("confidence", 1.0),
                token.get("line_index"),
            ),
        )


def replace_objects(
    conn: sqlite3.Connection,
    page_id: str,
    objects: Iterable[dict[str, Any]],
) -> None:
    conn.execute("DELETE FROM objects WHERE page_id = ?", (page_id,))
    for obj in objects:
        conn.execute(
            """
            INSERT INTO objects
            (page_id, label, x1, y1, x2, y2, attributes_json, relation_hint)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                page_id,
                obj["label"],
                obj["x1"],
                obj["y1"],
                obj["x2"],
                obj["y2"],
                json.dumps(obj.get("attributes", {})),
                obj.get("relation_hint"),
            ),
        )


def replace_qa_pairs(
    conn: sqlite3.Connection,
    page_id: str,
    pairs: Iterable[dict[str, Any]],
) -> None:
    conn.execute("DELETE FROM qa_pairs WHERE page_id = ?", (page_id,))
    for pair in pairs:
        conn.execute(
            """
            INSERT INTO qa_pairs
            (qa_id, page_id, question, answers_json, answer_type, reviewed)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                pair["qa_id"],
                page_id,
                pair["question"],
                json.dumps(pair["answers"]),
                pair["answer_type"],
                int(pair.get("reviewed", 0)),
            ),
        )


def fetch_pages(conn: sqlite3.Connection, split: Optional[str] = None) -> list[sqlite3.Row]:
    if split:
        return list(
            conn.execute(
                "SELECT * FROM pages WHERE split = ? ORDER BY rhyme_id, page_index",
                (split,),
            )
        )
    return list(conn.execute("SELECT * FROM pages ORDER BY rhyme_id, page_index"))
