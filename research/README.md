# Children’s Rhyme SLA Research

Domain-adapted SLA-style **TSS / SCP / VA** training on a public-domain children’s rhyme TextVQA dataset (**RhymeTextVQA**).

## Novelty framing

Compare module ablations **on RhymeTextVQA**, not by claiming TextVQA/ST-VQA SOTA unless you later evaluate there.

## Quick start

```bash
# from repo root
python research/build_dataset.py
python research/sla/train.py --epochs 8 --ablations none tss scp va tss_scp full
python research/sla/eval.py --checkpoint research/checkpoints/full_best.pt --split test
```

Artifacts:
- SQLite: `data/rhyme_textvqa.db`
- Pages: `data/pages/`
- Splits: `data/exports/{train,val,test}.jsonl`
- Checkpoints / ablation tables: `research/checkpoints/`

## Modules

| Flag | Module |
|------|--------|
| TSS | Text Semantic Separate (`<context>` tokens + same-line prior) |
| SCP | Spatial Circle Position (2D distance attention bias) |
| VA | Visual Align (RGB histogram KL + gating) |
