"""Synthetic boundary tests; no model or dataset access."""

import unittest

import numpy as np

from mask_metrics import MaskMetrics, score_masks


class MaskScoringTests(unittest.TestCase):
    def test_perfect_foreground_and_strict_zero_threshold(self):
        result = score_masks(np.array([[[1.0, 0.0], [-1.0, 2.0]]]),
                             np.array([[[1, 0], [0, 1]]]))
        self.assertEqual(result[0]["intersection"], 2)
        self.assertEqual(result[0]["union"], 2)
        self.assertAlmostEqual(result[0]["iou"], 2 / (2 + 1e-5))

    def test_disjoint_masks(self):
        result = score_masks(np.array([[[1.0, -1.0]]]), np.array([[[0, 1]]]))
        self.assertEqual(result[0]["iou"], 0)
        self.assertEqual(result[0]["union"], 2)

    def test_empty_union_is_one(self):
        self.assertEqual(score_masks(np.zeros((1, 2, 2)),
                                     np.zeros((1, 2, 2), dtype=np.uint8))[0]["iou"], 1)

    def test_empty_total_union_ciou_matches_fixed_formula(self):
        m = MaskMetrics(["a"])
        m.add("a", "scene", np.zeros((1, 1, 1)), np.zeros((1, 1, 1)))
        result = m.finish()
        self.assertEqual(result["giou"], 1)
        self.assertEqual(result["ciou"], 0)

    def test_input_arrays_are_not_modified(self):
        logits = np.array([[[1.0, -1.0]]])
        targets = np.array([[[255, 0]]])
        before = logits.copy(), targets.copy()
        score_masks(logits, targets)
        np.testing.assert_array_equal(logits, before[0])
        np.testing.assert_array_equal(targets, before[1])

    def test_unknown_category_is_rejected_without_consuming_id(self):
        m = MaskMetrics(["a"])
        mask = np.zeros((1, 1, 1))
        with self.assertRaises(ValueError):
            m.add("a", "made-up", mask, mask)
        m.add("a", "scene", mask, mask)
        self.assertEqual(m.finish()["sample_count"], 1)

    def test_ignore_label_is_excluded(self):
        result = score_masks(np.array([[[10.0, -1.0, 1.0]]]),
                             np.array([[[255, 0, 1]]]))
        self.assertEqual((result[0]["intersection"], result[0]["union"]), (1, 1))

    def test_all_ignored_mask_is_rejected(self):
        with self.assertRaises(ValueError):
            score_masks(np.ones((1, 1, 2)), np.full((1, 1, 2), 255))

    def test_invalid_logits_are_rejected(self):
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                score_masks(np.full((1, 2, 2), value), np.zeros((1, 2, 2)))

    def test_invalid_labels_and_mask_shapes_are_rejected(self):
        for shape in ((2, 2), (0, 2, 2), (1, 0, 2), (2, 2, 2)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                score_masks(np.zeros(shape), np.zeros((1, 2, 2)))
        with self.assertRaises(ValueError):
            score_masks(np.zeros((1, 2, 2)), np.full((1, 2, 2), 0.5))

    def test_giou_and_ciou_are_not_confused(self):
        metrics = MaskMetrics(["small", "large"])
        metrics.add("small", "spatial", np.array([[[1.0, -1.0]]]),
                    np.array([[[1, 0]]]))
        metrics.add("large", "attribute", -np.ones((1, 1, 9)), np.ones((1, 1, 9)))
        result = metrics.finish()
        self.assertAlmostEqual(result["giou"], (1 / (1 + 1e-5)) / 2)
        self.assertAlmostEqual(result["ciou"], 1 / (10 + 1e-10))
        self.assertEqual(result["sample_count"], 2)
        self.assertEqual(result["mask_count"], 2)
        self.assertEqual(result["by_reasoning_type"]["spatial"]["sample_count"], 1)

    def test_manifest_duplicates_missing_and_extra_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            MaskMetrics(["a", "a"])
        with self.assertRaises(ValueError):
            MaskMetrics([])
        m = MaskMetrics(["a", "b"])
        mask = np.zeros((1, 1, 1))
        with self.assertRaises(ValueError):
            m.add("extra", "scene", mask, mask)
        m.add("a", "scene", mask, mask)
        with self.assertRaises(ValueError):
            m.add("a", "scene", mask, mask)
        with self.assertRaises(ValueError):
            m.finish()

    def test_failed_add_does_not_consume_manifest_id(self):
        m = MaskMetrics(["a"])
        with self.assertRaises(ValueError):
            m.add("a", "scene", np.full((1, 1, 1), np.nan), np.ones((1, 1, 1)))
        m.add("a", "scene", np.ones((1, 1, 1)), np.ones((1, 1, 1)))
        self.assertEqual(m.finish()["sample_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
