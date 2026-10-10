"""Boundary tests for the rebuilt baseline's initialization and trainability."""

import argparse
import ast
import importlib.util
import io
import math
from pathlib import Path
import unittest

from rebuild_baseline import audit_base_keys, configure_alignment_training, select_smoke_input

SOURCE = None


class Param:
    def __init__(self, trainable=False):
        self.requires_grad = trainable

    def requires_grad_(self, value):
        self.requires_grad = value


class Module:
    def __init__(self, parameters):
        self.items = parameters

    def named_parameters(self):
        return iter(self.items.items())

    def parameters(self):
        return iter(self.items.values())


class Model:
    def __init__(self):
        self.tower = Module({"fast_vision_tower.weight": Param(True),
                             "slow_vision_tower.weight": Param(True),
                             "align_stages.0.weight": Param(),
                             "align_stages_latent.0.weight": Param(),
                             "align_stages_latent.1.weight": Param(),
                             "align_stages_latent.2.weight": Param()})
        self.tower.align_stages = [Module({"weight": self.tower.items["align_stages.0.weight"]})]
        self.tower.align_stages_latent = [
            Module({"weight": self.tower.items[f"align_stages_latent.{i}.weight"]})
            for i in range(3)]
        self.head = Param(True)

    def get_model(self):
        return self

    def get_vision_tower(self):
        return self.tower


class TrainabilityTests(unittest.TestCase):
    def test_only_two_alignment_groups_are_unfrozen(self):
        model = Model()
        names = configure_alignment_training(model)
        self.assertEqual(len(names), 4)
        for name, param in model.tower.named_parameters():
            self.assertEqual(param.requires_grad, name.startswith("align_stages"))
        self.assertTrue(model.head.requires_grad)

    def test_missing_group_fails_without_mutating_parameters(self):
        model = Model()
        del model.tower.align_stages_latent
        with self.assertRaises(ValueError):
            configure_alignment_training(model)
        self.assertTrue(model.tower.items["fast_vision_tower.weight"].requires_grad)

    def test_shared_backbone_parameter_is_rejected(self):
        model = Model()
        model.tower.align_stages[0].items["weight"] = model.tower.items["slow_vision_tower.weight"]
        with self.assertRaises(ValueError):
            configure_alignment_training(model)


class LoadingAuditTests(unittest.TestCase):
    def test_projection_is_explicit_reinitialization_not_a_shape_match(self):
        target = {"model.layers.0.weight": [4, 4], "model.mm_projector.weight": [4, 2],
                  "model.mask_decoder.weight": [2, 2]}
        base = {"model.layers.0.weight": [4, 4], "model.mm_projector.0.weight": [4, 2],
                "model.mm_projector.2.weight": [4, 4]}
        audit = audit_base_keys(target, base)
        self.assertEqual(audit["copied_keys"], ["model.layers.0.weight"])
        self.assertIn("model.mm_projector.weight", audit["initialized_keys"])
        self.assertEqual(len(audit["excluded_base_projector_keys"]), 2)

    def test_missing_language_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_base_keys({"model.layers.0.weight": [4, 4]}, {})

    def test_unexpected_language_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_base_keys({}, {"model.layers.99.weight": [4, 4]})

    def test_language_shape_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_base_keys({"lm_head.weight": [4, 4]}, {"lm_head.weight": [5, 4]})

    def test_projection_exclusion_does_not_allow_arbitrary_names(self):
        with self.assertRaises(ValueError):
            audit_base_keys({}, {"model.mm_projector.unknown.weight": [4, 4]})

    def test_anyres_layout_and_external_clip_have_explicit_exclusions(self):
        shapes = {"model.embed_tokens.weight": [32, 4]}
        audit = audit_base_keys(shapes, dict(shapes, **{
            "model.image_newline": [4],
            "model.vision_tower.vision_tower.vision_model.layer.weight": [4, 4]}))
        self.assertEqual(audit["excluded_base_layout_keys"], ["model.image_newline"])
        self.assertEqual(len(audit["excluded_base_vision_keys"]), 1)

    def test_wrong_anyres_layout_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_base_keys({"model.embed_tokens.weight": [32, 4]}, {
                "model.embed_tokens.weight": [32, 4], "model.image_newline": [5]})


