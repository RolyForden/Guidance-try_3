"""Engineering checks only: no pretrained model, dataset or evaluator is run."""

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


HERE = Path(__file__).resolve().parent
SOURCE = None
TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def official_method(relative_path, name):
    tree = ast.parse((SOURCE / relative_path).read_text(encoding="utf-8"))
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name == name)


class SourceContractTests(unittest.TestCase):
    def helper(self):
        method = official_method("model/llava/language_model/llava_llama.py",
                                 "prepare_inputs_for_generation")
        namespace = {}
        exec(compile(ast.fix_missing_locations(ast.Module(
            body=[method], type_ignores=[])), "<official helper>", "exec"), namespace)
        return namespace[method.name]

    def test_generation_prefill_preserves_text_features(self):
        feature = object()
        ids = object()
        result = self.helper()(object(), ids, txt_feat=feature)
        self.assertIs(result.get("txt_feat"), feature)
        self.assertIs(result["input_ids"], ids)

    def test_generation_signature_declares_feature_for_transformers_validation(self):
        import inspect
        self.assertIn("txt_feat", inspect.signature(self.helper()).parameters)

    @unittest.skipUnless(importlib.util.find_spec("transformers"), "Transformers required")
    def test_real_generation_validator_accepts_feature_and_rejects_typo(self):
        from transformers.generation.utils import GenerationMixin

        dummy = type("GenerationContract", (GenerationMixin,), {
            "prepare_inputs_for_generation": self.helper(),
            "forward": lambda self, **kwargs: None,
            "config": types.SimpleNamespace(is_encoder_decoder=False)})()
        dummy._validate_model_kwargs({"txt_feat": object()})
        with self.assertRaises(ValueError):
            dummy._validate_model_kwargs({"txt_feet": object()})

    def test_generation_cached_step_preserves_text_features(self):
        feature = object()
        last_token = object()

        class InputIds:
            def __getitem__(self, index):
                return last_token

        result = self.helper()(object(), InputIds(), past_key_values=(object(),),
                               txt_feat=feature)
        self.assertIs(result.get("txt_feat"), feature)
        self.assertIs(result["input_ids"], last_token)

    def test_generation_embeds_prefill_preserves_text_features(self):
        feature, embeds = object(), object()
        result = self.helper()(object(), object(), inputs_embeds=embeds,
                               txt_feat=feature)
        self.assertIs(result.get("txt_feat"), feature)
        self.assertIs(result["inputs_embeds"], embeds)

    def test_evaluate_supplies_text_features_to_generate(self):
        method = official_method("model/PixDLM.py", "evaluate")
        calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "generate"]
        self.assertEqual(len(calls), 1)
        feature = next((k.value for k in calls[0].keywords if k.arg == "txt_feat"), None)
        self.assertIsNotNone(feature, "evaluate drops txt_feat at generate boundary")
        self.assertEqual(ast.dump(feature), ast.dump(ast.Name(id="txt_feat", ctx=ast.Load())))

    def test_only_approved_two_source_changes(self):
        original = SOURCE.parent / "PixDLM-hf-f40fa58"
        expected_hashes = {
            "model/PixDLM.py": "e3ec1bf1e18b215d29ab8e0ccf549a42579db3fd7b1a511f10ab498bd35afda5",
            "model/llava/language_model/llava_llama.py":
                "1c8248edfe3d0c3c026d2a46c783dc5e02f320150da72850f85fd5c2737b089d",
        }
        for relative, digest in expected_hashes.items():
            raw = (original / relative).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            tree = ast.parse((SOURCE / relative).read_text(encoding="utf-8"))
            if relative == "model/PixDLM.py":
                evaluate = next(n for n in ast.walk(tree)
                                if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
                call = next(n for n in ast.walk(evaluate) if isinstance(n, ast.Call)
                            and isinstance(n.func, ast.Attribute) and n.func.attr == "generate")
                self.assertIn("txt_feat", [k.arg for k in call.keywords])
                call.keywords = [k for k in call.keywords if k.arg != "txt_feat"]
            else:
                helper = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                              and n.name == "prepare_inputs_for_generation")
                mapping = next(n for n in ast.walk(helper) if isinstance(n, ast.Dict)
                               and any(isinstance(k, ast.Constant) and k.value == "txt_feat"
                                       for k in n.keys))
                index = next(i for i, k in enumerate(mapping.keys) if isinstance(k, ast.Constant)
                             and k.value == "txt_feat")
                mapping.keys.pop(index)
                mapping.values.pop(index)
                if "txt_feat" in [arg.arg for arg in helper.args.args]:
                    index = next(i for i, arg in enumerate(helper.args.args)
                                 if arg.arg == "txt_feat")
                    first_default = len(helper.args.args) - len(helper.args.defaults)
                    helper.args.defaults.pop(index - first_default)
                    helper.args.args.pop(index)
            self.assertEqual(ast.dump(tree), ast.dump(ast.parse(raw)))
        changed = set()
        for path in original.rglob("*"):
            relative = path.relative_to(original)
            if path.is_file() and not {".cache", "__pycache__"}.intersection(relative.parts):
                if path.read_bytes() != (SOURCE / relative).read_bytes():
                    changed.add(relative.as_posix())
        self.assertEqual(changed, set(expected_hashes))


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HERE / "question_only.py").is_file(),
                        "question-only adapter has not been implemented")
        self.adapter = load_module("question_only", HERE / "question_only.py")
        self.conversation = load_module("p1_official_conversation",
                                        SOURCE / "utils/conversation.py").conv_templates["llava_v1"]

    def test_prompt_has_empty_assistant_and_no_seg_tokens(self):
        question = "Which vehicle is next to the building?"
        before = copy.deepcopy(self.conversation.messages)
        prompt = self.adapter.build_question_prompt(question, self.conversation)
        self.assertIn("<im_start><image><im_end>\n" + question, prompt)
        self.assertTrue(prompt.endswith("ASSISTANT:"))
        self.assertNotIn("[SEG", prompt)
        self.assertEqual(self.conversation.messages, before)

    def test_prompt_without_image_boundary_tokens(self):
        prompt = self.adapter.build_question_prompt("Locate the vehicle.",
                                                    self.conversation, use_mm_start_end=False)
        self.assertIn("<image>\nLocate the vehicle.", prompt)
        self.assertNotIn("<im_start>", prompt)

    def test_invalid_or_preconditioned_questions_are_rejected(self):
        for question in ("", "  ", None, "Locate [SEG0]", "<image> Locate it.",
                         "Locate it. <answer>vehicle</answer>", "<think>answer</think>"):
            with self.subTest(question=question), self.assertRaises(ValueError):
                self.adapter.build_question_prompt(question, self.conversation)

    def test_local_mapping_changes_only_two_vision_paths(self):
        original = {"model_type": "llava", "vision_tower": "remote-clip",
                    "mm_vision_tower": "remote-clip", "hidden_size": 4096,
                    "nested": {"unchanged": True}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "pretrained/pixdlm-7b"
            clip = root / "models/clip-vit-large-patch14"
            checkpoint.mkdir(parents=True)
            clip.mkdir(parents=True)
            (checkpoint / "config.json").write_text(json.dumps(original), encoding="utf-8")
            (clip / "config.json").write_text("{}", encoding="utf-8")
            (clip / "preprocessor_config.json").write_text("{}", encoding="utf-8")
            (clip / "model.safetensors").write_bytes(b"test fixture, not model weights")
            mapped = self.adapter.local_model_config(root)
            for key, value in original.items():
                if key not in ("vision_tower", "mm_vision_tower"):
                    self.assertEqual(mapped[key], value)
            self.assertEqual(mapped["vision_tower"], str(clip.resolve()))
            self.assertEqual(mapped["mm_vision_tower"], str(clip.resolve()))
            self.assertEqual(json.loads((checkpoint / "config.json").read_text()), original)
            (clip / "preprocessor_config.json").unlink()
            with self.assertRaises(FileNotFoundError):
                self.adapter.local_model_config(root)

    @unittest.skipUnless(TORCH_AVAILABLE, "PyTorch needed for CPU tensor contract checks")
    def test_question_feature_tokens_exclude_conversation_and_ground_truth(self):
        import torch

        self.assertTrue(hasattr(self.adapter, "prepare_question_inputs"),
                        "question-only feature construction is missing")

        class Tokenizer:
            bos_token_id = 1

            def __call__(self, text, return_tensors=None):
                ids = [1] + [ord(char) + 2 for char in text]
                if return_tensors:
                    ids = torch.tensor([ids])
                    return types.SimpleNamespace(input_ids=ids, attention_mask=torch.ones_like(ids))
                return types.SimpleNamespace(input_ids=ids)

        class Backbone(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = torch.nn.Embedding(512, 4)
                self.seen_ids = []

            def forward(self, input_ids, **kwargs):
                self.seen_ids.append(input_ids.clone())
                return types.SimpleNamespace(hidden_states=(self.embedding(input_ids),))

        tokenize_image = load_module("p1_official_mm_utils",
                                     SOURCE / "model/llava/mm_utils.py").tokenizer_image_token
        tokenizer, backbone = Tokenizer(), Backbone().eval()
        records = [{"question": "Locate the vehicle.", "answers": "A", "gt_mask": [0]},
                   {"question": "Locate the vehicle.", "answers": "B", "gt_mask": [1]}]
        outputs = [self.adapter.prepare_question_inputs(
            record["question"], tokenizer, self.conversation, backbone,
            tokenize_image=tokenize_image, device="cpu") for record in records]
        self.assertTrue(torch.equal(outputs[0]["input_ids"], outputs[1]["input_ids"]))
        self.assertTrue(torch.equal(outputs[0]["txt_feat"], outputs[1]["txt_feat"]))
        self.assertTrue(torch.equal(backbone.seen_ids[0], tokenizer(records[0]["question"],
                                                                    return_tensors="pt").input_ids))
        self.assertEqual((outputs[0]["input_ids"] == -200).sum().item(), 1)
        self.assertFalse(outputs[0]["txt_feat"].requires_grad)
        with self.assertRaises(TypeError):
            self.adapter.prepare_question_inputs(
                records[0]["question"], tokenizer, self.conversation, backbone,
                tokenize_image=tokenize_image, device="cpu", answers="forbidden")
        self.assertTrue(hasattr(self.adapter, "prepare_model_inputs"),
                        "RGB plus question input whitelist is missing")
        model = types.SimpleNamespace(training=False, get_model=lambda: backbone,
                                      config=types.SimpleNamespace(mm_use_im_start_end=True))
        images = torch.zeros(1, 3, 448, 448)
        rgb_kwargs = dict(images=images, images_clip=images, resize_list=[(448, 448)],
                          clip_resize_list=[(448, 448)], original_size_list=[(448, 448)])
        inputs = self.adapter.prepare_model_inputs(
            records[0]["question"], tokenizer, self.conversation, model,
            tokenize_image=tokenize_image, **rgb_kwargs)
        self.assertEqual(set(inputs), {"input_ids", "txt_feat", "images", "images_clip",
                                     "resize_list", "clip_resize_list", "original_size_list",
                                     "max_new_tokens", "tokenizer"})
        self.assertIs(inputs["images"], images)
        self.assertTrue(torch.equal(inputs["txt_feat"], outputs[0]["txt_feat"]))
        with self.assertRaises(TypeError):
            self.adapter.prepare_model_inputs(
                records[0]["question"], tokenizer, self.conversation, model,
                tokenize_image=tokenize_image, **rgb_kwargs, gt_masks=[1])
        rgb_kwargs["images_clip"] = torch.zeros(2, 3, 448, 448)
        with self.assertRaises(ValueError):
            self.adapter.prepare_model_inputs(
                records[0]["question"], tokenizer, self.conversation, model,
                tokenize_image=tokenize_image, **rgb_kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    arguments, unittest_arguments = parser.parse_known_args()
    SOURCE = arguments.source.resolve(strict=True)
    unittest.main(argv=[sys.argv[0]] + unittest_arguments)
