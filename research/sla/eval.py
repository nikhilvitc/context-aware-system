#!/usr/bin/env python3
"""Evaluate a RhymeSLA checkpoint on val/test JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.sla.data import RhymeTextVQADataset, Vocabulary, collate_batch
from research.sla.metrics import aggregate, anls, vqa_accuracy
from research.sla.model import RhymeSLAModel

EXPORT_DIR = ROOT / "data" / "exports"
CKPT_DIR = ROOT / "research" / "checkpoints"


@torch.no_grad()
def evaluate(model, loader, vocab: Vocabulary, device: torch.device) -> dict:
    model.eval()
    accs = []
    anls_scores = []
    for batch in loader:
        batch_t = {
            k: v.to(device) if torch.is_tensor(v) else v for k, v in batch.items()
        }
        logits = model(batch_t)
        pred_ids = logits.argmax(dim=-1).tolist()
        for i, pred_id in enumerate(pred_ids):
            pred = vocab.decode(pred_id)
            answers = batch["answers"][i]
            accs.append(vqa_accuracy(pred, answers))
            anls_scores.append(anls(pred, answers))
    return {
        "vqa_acc": aggregate(accs),
        "anls": aggregate(anls_scores),
        "n": len(accs),
    }


def load_checkpoint(path: Path, device: torch.device):
    ckpt = torch.load(path, map_location=device, weights_only=False)
    vocab = Vocabulary([])
    vocab.itos = ckpt["vocab_itos"]
    vocab.stoi = {a: i for i, a in enumerate(vocab.itos)}
    word_stoi = ckpt["word_stoi"]
    model = RhymeSLAModel(
        vocab_size_words=len(word_stoi),
        num_answers=len(vocab),
        d_model=ckpt.get("d_model", 256),
        n_heads=ckpt.get("n_heads", 4),
        n_layers=ckpt.get("n_layers", 2),
        **ckpt["flags"],
    ).to(device)
    model.load_state_dict(ckpt["model"])
    return model, vocab, word_stoi, ckpt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    device = torch.device(args.device)
    model, vocab, word_stoi, ckpt = load_checkpoint(args.checkpoint, device)
    ds = RhymeTextVQADataset(EXPORT_DIR / f"{args.split}.jsonl", vocab)
    ds.word_stoi = word_stoi
    loader = DataLoader(ds, batch_size=args.batch_size, collate_fn=collate_batch)
    metrics = evaluate(model, loader, vocab, device)
    metrics["ablation"] = ckpt.get("ablation")
    metrics["split"] = args.split
    print(json.dumps(metrics, indent=2))
    out = CKPT_DIR / f"{args.checkpoint.stem}_{args.split}_metrics.json"
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
