"""Independent single-target COCO polygon decoding for offline supervision/scoring."""

import numpy as np


def validate_target_polygon(row, rgb_shape):
    if len(rgb_shape) != 2 or any(type(n) is not int or n <= 0 for n in rgb_shape):
        raise ValueError("Expected positive original RGB height/width")
    if (row.get("height"), row.get("width")) != tuple(rgb_shape):
        raise ValueError("Declared GT geometry differs from original RGB")
    annotations = row.get("ann_list")
    if not isinstance(annotations, list) or len(annotations) != 1:
        raise ValueError("Expected exactly one target annotation")
    polygon = annotations[0].get("segmentation")
    if not isinstance(polygon, list) or not polygon:
        raise ValueError("Expected a nonempty COCO polygon")
    if isinstance(polygon[0], list):
        if len(polygon) != 1:
            raise ValueError("Multiple polygons require an explicit protocol; do not discard parts")
        polygon = polygon[0]
    if len(polygon) < 6 or len(polygon) % 2:
        raise ValueError("Expected at least three coordinate pairs")
    if any(isinstance(v, (bool, str)) or not isinstance(v, (int, float)) for v in polygon):
        raise ValueError("Polygon coordinates must be real numbers")
    points = np.asarray(polygon, dtype=np.float64).reshape(-1, 2)
    if not np.isfinite(points).all() or len(np.unique(points, axis=0)) < 3:
        raise ValueError("Nonfinite or degenerate polygon")
    return list(polygon)


def decode_target_mask(row, rgb_shape, *, polygon_policy="reject_multipart"):
    if polygon_policy not in ("reject_multipart", "union", "first_polygon"):
        raise ValueError("Unknown polygon policy")
    if polygon_policy == "reject_multipart":
        polygons = [validate_target_polygon(row, rgb_shape)]
    else:
        annotations = row.get("ann_list")
        if not isinstance(annotations, list) or len(annotations) != 1:
            raise ValueError("Expected exactly one target annotation")
        segmentation = annotations[0].get("segmentation")
        if not isinstance(segmentation, list) or not segmentation:
            raise ValueError("Expected nonempty segmentation")
        parts = segmentation if isinstance(segmentation[0], list) else [segmentation]
        if polygon_policy == "first_polygon":
            parts = parts[:1]
        polygons = [validate_target_polygon(
            {"height": row.get("height"), "width": row.get("width"),
             "ann_list": [{"segmentation": part}]}, rgb_shape) for part in parts]
    from pycocotools import mask as mask_utils

    height, width = rgb_shape
    rle = mask_utils.frPyObjects(polygons, height, width)
    decoded = mask_utils.decode(rle)
    if decoded.shape != (height, width, len(polygons)):
        raise ValueError("Unexpected decoded GT geometry")
    mask = np.any(decoded, axis=2)[None].astype(np.uint8)
    if not np.isin(mask, [0, 1]).all() or not mask.any():
        raise ValueError("Empty or nonbinary target mask")
    return mask
