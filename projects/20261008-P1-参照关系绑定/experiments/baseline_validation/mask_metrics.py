"""Offline foreground scoring; this module cannot call a model or read labels."""

import math

import numpy as np


GIOU_EPSILON = 1e-5
CIOU_EPSILON = 1e-10


def score_masks(logits, targets):
    """Score exactly paired [N,H,W] masks at original resolution; never match by GT."""
    logits, targets = np.asarray(logits), np.asarray(targets)
    if logits.ndim != 3 or logits.shape != targets.shape or any(n == 0 for n in logits.shape):
        raise ValueError("Expected nonempty paired [N,H,W] masks with identical shapes")
    if not np.issubdtype(logits.dtype, np.number) or np.iscomplexobj(logits):
        raise ValueError("Logits must be real numeric arrays")
    if not np.isfinite(logits).all():
        raise ValueError("Nonfinite logits")
    if not np.isin(targets, [0, 1, 255]).all():
        raise ValueError("Targets must contain only 0, 1 or ignore label 255")
    prediction = logits > 0
    rows = []
    for pred, target in zip(prediction, targets):
        valid = target != 255
        if not valid.any():
            raise ValueError("A mask has no nonignored pixels")
        foreground = target == 1
        intersection = int(np.count_nonzero(pred & foreground & valid))
        union = int(np.count_nonzero((pred | foreground) & valid))
        rows.append({"intersection": intersection, "union": union,
                     "iou": intersection / (union + GIOU_EPSILON) if union else 1.0})
    return rows


def _summary(samples):
    masks = [mask for sample in samples for mask in sample["masks"]]
    intersection = sum(m["intersection"] for m in masks)
    union = sum(m["union"] for m in masks)
    return {"sample_count": len(samples), "mask_count": len(masks),
            "intersection": intersection, "union": union,
            "giou": math.fsum(m["iou"] for m in masks) / len(masks),
            "ciou": intersection / (union + CIOU_EPSILON)}


class MaskMetrics:
    """Require complete, unique manifest coverage; do not silently skip generation failures."""

    def __init__(self, expected_ids):
        ids = list(expected_ids)
        if not ids or any(not isinstance(i, str) or not i for i in ids):
            raise ValueError("Expected a nonempty manifest of string IDs")
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate manifest IDs")
        self._ids = ids
        self._expected = set(ids)
        self._samples = {}

    def add(self, sample_id, reasoning_type, logits, targets):
        if sample_id not in self._expected or sample_id in self._samples:
            raise ValueError("Unexpected or duplicate sample ID")
        if reasoning_type not in ("spatial", "attribute", "scene"):
            raise ValueError("Unknown DRSeg reasoning type")
        masks = score_masks(logits, targets)
        self._samples[sample_id] = {"id": sample_id, "reasoning_type": reasoning_type,
                                    "masks": masks}

    def finish(self):
        missing = self._expected - self._samples.keys()
        if missing:
            raise ValueError(f"Incomplete manifest coverage: {len(missing)} missing samples")
        samples = [self._samples[i] for i in self._ids]
        result = _summary(samples)
        result["by_reasoning_type"] = {
            kind: _summary([s for s in samples if s["reasoning_type"] == kind])
            for kind in ("spatial", "attribute", "scene")
            if any(s["reasoning_type"] == kind for s in samples)
        }
        result["metric_config"] = {"foreground_threshold": 0, "ignore_label": 255,
                                   "giou_epsilon": GIOU_EPSILON,
                                   "ciou_epsilon": CIOU_EPSILON,
                                   "empty_union_giou": 1.0,
                                   "empty_total_union_ciou": 0.0}
        return result
