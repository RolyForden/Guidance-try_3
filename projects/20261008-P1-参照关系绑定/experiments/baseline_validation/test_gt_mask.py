"""Synthetic GT decoding contracts; no model or original dataset access."""

import importlib.util
import unittest

import numpy as np

from gt_mask import decode_target_mask, validate_target_polygon


def row(polygon):
    return {"height": 10, "width": 12, "ann_list": [{"segmentation": polygon}]}


class PolygonTests(unittest.TestCase):
    def test_flat_and_single_nested_polygon_are_equivalent(self):
        polygon = [1, 1, 8, 1, 8, 8, 1, 8]
        self.assertEqual(validate_target_polygon(row(polygon), (10, 12)), polygon)
        self.assertEqual(validate_target_polygon(row([polygon]), (10, 12)), polygon)

    def test_multiple_polygons_are_not_silently_discarded(self):
        with self.assertRaises(ValueError):
            validate_target_polygon(row([[1, 1, 8, 1, 8, 8], [0, 0, 2, 0, 2, 2]]), (10, 12))

    def test_declared_geometry_must_match_rgb(self):
        with self.assertRaises(ValueError):
            validate_target_polygon(row([1, 1, 8, 1, 8, 8]), (12, 10))

    def test_bad_coordinates_are_rejected(self):
        for polygon in ([], [1, 2, 3], [1, 1, 2, 1, 2, 2, 3],
                        [1, 1, float("nan"), 1, 2, 2], [1, 1, 1, 1, 1, 1]):
            with self.subTest(polygon=polygon), self.assertRaises(ValueError):
                validate_target_polygon(row(polygon), (10, 12))

    def test_requires_exactly_one_target_annotation(self):
        for annotations in ([], [{"segmentation": [1, 1, 8, 1, 8, 8]}] * 2):
            sample = row([])
            sample["ann_list"] = annotations
            with self.assertRaises(ValueError):
                validate_target_polygon(sample, (10, 12))

    def test_unknown_polygon_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            decode_target_mask(row([1, 1, 8, 1, 8, 8]), (10, 12), polygon_policy="guess")


@unittest.skipUnless(importlib.util.find_spec("pycocotools"), "Fixed pycocotools runtime required")
class DecodeTests(unittest.TestCase):
    def test_union_and_explicit_upstream_first_polygon(self):
        sample = row([[1, 1, 4, 1, 4, 4, 1, 4], [9, 8, 11, 8, 11, 10, 9, 10]])
        union = decode_target_mask(sample, (10, 12), polygon_policy="union")
        first = decode_target_mask(sample, (10, 12), polygon_policy="first_polygon")
        self.assertEqual(int(union.sum()), 13)
        self.assertEqual(int(first.sum()), 9)
        self.assertTrue((union >= first).all())

    def test_rectangle_rasterization_and_binary_shape(self):
        mask = decode_target_mask(row([1, 1, 8, 1, 8, 8, 1, 8]), (10, 12))
        expected = np.zeros((1, 10, 12), dtype=np.uint8)
        expected[0, 1:8, 1:8] = 1
        np.testing.assert_array_equal(mask, expected)

    def test_empty_rasterization_is_rejected(self):
        with self.assertRaises(ValueError):
            decode_target_mask(row([20, 20, 25, 20, 25, 25]), (10, 12))


if __name__ == "__main__":
    unittest.main()
