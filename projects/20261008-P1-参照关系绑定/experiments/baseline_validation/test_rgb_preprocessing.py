"""RGB engineering tests; no pretrained model or DRSeg sample access."""

import argparse
import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

import rgb_preprocessing as rgb_inputs


SOURCE = None


class RgbBoundaryTests(unittest.TestCase):
    def test_test_split_is_rejected_before_filesystem_access(self):
        with self.assertRaises(ValueError):
            rgb_inputs.read_rgb(Path("missing_dataset"), "test", "1")

    def test_unsafe_image_id_is_rejected_before_filesystem_access(self):
        for image_id in ("../x", "a/b", "a\\b", "", ".", ".."):
            with self.subTest(image_id=image_id), self.assertRaises(ValueError):
                rgb_inputs.read_rgb(Path("missing_dataset"), "val", image_id)

    def test_invalid_rgb_is_rejected_before_torch_import(self):
        for array in (np.zeros((2, 2)), np.zeros((2, 2, 4), dtype=np.uint8),
                      np.zeros((2, 2, 3)), np.zeros((0, 2, 3), dtype=np.uint8)):
            with self.subTest(shape=array.shape), self.assertRaises(ValueError):
                rgb_inputs.prepare_rgb_inputs(array, detail_transform=None, clip_processor=None)


@unittest.skipUnless(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers"),
                     "Requires the fixed runtime with CPU PyTorch and Transformers")
class OfficialRgbTests(unittest.TestCase):
    def test_official_resize_clip_and_detail_normalization(self):
        import torch

        transform, processor = rgb_inputs.build_preprocessors(SOURCE)
        rgb = np.empty((300, 400, 3), dtype=np.uint8)
        rgb[:] = [255, 32, 8]
        before = rgb.copy()
        actual = rgb_inputs.prepare_rgb_inputs(rgb, detail_transform=transform,
                                              clip_processor=processor)
        self.assertEqual(set(actual), {"images", "images_clip", "resize_list",
                                      "clip_resize_list", "original_size_list"})
        self.assertEqual(actual["images"].shape, (1, 3, 1024, 1024))
        self.assertEqual(actual["images_clip"].shape, (1, 3, 448, 448))
        self.assertEqual(actual["resize_list"], [(768, 1024)])
        self.assertEqual(actual["clip_resize_list"], [(448, 448)])
        self.assertEqual(actual["original_size_list"], [(300, 400)])
        reference_clip = processor.preprocess(rgb, return_tensors="pt")["pixel_values"]
        self.assertTrue(torch.equal(reference_clip, actual["images_clip"]))
        mean = torch.tensor([123.675, 116.28, 103.53])
        std = torch.tensor([58.395, 57.12, 57.375])
        expected = (torch.tensor([255., 32., 8.]) - mean) / std
        torch.testing.assert_close(actual["images"][0, :, 100, 100], expected)
        self.assertEqual(torch.count_nonzero(actual["images"][:, :, 768:]).item(), 0)
        self.assertTrue(torch.isfinite(actual["images"]).all())
        np.testing.assert_array_equal(rgb, before)

    def test_portrait_geometry_is_not_transposed(self):
        transform, processor = rgb_inputs.build_preprocessors(SOURCE)
        actual = rgb_inputs.prepare_rgb_inputs(np.zeros((400, 300, 3), dtype=np.uint8),
                                              detail_transform=transform, clip_processor=processor)
        self.assertEqual(actual["resize_list"], [(1024, 768)])
        self.assertEqual(actual["original_size_list"], [(400, 300)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    SOURCE = args.source.resolve(strict=True)
    sys.path.insert(0, str(SOURCE))
    unittest.main(argv=[__file__, "-v"])
