"""VQA accuracy (soft) and ANLS metrics."""

from __future__ import annotations

import re
from typing import Iterable, Sequence


def normalize_answer(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def vqa_accuracy(prediction: str, answers: Sequence[str]) -> float:
    """Soft VQA accuracy: min(#matches/3, 1)."""
    pred = normalize_answer(prediction)
    matches = sum(1 for a in answers if normalize_answer(a) == pred)
    return min(matches / 3.0, 1.0)


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def anls(prediction: str, answers: Sequence[str], threshold: float = 0.5) -> float:
    pred = normalize_answer(prediction)
    best = 0.0
    for ans in answers:
        gt = normalize_answer(ans)
        if not pred and not gt:
            score = 1.0
        elif not pred or not gt:
            score = 0.0
        else:
            dist = levenshtein(pred, gt)
            score = 1.0 - dist / max(len(pred), len(gt))
            if score < threshold:
                score = 0.0
        best = max(best, score)
    return best


def aggregate(scores: Iterable[float]) -> float:
    values = list(scores)
    return sum(values) / len(values) if values else 0.0
