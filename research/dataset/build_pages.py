#!/usr/bin/env python3
"""Compose picture-book style page images for each rhyme and register them in SQLite."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.dataset.db import DEFAULT_DB, init_db, insert_page
from research.dataset.public_rhymes import PUBLIC_RHYMES

PAGE_W = 768
PAGE_H = 1024
PAGES_DIR = ROOT / "data" / "pages"


def _font(size: int) -> ImageFont.ImageFont:
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        path = Path(name)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _palette(seed: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    digest = hashlib.md5(seed.encode()).hexdigest()
    hue = int(digest[:2], 16) / 255.0
    bg = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.18, 0.96))
    accent = tuple(int(c * 255) for c in colorsys.hsv_to_rgb((hue + 0.35) % 1.0, 0.55, 0.75))
    ink = (40, 36, 48)
    return bg, accent, ink  # type: ignore[return-value]


def _draw_illustration(
    draw: ImageDraw.ImageDraw,
    objects: list[dict],
    accent: tuple[int, int, int],
) -> list[dict]:
    """Draw simple geometric stand-ins for illustration objects; return bboxes."""
    placed: list[dict] = []
    region = (60, 90, PAGE_W - 60, 380)
    n = max(1, len(objects))
    gap = (region[2] - region[0]) // n

    for i, obj in enumerate(objects):
        cx = region[0] + gap * i + gap // 2
        cy = (region[1] + region[3]) // 2
        size = 70 + (i % 3) * 12
        x1, y1, x2, y2 = cx - size, cy - size, cx + size, cy + size
        label = obj["label"]

        if label in {"star", "moon"}:
            draw.ellipse([x1, y1, x2, y2], fill=accent, outline=(30, 30, 30), width=3)
        elif label in {"sheep", "lamb", "cow", "dog", "cat", "mouse", "monkey", "spider"}:
            draw.rounded_rectangle(
                [x1, y1, x2, y2],
                radius=28,
                fill=accent,
                outline=(30, 30, 30),
                width=3,
            )
        elif label in {"hill", "farm", "wall", "tree", "stream", "sky"}:
            draw.polygon(
                [(x1, y2), ((x1 + x2) // 2, y1), (x2, y2)],
                fill=accent,
                outline=(30, 30, 30),
            )
        else:
            draw.rectangle([x1, y1, x2, y2], fill=accent, outline=(30, 30, 30), width=3)

        draw.text((x1 + 8, y2 - 28), label, fill=(20, 20, 20), font=_font(18))
        placed.append(
            {
                "label": label,
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "attributes": {"category": obj.get("category", "object")},
                "relation_hint": obj.get("relation_hint"),
            }
        )
    return placed


def _layout_tokens(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    ink: tuple[int, int, int],
) -> list[dict]:
    """Draw rhyme lines and return word-level boxes (ground-truth OCR)."""
    font = _font(34)
    title_font = _font(28)
    tokens: list[dict] = []
    y = 430
    token_index = 0

    for line_index, line in enumerate(lines):
        x = 70
        words = line.split()
        for word in words:
            bbox = draw.textbbox((x, y), word, font=font)
            draw.text((x, y), word, fill=ink, font=font)
            tokens.append(
                {
                    "token_index": token_index,
                    "text": word.strip(",.;:!?"),
                    "raw": word,
                    "x1": float(bbox[0]),
                    "y1": float(bbox[1]),
                    "x2": float(bbox[2]),
                    "y2": float(bbox[3]),
                    "confidence": 1.0,
                    "line_index": line_index,
                }
            )
            token_index += 1
            x = bbox[2] + 16
        y += 54

    # Title strip color-coded for VA cues
    draw.rectangle([0, 0, PAGE_W, 70], fill=(255, 248, 220))
    return tokens


def render_page(rhyme: dict, out_path: Path) -> tuple[list[dict], list[dict]]:
    bg, accent, ink = _palette(rhyme["rhyme_id"])
    image = Image.new("RGB", (PAGE_W, PAGE_H), bg)
    draw = ImageDraw.Draw(image)

    title_font = _font(40)
    draw.rectangle([0, 0, PAGE_W, 70], fill=(255, 248, 220))
    draw.text((40, 16), rhyme["title"], fill=ink, font=title_font)

    objects = _draw_illustration(draw, rhyme["objects"], accent)
    tokens = _layout_tokens(draw, rhyme["lines"], ink)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, format="PNG")
    return tokens, objects


def assign_split(index: int, total: int) -> str:
    # ~70/15/15 by rhyme order
    ratio = index / max(total, 1)
    if ratio < 0.70:
        return "train"
    if ratio < 0.85:
        return "val"
    return "test"


def build(db_path: Path = DEFAULT_DB, pages_dir: Path = PAGES_DIR) -> int:
    conn = init_db(db_path)
    pages_dir.mkdir(parents=True, exist_ok=True)
    meta_cache: dict[str, dict] = {}

    # Multiple visual variants per rhyme; QA-level split happens at export time.
    variants_per_rhyme = 5
    total_slots = len(PUBLIC_RHYMES) * variants_per_rhyme
    slot = 0
    for rhyme in PUBLIC_RHYMES:
        for page_index in range(variants_per_rhyme):
            variant = dict(rhyme)
            variant["rhyme_id"] = f"{rhyme['rhyme_id']}_v{page_index}"
            page_id = f"{rhyme['rhyme_id']}_{page_index}"
            rel_path = f"pages/{page_id}.png"
            abs_path = pages_dir / f"{page_id}.png"
            tokens, objects = render_page(variant, abs_path)
            # Placeholder split on pages; export_splits.py reassigns by QA.
            split = assign_split(slot, total_slots)
            insert_page(
                conn,
                page_id=page_id,
                rhyme_id=rhyme["rhyme_id"],
                page_index=page_index,
                image_path=rel_path,
                width=PAGE_W,
                height=PAGE_H,
                split=split,
                illustration_prompt=", ".join(o["label"] for o in rhyme["objects"]),
            )
            meta_cache[page_id] = {"tokens": tokens, "objects": objects}
            slot += 1

    conn.commit()
    # Stash layout GT beside images for annotate step
    import json

    cache_path = pages_dir / "_layout_gt.json"
    cache_path.write_text(json.dumps(meta_cache, indent=2), encoding="utf-8")
    n = conn.execute("SELECT COUNT(*) AS n FROM pages").fetchone()["n"]
    conn.close()
    return int(n)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--pages-dir", type=Path, default=PAGES_DIR)
    args = parser.parse_args()
    n = build(args.db, args.pages_dir)
    print(f"Built {n} pages under {args.pages_dir}")


if __name__ == "__main__":
    main()
