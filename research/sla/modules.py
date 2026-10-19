"""PyTorch implementations of SLA TSS, SCP, and VA (rhyme-specialized)."""

from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class TSSModule(nn.Module):
    """Text Semantic Separate: learnable <context> separators between OCR tokens.

    Rhyme specialization: tokens on the same verse line get a soft adjacency
    prior so couplets stay linked while page chrome stays separated.
    """

    def __init__(self, d_model: int = 256, context_init_std: float = 0.02):
        super().__init__()
        self.context_embed = nn.Parameter(torch.randn(d_model) * context_init_std)
        self.line_bias = nn.Parameter(torch.tensor(0.5))

    def forward(
        self,
        ocr_feats: torch.Tensor,
        line_index: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            ocr_feats: [B, N, D]
            line_index: [B, N] optional verse line ids (-1 unknown)
        Returns:
            Sequence with context vectors interleaved: [B, 2N, D]
        """
        b, n, d = ocr_feats.shape
        ctx = self.context_embed.view(1, 1, d).expand(b, n, d)
        if line_index is not None:
            # Same-line neighbors get a small additive boost on the context token.
            same = torch.zeros(b, n, device=ocr_feats.device)
            same[:, 1:] = (line_index[:, 1:] == line_index[:, :-1]).float()
            ctx = ctx + same.unsqueeze(-1) * self.line_bias * ocr_feats
        # Interleave token, context, token, context, ...
        stacked = torch.stack([ocr_feats, ctx], dim=2)  # [B, N, 2, D]
        return stacked.reshape(b, n * 2, d)


class SCPModule(nn.Module):
    """Spatial Circle Position: relative 2D distance bias for OCR attention."""

    def __init__(self, num_bins: int = 32, n_heads: int = 4):
        super().__init__()
        self.num_bins = num_bins
        self.n_heads = n_heads
        self.distance_embed = nn.Embedding(num_bins, n_heads)
        nn.init.zeros_(self.distance_embed.weight)

    @staticmethod
    def _centers(boxes: torch.Tensor) -> torch.Tensor:
        # boxes: [B, N, 4] as x1,y1,x2,y2 normalized
        cx = (boxes[..., 0] + boxes[..., 2]) * 0.5
        cy = (boxes[..., 1] + boxes[..., 3]) * 0.5
        return torch.stack([cx, cy], dim=-1)

    def relative_bins(self, boxes: torch.Tensor) -> torch.Tensor:
        centers = self._centers(boxes)
        # pairwise euclidean, scaled into bins
        dist = torch.cdist(centers, centers, p=2)  # [B, N, N]
        # Circle-style packing: multiply by 2 then quantize (paper Algorithm)
        scaled = (dist * 2 * (self.num_bins - 1)).clamp(0, self.num_bins - 1).long()
        return scaled

    def attention_bias(self, boxes: torch.Tensor) -> torch.Tensor:
        """Return bias [B, H, N, N] to add inside attention logits."""
        bins = self.relative_bins(boxes)
        emb = self.distance_embed(bins)  # [B, N, N, H]
        return emb.permute(0, 3, 1, 2)

    def forward(self, boxes: torch.Tensor) -> torch.Tensor:
        return self.attention_bias(boxes)


class VAModule(nn.Module):
    """Visual Align: RGB histogram KL similarity with gating (SLA §III-D)."""

    def __init__(self, n_heads: int = 4, hist_bins: int = 16):
        super().__init__()
        self.hist_bins = hist_bins
        self.n_heads = n_heads
        self.sim_embed = nn.Linear(1, n_heads)

    def color_histograms(self, patches: torch.Tensor) -> torch.Tensor:
        """
        Args:
            patches: [B, N, 3, H, W] in 0..1
        Returns:
            hist: [B, N, 3, bins]
        """
        b, n, c, h, w = patches.shape
        flat = patches.reshape(b, n, c, h * w)
        # Soft histogram via binning
        bin_ids = (flat * (self.hist_bins - 1)).clamp(0, self.hist_bins - 1).long()
        hist = torch.zeros(b, n, c, self.hist_bins, device=patches.device)
        hist.scatter_add_(3, bin_ids, torch.ones_like(flat))
        hist = hist / hist.sum(dim=-1, keepdim=True).clamp_min(1e-6)
        return hist

    @staticmethod
    def kl_pairwise(hist: torch.Tensor) -> torch.Tensor:
        # hist [B, N, 3, bins] -> KL per channel [B, N, N, 3]
        b, n, c, bins = hist.shape
        p = hist.unsqueeze(2).clamp_min(1e-6)  # [B,N,1,C,bins]
        q = hist.unsqueeze(1).clamp_min(1e-6)  # [B,1,N,C,bins]
        kl = (p * (p.log() - q.log())).sum(dim=-1)  # [B,N,N,C]
        return kl

    def attention_bias(self, patches: torch.Tensor) -> torch.Tensor:
        hist = self.color_histograms(patches)
        kl = self.kl_pairwise(hist)  # [B,N,N,3]
        r, g, b = kl[..., 0], kl[..., 1], kl[..., 2]
        # Lower KL => higher similarity; convert to affinity
        sim_r = torch.exp(-r)
        sim_g = torch.exp(-g)
        sim_b = torch.exp(-b)
        alpha = torch.sigmoid(sim_r * sim_g)
        beta = torch.sigmoid(sim_b * sim_g)
        fused = (alpha * sim_r + beta * sim_b) / 2 + (2 - alpha - beta) / 2 * sim_g
        # [B,N,N] -> [B,H,N,N]
        bias = self.sim_embed(fused.unsqueeze(-1)).permute(0, 3, 1, 2)
        return bias

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        return self.attention_bias(patches)


class RelationAwareAttention(nn.Module):
    """Multi-head attention with optional SCP/VA additive biases."""

    def __init__(self, d_model: int = 256, n_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.qkv = nn.Linear(d_model, d_model * 3)
        self.out = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        bias: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        b, n, d = x.shape
        qkv = self.qkv(x).reshape(b, n, 3, self.n_heads, self.d_head)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_head)
        if bias is not None:
            # bias may be over OCR length; crop/pad to n if needed
            h = min(bias.shape[-1], n)
            att[:, :, :h, :h] = att[:, :, :h, :h] + bias[:, :, :h, :h]
        att = self.dropout(F.softmax(att, dim=-1))
        y = (att @ v).transpose(1, 2).reshape(b, n, d)
        return self.out(y)
