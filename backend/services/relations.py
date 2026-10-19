"""Inference-time TSS / SCP / VA relation scoring for rhyme kids mode."""

from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np


def _center(bbox) -> tuple[float, float]:
    # bbox as [[x,y], ...] or [x1,y1,x2,y2]
    if bbox and isinstance(bbox[0], (list, tuple)):
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def _rect(bbox) -> tuple[float, float, float, float]:
    if bbox and isinstance(bbox[0], (list, tuple)):
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return min(xs), min(ys), max(xs), max(ys)
    return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])


def scp_score(a_bbox, b_bbox, image_diag: float) -> float:
    ax, ay = _center(a_bbox)
    bx, by = _center(b_bbox)
    dist = math.hypot(ax - bx, ay - by)
    return float(max(0.0, 1.0 - dist / max(image_diag, 1.0)))


def tss_score(a: dict, b: dict) -> float:
    """Semantic adjacency prior: same line / shared lexical neighborhood."""
    la = a.get("line_index")
    lb = b.get("line_index")
    if la is not None and lb is not None and la == lb:
        return 0.9
    ta = set(a.get("text", "").lower().split())
    tb = set(b.get("text", "").lower().split())
    if not ta or not tb:
        return 0.2
    overlap = len(ta & tb) / len(ta | tb)
    return 0.35 + 0.5 * overlap


def va_score(image: Optional[np.ndarray], a_bbox, b_bbox) -> float:
    """Color-histogram affinity; falls back to neutral if image missing."""
    if image is None:
        return 0.5
    try:
        import cv2
    except ImportError:
        return 0.5

    def hist(bbox):
        x1, y1, x2, y2 = [int(v) for v in _rect(bbox)]
        x1, y1 = max(0, x1), max(0, y1)
        x2 = min(image.shape[1], max(x1 + 1, x2))
        y2 = min(image.shape[0], max(y1 + 1, y2))
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        h = cv2.calcHist([crop], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        h = cv2.normalize(h, h).flatten()
        return h

    ha, hb = hist(a_bbox), hist(b_bbox)
    if ha is None or hb is None:
        return 0.5
    # Correlation in [0,1] after shift
    corr = float(cv2.compareHist(ha, hb, cv2.HISTCMP_CORREL))
    return max(0.0, min(1.0, (corr + 1.0) / 2.0))


def point_in_bbox(x: float, y: float, bbox) -> bool:
    x1, y1, x2, y2 = _rect(bbox)
    return x1 <= x <= x2 and y1 <= y <= y2


def find_tap_target(
    ocr_results: list[dict],
    objects: list[dict],
    x: float,
    y: float,
) -> tuple[Optional[dict], str]:
    """Return (item, selected_type) where type is text|object."""
    for obj in objects:
        bbox = obj.get("bbox") or [obj["x1"], obj["y1"], obj["x2"], obj["y2"]]
        if point_in_bbox(x, y, bbox):
            item = {
                "text": obj.get("label") or obj.get("text"),
                "bbox": bbox
                if isinstance(bbox[0], (list, tuple))
                else [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                ],
                "label": obj.get("label"),
                "attributes": obj.get("attributes", {}),
                "relation_hint": obj.get("relation_hint"),
                "line_index": None,
            }
            return item, "object"

    for item in ocr_results:
        if point_in_bbox(x, y, item["bbox"]):
            return item, "text"

    # Nearest OCR or object
    tap = (x, y)
    best = None
    best_d = float("inf")
    best_type = "text"
    for item in ocr_results:
        cx, cy = _center(item["bbox"])
        d = math.hypot(cx - tap[0], cy - tap[1])
        if d < best_d:
            best_d = d
            best = item
            best_type = "text"
    for obj in objects:
        bbox = obj.get("bbox") or [obj["x1"], obj["y1"], obj["x2"], obj["y2"]]
        cx, cy = _center(bbox)
        d = math.hypot(cx - tap[0], cy - tap[1])
        if d < best_d:
            best_d = d
            poly = (
                bbox
                if isinstance(bbox[0], (list, tuple))
                else [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                ]
            )
            best = {
                "text": obj.get("label"),
                "bbox": poly,
                "label": obj.get("label"),
                "attributes": obj.get("attributes", {}),
                "relation_hint": obj.get("relation_hint"),
                "line_index": None,
            }
            best_type = "object"
    return best, best_type


def score_relations(
    selected: dict,
    neighbors: list[dict],
    image: Optional[np.ndarray],
    width: int,
    height: int,
    top_k: int = 6,
) -> list[dict[str, Any]]:
    diag = math.hypot(width, height)
    scored = []
    for item in neighbors:
        if item is selected:
            continue
        if item.get("bbox") == selected.get("bbox") and item.get("text") == selected.get("text"):
            continue
        scp = scp_score(selected["bbox"], item["bbox"], diag)
        tss = tss_score(selected, item)
        va = va_score(image, selected["bbox"], item["bbox"])
        combined = 0.4 * scp + 0.35 * tss + 0.25 * va
        scored.append(
            {
                "text": item.get("text"),
                "bbox": item.get("bbox"),
                "confidence": item.get("confidence", 1.0),
                "relations": [
                    {"code": "SCP", "score": round(scp, 4)},
                    {"code": "TSS", "score": round(tss, 4)},
                    {"code": "VA", "score": round(va, 4)},
                ],
                "score": combined,
            }
        )
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
