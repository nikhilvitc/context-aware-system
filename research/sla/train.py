#!/usr/bin/env python3
"""Train RhymeSLA with module ablations on RhymeTextVQA."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.sla.data import RhymeTextVQADataset, build_vocab, collate_batch
from research.sla.eval import evaluate
from research.sla.model import RhymeSLAModel

EXPORT_DIR = ROOT / "data" / "exports"
CKPT_DIR = ROOT / "research" / "checkpoints"


def parse_flags(name: str) -> dict[str, bool]:
    mapping = {
        "none": dict(use_tss=False, use_scp=False, use_va=False),
        "tss": dict(use_tss=True, use_scp=False, use_va=False),
        "scp": dict(use_tss=False, use_scp=True, use_va=False),
        "va": dict(use_tss=False, use_scp=False, use_va=True),
        "tss_scp": dict(use_tss=True, use_scp=True, use_va=False),
        "full": dict(use_tss=True, use_scp=True, use_va=True),
    }
    if name not in mapping:
        raise ValueError(f"Unknown ablation {name}. Choose from {list(mapping)}")
    return mapping[name]


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _union_word_stoi(*datasets: RhymeTextVQADataset) -> dict[str, int]:
    words = {"<pad>": 0, "<unk>": 1}
    for ds in datasets:
        for w, idx in ds.word_stoi.items():
            if w not in words:
                words[w] = len(words)
    return words


def train_one(
    ablation: str,
    epochs: int,
    batch_size: int,
    lr: float,
    device: torch.device,
    seed: int = 42,
    target_acc: float = 0.70,
) -> dict:
    _set_seed(seed)
    flags = parse_flags(ablation)
    train_path = EXPORT_DIR / "train.jsonl"
    val_path = EXPORT_DIR / "val.jsonl"
    test_path = EXPORT_DIR / "test.jsonl"
    vocab = build_vocab([train_path, val_path, test_path])

    train_ds = RhymeTextVQADataset(train_path, vocab)
    val_ds = RhymeTextVQADataset(val_path, vocab)
    test_ds = RhymeTextVQADataset(test_path, vocab) if test_path.exists() else None
    word_stoi = _union_word_stoi(train_ds, val_ds, *( [test_ds] if test_ds else [] ))
    train_ds.word_stoi = word_stoi
    val_ds.word_stoi = word_stoi
    if test_ds is not None:
        test_ds.word_stoi = word_stoi

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_batch,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_batch,
    )

    model = RhymeSLAModel(
        vocab_size_words=len(word_stoi),
        num_answers=len(vocab),
        d_model=256,
        n_heads=4,
        n_layers=2,
        **flags,
    ).to(device)

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(epochs, 1))
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

    history = []
    best_acc = -1.0
    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    best_path = CKPT_DIR / f"{ablation}_best.pt"

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        steps = 0
        for batch in train_loader:
            batch_t = {
                k: v.to(device) if torch.is_tensor(v) else v for k, v in batch.items()
            }
            logits = model(batch_t)
            loss = criterion(logits, batch_t["target"])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total_loss += float(loss.item())
            steps += 1
        scheduler.step()

        metrics = evaluate(model, val_loader, vocab, device)
        row = {
            "epoch": epoch,
            "loss": total_loss / max(steps, 1),
            **metrics,
        }
        history.append(row)
        print(
            f"[{ablation}] epoch {epoch} loss={row['loss']:.4f} "
            f"acc={row['vqa_acc']:.3f} anls={row['anls']:.3f}"
        )
        if metrics["vqa_acc"] >= best_acc:
            best_acc = metrics["vqa_acc"]
            torch.save(
                {
                    "model": model.state_dict(),
                    "vocab_itos": vocab.itos,
                    "word_stoi": word_stoi,
                    "flags": flags,
                    "ablation": ablation,
                    "d_model": 256,
                    "n_heads": 4,
                    "n_layers": 2,
                },
                best_path,
            )
        if best_acc >= target_acc:
            print(f"[{ablation}] reached target val acc {best_acc:.3f} >= {target_acc:.2f}")
            break

    report = {
        "ablation": ablation,
        "flags": flags,
        "best_val_vqa_acc": best_acc,
        "history": history,
        "checkpoint": str(best_path),
    }
    report_path = CKPT_DIR / f"{ablation}_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ablations",
        nargs="+",
        default=["none", "tss", "scp", "va", "tss_scp", "full"],
    )
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-acc", type=float, default=0.70)
    args = parser.parse_args()

    device = torch.device(args.device)
    summary = []
    for name in args.ablations:
        summary.append(
            train_one(
                name,
                args.epochs,
                args.batch_size,
                args.lr,
                device,
                seed=args.seed,
                target_acc=args.target_acc,
            )
        )

    table = [
        {
            "ablation": r["ablation"],
            "best_val_vqa_acc": r["best_val_vqa_acc"],
            "final_anls": r["history"][-1]["anls"] if r["history"] else 0.0,
        }
        for r in summary
    ]
    out = CKPT_DIR / "ablation_summary.json"
    out.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print("Ablation summary:")
    print(json.dumps(table, indent=2))


if __name__ == "__main__":
    main()
