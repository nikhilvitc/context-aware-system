"""JSONL dataset loader for RhymeTextVQA training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch.utils.data import Dataset

ROOT = Path(__file__).resolve().parents[2]


class Vocabulary:
    def __init__(self, answers: list[str], min_freq: int = 1):
        freq: dict[str, int] = {}
        for a in answers:
            key = a.lower().strip()
            freq[key] = freq.get(key, 0) + 1
        kept = sorted([a for a, c in freq.items() if c >= min_freq])
        self.itos = kept
        self.stoi = {a: i for i, a in enumerate(self.itos)}

    def __len__(self) -> int:
        return len(self.itos)

    def encode_multihot(self, answers: list[str]) -> torch.Tensor:
        y = torch.zeros(len(self), dtype=torch.float32)
        for a in answers:
            idx = self.stoi.get(a.lower().strip())
            if idx is not None:
                y[idx] = 1.0
        return y

    def encode_class(self, answers: list[str]) -> torch.Tensor:
        """Canonical answer index for cross-entropy (majority / first known)."""
        for a in answers:
            idx = self.stoi.get(a.lower().strip())
            if idx is not None:
                return torch.tensor(idx, dtype=torch.long)
        return torch.tensor(0, dtype=torch.long)

    def decode(self, idx: int) -> str:
        if 0 <= idx < len(self.itos):
            return self.itos[idx]
        return ""


def build_vocab(jsonl_paths: list[Path]) -> Vocabulary:
    answers: list[str] = []
    for path in jsonl_paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                answers.extend(rec["answers"])
    return Vocabulary(answers)


class RhymeTextVQADataset(Dataset):
    def __init__(
        self,
        jsonl_path: Path,
        vocab: Vocabulary,
        max_ocr: int = 64,
        max_objects: int = 16,
        patch_size: int = 16,
        data_root: Path = ROOT / "data",
    ):
        self.records: list[dict[str, Any]] = []
        with jsonl_path.open(encoding="utf-8") as fh:
            for line in fh:
                self.records.append(json.loads(line))
        self.vocab = vocab
        self.max_ocr = max_ocr
        self.max_objects = max_objects
        self.patch_size = patch_size
        self.data_root = data_root
        self.word_stoi = self._build_word_vocab()

    def _build_word_vocab(self) -> dict[str, int]:
        words = {"<pad>": 0, "<unk>": 1}
        for rec in self.records:
            for w in rec["question"].lower().split():
                words.setdefault(w, len(words))
            for t in rec["ocr_tokens"]:
                words.setdefault(t["text"].lower(), len(words))
            for o in rec["objects"]:
                words.setdefault(o["label"].lower(), len(words))
        return words

    def __len__(self) -> int:
        return len(self.records)

    def _encode_words(self, tokens: list[str], max_len: int) -> torch.Tensor:
        ids = [self.word_stoi.get(t.lower(), 1) for t in tokens][:max_len]
        ids += [0] * (max_len - len(ids))
        return torch.tensor(ids, dtype=torch.long)

    def _crop_patch(self, image: Image.Image, bbox: list[float]) -> torch.Tensor:
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(image.width, max(x1 + 1, x2)), min(image.height, max(y1 + 1, y2))
        crop = image.crop((x1, y1, x2, y2)).resize((self.patch_size, self.patch_size))
        arr = torch.tensor(
            list(crop.convert("RGB").getdata()),
            dtype=torch.float32,
        ).reshape(self.patch_size, self.patch_size, 3)
        return (arr / 255.0).permute(2, 0, 1)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        rec = self.records[idx]
        image = Image.open(self.data_root / rec["image_path"]).convert("RGB")
        w, h = rec["width"], rec["height"]

        ocr = rec["ocr_tokens"][: self.max_ocr]
        n_ocr = len(ocr)
        boxes = torch.zeros(self.max_ocr, 4)
        line_index = torch.full((self.max_ocr,), -1, dtype=torch.long)
        patches = torch.zeros(self.max_ocr, 3, self.patch_size, self.patch_size)
        ocr_ids = torch.zeros(self.max_ocr, dtype=torch.long)
        for i, tok in enumerate(ocr):
            x1, y1, x2, y2 = tok["bbox"]
            boxes[i] = torch.tensor([x1 / w, y1 / h, x2 / w, y2 / h])
            line_index[i] = int(tok["line_index"]) if tok["line_index"] is not None else -1
            patches[i] = self._crop_patch(image, tok["bbox"])
            ocr_ids[i] = self.word_stoi.get(tok["text"].lower(), 1)

        objs = rec["objects"][: self.max_objects]
        obj_ids = torch.zeros(self.max_objects, dtype=torch.long)
        for i, obj in enumerate(objs):
            obj_ids[i] = self.word_stoi.get(obj["label"].lower(), 1)

        q_tokens = rec["question"].lower().split()
        return {
            "question_ids": self._encode_words(q_tokens, 32),
            "ocr_ids": ocr_ids,
            "ocr_boxes": boxes,
            "ocr_patches": patches,
            "line_index": line_index,
            "n_ocr": torch.tensor(n_ocr, dtype=torch.long),
            "obj_ids": obj_ids,
            "n_obj": torch.tensor(len(objs), dtype=torch.long),
            "target": self.vocab.encode_class(rec["answers"]),
            "target_multihot": self.vocab.encode_multihot(rec["answers"]),
            "answers": rec["answers"],
            "question_id": rec["question_id"],
        }


def collate_batch(batch: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    tensor_keys = [
        "question_ids",
        "ocr_ids",
        "ocr_boxes",
        "ocr_patches",
        "line_index",
        "n_ocr",
        "obj_ids",
        "n_obj",
        "target",
        "target_multihot",
    ]
    for key in tensor_keys:
        out[key] = torch.stack([b[key] for b in batch], dim=0)
    out["answers"] = [b["answers"] for b in batch]
    out["question_id"] = [b["question_id"] for b in batch]
    return out
