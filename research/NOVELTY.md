# Novelty statement — Children’s Rhyme SLA

## Claim (precise)

We adapt Separate–Locate–Align (**TSS**, **SCP**, **VA**) scene-text relation modeling to **children’s nursery-rhyme picture books**, releasing **RhymeTextVQA** (public-domain rhymes + synthesized pages + OCR/object/QA annotations) and showing that relation-aware modules improve rhyme-domain VQA over an identical backbone without those modules.

## What is *not* claimed

We do **not** claim higher accuracy than Fang et al. SLA on TextVQA / ST-VQA unless those public benchmarks are re-evaluated with the same OCR and training protocol.

## Why rhymes are a good domain

- Verse lines create natural **semantic adjacency** (TSS).
- Picture-book layout is strongly **2-D** (SCP).
- Titles, body text, and captions often differ in **color/style** (VA).
- Children need explanations for **both words and illustrations** (monkey on a tree).

## Deliverables

1. Dataset pipeline (`research/build_dataset.py`)
2. Trainable TSS/SCP/VA ablations (`research/sla/train.py`)
3. Kids mode API + UI (tap text or object → rhyme-aware explanation)
