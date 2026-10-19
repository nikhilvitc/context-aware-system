"""Text-first multimodal backbone with optional TSS/SCP/VA biases."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .modules import RelationAwareAttention, SCPModule, TSSModule, VAModule


class RhymeSLAModel(nn.Module):
    def __init__(
        self,
        vocab_size_words: int,
        num_answers: int,
        d_model: int = 256,
        n_heads: int = 4,
        n_layers: int = 2,
        use_tss: bool = True,
        use_scp: bool = True,
        use_va: bool = True,
    ):
        super().__init__()
        self.use_tss = use_tss
        self.use_scp = use_scp
        self.use_va = use_va
        self.d_model = d_model

        self.token_embed = nn.Embedding(vocab_size_words, d_model, padding_idx=0)
        self.box_proj = nn.Linear(4, d_model)
        self.patch_proj = nn.Sequential(
            nn.Flatten(),
            nn.Linear(3 * 16 * 16, d_model),
        )
        self.tss = TSSModule(d_model) if use_tss else None
        self.scp = SCPModule(n_heads=n_heads) if use_scp else None
        self.va = VAModule(n_heads=n_heads) if use_va else None
        self.ocr_attn = RelationAwareAttention(d_model, n_heads, dropout=0.0)
        self.q_proj = nn.Linear(d_model, d_model)
        self.ctx_proj = nn.Linear(d_model, d_model)
        self.layers = nn.ModuleList(
            [nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=n_heads,
                dim_feedforward=d_model * 2,
                batch_first=True,
                activation="gelu",
                dropout=0.1,
            ) for _ in range(n_layers)]
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(d_model * 4),
            nn.Linear(d_model * 4, d_model * 2),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(d_model * 2, num_answers),
        )

    def _masked_mean(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        mask = mask.unsqueeze(-1).float()
        return (x * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)

    def encode_ocr(
        self,
        ocr_ids: torch.Tensor,
        boxes: torch.Tensor,
        patches: torch.Tensor,
        n_ocr: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        text = self.token_embed(ocr_ids)
        geom = self.box_proj(boxes)
        b, n, _, _, _ = patches.shape
        vis = self.patch_proj(patches.reshape(b * n, 3, 16, 16)).reshape(b, n, -1)
        # Text dominates; geometry/visual are light additives (SLA cues).
        feats = text + 0.25 * geom + 0.15 * vis
        mask = torch.arange(n, device=feats.device).unsqueeze(0) < n_ocr.unsqueeze(1)
        feats = feats * mask.unsqueeze(-1).float()
        return feats, mask

    def _relation_bias(self, batch: dict) -> torch.Tensor | None:
        bias = None
        if self.use_scp and self.scp is not None:
            bias = self.scp(batch["ocr_boxes"])
        if self.use_va and self.va is not None:
            va_bias = self.va(batch["ocr_patches"])
            bias = va_bias if bias is None else bias + va_bias
        return bias

    def forward(self, batch: dict) -> torch.Tensor:
        q_ids = batch["question_ids"]
        q_mask = q_ids != 0
        q = self.token_embed(q_ids)
        q_vec = self._masked_mean(q, q_mask)

        ocr, ocr_mask = self.encode_ocr(
            batch["ocr_ids"],
            batch["ocr_boxes"],
            batch["ocr_patches"],
            batch["n_ocr"],
        )
        bias = self._relation_bias(batch)
        if bias is not None:
            ocr = ocr + self.ocr_attn(ocr, bias=bias)

        if self.use_tss and self.tss is not None:
            ocr = self.tss(ocr, batch["line_index"])
            # Expand mask for interleaved context tokens: token, ctx, token, ctx...
            ocr_mask = ocr_mask.repeat_interleave(2, dim=1)

        objs = self.token_embed(batch["obj_ids"])
        obj_mask = torch.arange(objs.shape[1], device=objs.device).unsqueeze(0) < batch[
            "n_obj"
        ].unsqueeze(1)

        # Cross-attend question to OCR / objects
        q_as_q = self.q_proj(q_vec).unsqueeze(1)  # [B,1,D]
        ocr_k = self.ctx_proj(ocr)
        obj_k = self.ctx_proj(objs)
        ocr_att = torch.matmul(q_as_q, ocr_k.transpose(1, 2)).squeeze(1) / (self.d_model ** 0.5)
        ocr_att = ocr_att.masked_fill(~ocr_mask, -1e9)
        ocr_ctx = torch.matmul(F.softmax(ocr_att, dim=-1).unsqueeze(1), ocr).squeeze(1)

        obj_att = torch.matmul(q_as_q, obj_k.transpose(1, 2)).squeeze(1) / (self.d_model ** 0.5)
        obj_att = obj_att.masked_fill(~obj_mask, -1e9)
        obj_ctx = torch.matmul(F.softmax(obj_att, dim=-1).unsqueeze(1), objs).squeeze(1)

        seq = torch.cat([q, ocr, objs], dim=1)
        for layer in self.layers:
            seq = layer(seq)
        seq_vec = seq.mean(dim=1)

        fused = torch.cat([q_vec, ocr_ctx, obj_ctx, seq_vec], dim=-1)
        return self.classifier(fused)