class SmokeSelectionTests(unittest.TestCase):
    def test_stable_first_training_id_only_exposes_question(self):
        proposal = {"splits": {"train": {"ids": ["b", "a"]}}}
        rows = [{"id": "a", "questions": ["Which car?"], "answers": ["secret"],
                 "ann_list": ["private"]}, {"id": "b", "questions": ["Other?"]}]
        self.assertEqual(select_smoke_input(proposal, rows), {"id": "a", "question": "Which car?"})

    def test_missing_id_is_not_replaced_by_another_sample(self):
        with self.assertRaises(ValueError):
            select_smoke_input({"splits": {"train": {"ids": ["a"]}}}, [])

    def test_duplicate_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            select_smoke_input({"splits": {"train": {"ids": ["a"]}}},
                               [{"id": "a", "questions": ["Q"]}] * 2)


@unittest.skipUnless(importlib.util.find_spec("torch"), "CPU PyTorch required")
class ActualAlignmentTests(unittest.TestCase):
    def test_fixed_source_gradients_updates_and_adamw_restore(self):
        if SOURCE is None:
            self.skipTest("Audited source path required")
        import torch
        import torch.nn as nn
        import torch.nn.functional as F

        torch.set_num_threads(1)
        torch.manual_seed(17)
        path = SOURCE / "model/llava/multimodal_encoder/multipath_encoder_wapper.py"
        tree = ast.parse(path.read_text())
        names = {"MultiPathAlignModule", "S2FStitchAlignModuleV2"}
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name in names]
        self.assertEqual(len(classes), 2)
        namespace = {"torch": torch, "nn": nn, "F": F, "math": math,
                     "_verbose_log": lambda _: None}
        exec(compile(ast.Module(body=classes, type_ignores=[]), str(path), "exec"), namespace)

        class Tower(nn.Module):
            def __init__(self):
                super().__init__()
                self.fast_vision_tower = nn.Linear(8, 8)
                self.slow_vision_tower = nn.Conv2d(4, 4, 1)
                self.align_stages = nn.ModuleList([
                    namespace["MultiPathAlignModule"](8, 4, {})])
                self.align_stages_latent = nn.ModuleList([
                    namespace["S2FStitchAlignModuleV2"](8, 4, True) for _ in range(3)])

        class Tiny(nn.Module):
            def __init__(self):
                super().__init__()
                self.vision_tower = Tower().to(torch.bfloat16)

            def get_model(self):
                return self

            def get_vision_tower(self):
                return self.vision_tower

            def forward(self, fast, slow):
                fast = self.vision_tower.fast_vision_tower(fast)
                slow = self.vision_tower.slow_vision_tower(slow)
                for module in self.vision_tower.align_stages_latent:
                    fast = module(fast, slow)
                return self.vision_tower.align_stages[0](fast, slow)

        model = Tiny()
        configure_alignment_training(model)
        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                      lr=3e-4, betas=(.9, .95), weight_decay=0)
        fast = torch.randn(1, 16, 8, dtype=torch.bfloat16)
        slow = torch.randn(1, 4, 4, 4, dtype=torch.bfloat16)
        before = {name: p.detach().clone() for name, p in model.named_parameters()}
        optimizer.zero_grad()
        model(fast, slow).float().square().mean().backward()
        for name, p in model.named_parameters():
            if p.requires_grad:
                self.assertIsNotNone(p.grad, name)
                self.assertTrue(torch.isfinite(p.grad).all(), name)
            else:
                self.assertIsNone(p.grad, name)
        optimizer.step()
        for name, p in model.named_parameters():
            if not p.requires_grad:
                self.assertTrue(torch.equal(p, before[name]), name)
        self.assertTrue(any(not torch.equal(p, before[name]) for name, p in model.named_parameters()
                            if p.requires_grad))
        buffer = io.BytesIO()
        torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict()}, buffer)
        restored = Tiny()
        configure_alignment_training(restored)
        second_optimizer = torch.optim.AdamW([p for p in restored.parameters() if p.requires_grad],
                                             lr=3e-4, betas=(.9, .95), weight_decay=0)
        buffer.seek(0)
        state = torch.load(buffer, weights_only=True)
        restored.load_state_dict(state["model"], strict=True)
        second_optimizer.load_state_dict(state["optimizer"])
        torch.testing.assert_close(model(fast, slow), restored(fast, slow), rtol=0, atol=0)
        for candidate, opt in ((model, optimizer), (restored, second_optimizer)):
            opt.zero_grad()
            candidate(fast, slow).float().square().mean().backward()
            opt.step()
        for name, p in model.state_dict().items():
            self.assertTrue(torch.equal(p, restored.state_dict()[name]), name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    SOURCE = args.source.resolve(strict=True) if args.source else None
    unittest.main(argv=[__file__, "-v"])
