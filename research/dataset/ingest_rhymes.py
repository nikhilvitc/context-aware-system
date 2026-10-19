#!/usr/bin/env python3
"""Ingest bundled public-domain rhymes into SQLite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.dataset.db import DEFAULT_DB, init_db, insert_rhyme, upsert_license
from research.dataset.public_rhymes import (
    LICENSE_NAME,
    LICENSE_NOTES,
    LICENSE_URL,
    PUBLIC_RHYMES,
    SOURCE_NAME,
    SOURCE_URL,
    full_text,
)


def ingest(db_path: Path = DEFAULT_DB) -> int:
    conn = init_db(db_path)
    license_id = upsert_license(
        conn,
        name=LICENSE_NAME,
        url=LICENSE_URL,
        notes=LICENSE_NOTES,
    )
    for rhyme in PUBLIC_RHYMES:
        insert_rhyme(
            conn,
            rhyme_id=rhyme["rhyme_id"],
            title=rhyme["title"],
            full_text=full_text(rhyme),
            source_name=SOURCE_NAME,
            source_url=SOURCE_URL,
            license_id=license_id,
        )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) AS n FROM rhymes").fetchone()["n"]
    conn.close()
    return int(count)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    n = ingest(args.db)
    print(f"Ingested {n} rhymes into {args.db}")


if __name__ == "__main__":
    main()
