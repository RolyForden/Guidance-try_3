"""Check generation contracts without loading the published model or data."""

import argparse
import ast
import hashlib
import importlib.util
from pathlib import Path
import types
import unittest


SOURCE = None


def evaluate_method():
    tree = ast.parse((SOURCE / "model/PixDLM.py").read_text(encoding="utf-8"))
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "evaluate")


class GenerationAlignmentTests(unittest.TestCase):
    def test_alignment_patch_has_no_other_source_changes(self):
        previous = SOURCE.parent / "PixDLM-question-only-f40fa58"
        path = Path("model/PixDLM.py")
        raw = (previous / path).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "61e92f483d772e87e5edff97609f0aa9928d90ed4fa7bf5d38ad72153204d626")
        tree = ast.parse((SOURCE / path).read_text(encoding="utf-8"))
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == "evaluate")
        call = next(n for n in ast.walk(method) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "generate")
        call.keywords = [k for k in call.keywords if k.arg != "use_cache"]
        for node in ast.walk(method):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
                    and t.id == "output_hidden_states" for t in node.targets):
                node.value = ast.parse("outputs.hidden_states[-1]", mode="eval").body
            if isinstance(node, ast.For):
                node.body = [n for n in node.body if not (isinstance(n, ast.If)
                             and "output_hidden_states" in ast.unparse(n.test))]
        self.assertEqual(ast.dump(tree), ast.dump(ast.parse(raw)))
        for original in previous.rglob("*"):
            relative = original.relative_to(previous)
            if original.is_file() and relative != path and not {
                    "__pycache__", ".cache"}.intersection(relative.parts):
                self.assertEqual(original.read_bytes(), (SOURCE / relative).read_bytes(),
                                 str(relative))

    def test_generate_locks_loaded_cached_contract(self):
        call = next(n for n in ast.walk(evaluate_method()) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "generate")
        value = next((k.value for k in call.keywords if k.arg == "use_cache"), None)
        self.assertIsNotNone(value, "loaded generation config defaults to cache=True")
        self.assertIsInstance(value, ast.Constant)
        self.assertIs(value.value, True)

    def test_each_generation_step_contributes_last_layer(self):
        assignment = next(n for n in ast.walk(evaluate_method()) if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "output_hidden_states"
                                  for t in n.targets))
        self.assertIsInstance(assignment.value, ast.Call,
                              "cached output must join prefill and one-token steps")
        self.assertEqual(ast.unparse(assignment.value.func), "torch.cat")
        self.assertEqual(ast.unparse(assignment.value.args[0]),
                         "[step[-1] for step in outputs.hidden_states]")
        dim = next(k.value for k in assignment.value.keywords if k.arg == "dim")
        self.assertEqual(dim.value, 1)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "Requires CPU PyTorch")
    def test_tensor_concatenation_preserves_prefill_and_generated_positions(self):
        import torch

        assignment = next(n for n in ast.walk(evaluate_method()) if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "output_hidden_states"
                                  for t in n.targets))
        layers = [(torch.zeros(1, length, 4), torch.full((1, length, 4), value))
                  for length, value in [(4, 1.0), (1, 2.0), (1, 3.0)]]
        actual = eval(compile(ast.Expression(assignment.value), "<official evaluate>", "eval"),
                      {"outputs": types.SimpleNamespace(hidden_states=tuple(layers)), "torch": torch})
        self.assertIsInstance(actual, torch.Tensor)
        self.assertTrue(torch.equal(actual, torch.cat([step[-1] for step in layers], dim=1)))
        self.assertEqual(actual.shape, (1, 6, 4))

    def test_seg_alignment_mismatch_fails_instead_of_silent_padding(self):
        guards = [n for n in ast.walk(evaluate_method()) if isinstance(n, ast.If)
                  and "output_hidden_states" in ast.unparse(n.test)
                  and any(isinstance(r, ast.Raise) for r in n.body)]
        self.assertEqual(len(guards), 1, "missing generation/SEG sequence alignment check")
        code = compile(ast.fix_missing_locations(ast.Module(body=guards, type_ignores=[])),
                       "<official alignment guard>", "exec")
        for shape, should_fail in [((1, 278, 4), False), ((1, 1, 4), True),
                                   ((2, 278, 4), True), ((1, 279, 4), True),
                                   ((1, 278, 4, 1), True)]:
            namespace = {"output_ids": types.SimpleNamespace(shape=(1, 24)),
                         "self": types.SimpleNamespace(_last_visual_token_num=255),
                         "output_hidden_states": types.SimpleNamespace(shape=shape, ndim=len(shape))}
            with self.subTest(shape=shape):
                if should_fail:
                    with self.assertRaises(RuntimeError):
                        exec(code, namespace)
                else:
                    exec(code, namespace)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    SOURCE = args.source.resolve(strict=True)
    unittest.main(argv=[__file__, "-v"])
