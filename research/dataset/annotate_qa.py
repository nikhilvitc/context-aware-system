#!/usr/bin/env python3
"""Generate TextVQA-style QA pairs for rhyme pages (dense, short-answer templates)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.dataset.db import DEFAULT_DB, fetch_pages, init_db, replace_qa_pairs
from research.dataset.public_rhymes import PUBLIC_RHYMES

RHYME_BY_ID = {r["rhyme_id"]: r for r in PUBLIC_RHYMES}


def _pad_answers(answer: str, n: int = 10) -> list[str]:
    return [answer] * n


def _pair(qa_id: str, question: str, answer: str, answer_type: str) -> dict:
    return {
        "qa_id": qa_id,
        "question": question,
        "answers": _pad_answers(answer),
        "answer_type": answer_type,
        "reviewed": 0,
    }


def template_qa_for_page(page_id: str, rhyme_id: str) -> list[dict]:
    rhyme = RHYME_BY_ID[rhyme_id]
    title = rhyme["title"]
    lines = rhyme["lines"]
    objects = rhyme["objects"]
    pairs: list[dict] = []
    first_word = lines[0].replace(",", "").split()[0].strip(",.;:!?")

    # High-frequency short answers (many paraphrases → easier 70%+ learning)
    title_questions = [
        "What is the title of this rhyme?",
        "Which nursery rhyme is this page from?",
        "What rhyme are we reading?",
        "Name this nursery rhyme.",
        "What is the name of the poem on this page?",
    ]
    for i, q in enumerate(title_questions):
        pairs.append(_pair(f"qa_{page_id}_title{i}", q, title, "text"))

    first_word_questions = [
        "Which word begins the rhyme?",
        "What is the first word of the rhyme?",
        "What word starts the first line?",
    ]
    for i, q in enumerate(first_word_questions):
        pairs.append(_pair(f"qa_{page_id}_fw{i}", q, first_word, "text"))

    if len(lines) > 1:
        second = lines[1].rstrip(".,;")
        # Prefer a short keyword from line 2 when possible
        short = second.split()[0].strip(",.;:!?") if second.split() else second
        pairs.append(
            _pair(
                f"qa_{page_id}_line2_short",
                "What is the first word of the second line?",
                short,
                "text",
            )
        )

    for oi, obj in enumerate(objects):
        label = obj["label"]
        category = obj.get("category", "object")
        cat_answer = "person" if category == "character" else category
        pairs.extend(
            [
                _pair(
                    f"qa_{page_id}_obj{oi}_a",
                    f"What is drawn as object {oi + 1} in the picture?",
                    label,
                    "object",
                ),
                _pair(
                    f"qa_{page_id}_obj{oi}_b",
                    f"Which picture label is '{label}'?",
                    label,
                    "object",
                ),
                _pair(
                    f"qa_{page_id}_obj{oi}_c",
                    f"Is the {label} an animal, a place, a person, or an object?",
                    cat_answer,
                    "object",
                ),
            ]
        )
        if obj.get("relation_hint"):
            hint = obj["relation_hint"]
            pairs.extend(
                [
                    _pair(
                        f"qa_{page_id}_rel{oi}_a",
                        f"Where is the {label} in the rhyme picture?",
                        hint,
                        "relation",
                    ),
                    _pair(
                        f"qa_{page_id}_rel{oi}_b",
                        f"How is the {label} related in the picture?",
                        hint,
                        "relation",
                    ),
                ]
            )

    # Explicit object inventory questions
    if objects:
        pairs.append(
            _pair(
                f"qa_{page_id}_first_obj",
                "What animal or thing is shown first in the picture?",
                objects[0]["label"],
                "object",
            )
        )

    return pairs


def maybe_llm_enrich(pairs: list[dict], rhyme: dict) -> list[dict]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return pairs
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = (
            "Create one simple question a child could answer from this rhyme. "
            "Return JSON with keys question and answer only. Answer must be 1-3 words.\n\n"
            f"Title: {rhyme['title']}\n"
            f"Text:\n" + "\n".join(rhyme["lines"])
        )
        interaction = client.interactions.create(model="gemini-3.6-flash", input=prompt)
        text = interaction.output_text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(text[start : end + 1])
            pairs.append(
                _pair(
                    f"qa_{rhyme['rhyme_id']}_llm0",
                    data["question"],
                    str(data["answer"]),
                    "text",
                )
            )
    except Exception:
        return pairs
    return pairs


def annotate(db_path: Path = DEFAULT_DB, use_llm: bool = False) -> int:
    conn = init_db(db_path)
    total = 0
    for page in fetch_pages(conn):
        rhyme = RHYME_BY_ID[page["rhyme_id"]]
        pairs = template_qa_for_page(page["page_id"], page["rhyme_id"])
        if use_llm:
            pairs = maybe_llm_enrich(pairs, rhyme)
        replace_qa_pairs(conn, page["page_id"], pairs)
        total += len(pairs)
    conn.commit()
    conn.close()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--use-llm", action="store_true")
    args = parser.parse_args()
    n = annotate(args.db, use_llm=args.use_llm)
    print(f"Generated {n} QA pairs")


if __name__ == "__main__":
    main()
