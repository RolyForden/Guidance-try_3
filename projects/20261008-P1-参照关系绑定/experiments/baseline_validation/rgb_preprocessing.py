"""Fixed-source RGB preprocessing without a dataset/annotation constructor."""

from pathlib import Path

import numpy as np


def read_rgb(dataset_root, split, image_id):
    if split not in ("train", "val"):
        raise ValueError("Only prepared train/val RGB images are allowed")
    if not isinstance(image_id, str) or image_id in ("", ".", "..") or any(
            c in image_id for c in ("/", "\\", "\0")):
        raise ValueError("Unsafe image ID")
    root = Path(dataset_root).resolve(strict=True)
    directory = (root / "CODrone" / ("DR" + split)).resolve(strict=True)
    image_path = (directory / (image_id + ".jpg")).resolve(strict=True)
    if not directory.is_relative_to(root) or not image_path.is_relative_to(directory):
        raise ValueError("RGB path escapes the prepared split")
    import cv2

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Cannot decode the specified RGB image")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def build_preprocessors(source_root):
    """Caller places the audited source first on sys.path; do not import a dataset."""
    from model.segment_anything.utils import transforms
    import transformers

    source = Path(source_root).resolve(strict=True)
    if not Path(transforms.__file__).resolve().is_relative_to(source):
        raise ValueError("Resize transform was imported from a different source")
    if transformers.__version__ != "4.31.0":
        raise ValueError("Expected the fixed Transformers 4.31.0 runtime")
    processor = transformers.CLIPImageProcessor.from_pretrained(
        str(source / "configs/preprocessor_448.json"), local_files_only=True)
    if processor.size != {"shortest_edge": 448} or processor.crop_size != {
            "height": 448, "width": 448} or not all((processor.do_resize,
            processor.do_center_crop, processor.do_normalize, processor.do_rescale)):
        raise ValueError("Unexpected fixed CLIP preprocessing configuration")
    return transforms.ResizeLongestSide(1024), processor


def prepare_rgb_inputs(rgb, *, detail_transform, clip_processor):
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8 or any(
            n == 0 for n in rgb.shape):
        raise ValueError("Expected a nonempty uint8 RGB array [H,W,3]")
    import torch
    import torch.nn.functional as F

    if detail_transform.target_length != 1024:
        raise ValueError("Expected fixed long-side resize to 1024")
    clip = clip_processor.preprocess(rgb, return_tensors="pt")["pixel_values"]
    if clip.shape != (1, 3, 448, 448) or not torch.isfinite(clip).all():
        raise ValueError("Invalid CLIP RGB tensor")
    resized = detail_transform.apply_image(rgb)
    h, w = resized.shape[:2]
    if max(h, w) != 1024 or min(h, w) <= 0:
        raise ValueError("Invalid detail-image resize geometry")
    detail = torch.from_numpy(resized).permute(2, 0, 1).contiguous().float()
    mean = detail.new_tensor([123.675, 116.28, 103.53]).view(3, 1, 1)
    std = detail.new_tensor([58.395, 57.12, 57.375]).view(3, 1, 1)
    detail = F.pad((detail - mean) / std, (0, 1024 - w, 0, 1024 - h))
    return {"images": detail.unsqueeze(0), "images_clip": clip,
            "resize_list": [(h, w)], "clip_resize_list": [tuple(clip.shape[-2:])],
            "original_size_list": [tuple(rgb.shape[:2])]}
