"""Audited foundation loading and alignment trainability; no training launcher."""

import argparse
import gc
import json
import os
from pathlib import Path
import random
import sys


_NEW = ("model.prompt_encoder.", "model.mask_decoder.",
        "model.image_feature_neck.", "model.sam_to_embed_conv.",
        "model.text_hidden_fcs.")
_PROJECTOR = {"model.mm_projector.weight", "model.mm_projector.bias"}
_BASE_PROJECTOR = {f"model.mm_projector.{layer}.{kind}"
                   for layer in (0, 2) for kind in ("weight", "bias")}


def audit_base_keys(target_shapes, base_shapes):
    copied, initialized, external, deterministic, excluded = [], [], [], [], []
    excluded_layout, excluded_vision = [], []
    for name, shape in target_shapes.items():
        if name.startswith("model.vision_tower."):
            external.append(name)
        elif name in base_shapes:
            if list(shape) != list(base_shapes[name]):
                raise ValueError(f"Foundation shape mismatch: {name}")
            copied.append(name)
        elif name.startswith(_NEW) or name in _PROJECTOR:
            initialized.append(name)
        elif name.endswith(".rotary_emb.inv_freq") and name.startswith("model.layers."):
            deterministic.append(name)
        else:
            raise ValueError(f"Unexplained missing foundation key: {name}")
    for name in base_shapes:
        if name in copied:
            continue
        if name in _BASE_PROJECTOR:
            excluded.append(name)
        elif name == "model.image_newline" and list(base_shapes[name]) == [
                target_shapes.get("model.embed_tokens.weight", [0, 0])[-1]]:
            excluded_layout.append(name)
        elif name.startswith("model.vision_tower.vision_tower.vision_model."):
            excluded_vision.append(name)
        else:
            raise ValueError(f"Unexpected foundation key: {name}")
    return {"copied_keys": sorted(copied), "initialized_keys": sorted(initialized),
            "external_vision_keys": sorted(external),
            "deterministic_buffer_keys": sorted(deterministic),
            "excluded_base_projector_keys": sorted(excluded),
            "excluded_base_layout_keys": sorted(excluded_layout),
            "excluded_base_vision_keys": sorted(excluded_vision)}


def configure_alignment_training(model):
    tower = model.get_model().get_vision_tower()
    groups = [getattr(tower, name, None) for name in ("align_stages", "align_stages_latent")]
    if groups[0] is None or groups[1] is None or len(groups[0]) != 1 or len(groups[1]) != 3:
        raise ValueError("Expected one final and three latent alignment modules")
    intended = {id(p) for group in groups for module in group for p in module.parameters()}
    named = list(tower.named_parameters())
    declared = {id(p) for name, p in named
                if name.startswith(("align_stages.", "align_stages_latent."))}
    if not intended or intended != declared or any(
            id(p) in intended and not name.startswith(("align_stages.", "align_stages_latent."))
            for name, p in named):
        raise ValueError("Alignment parameter ownership mismatch")
    for name, parameter in named:
        parameter.requires_grad_(id(parameter) in intended)
    return sorted(name for name, p in named if p.requires_grad)


def select_smoke_input(proposal, rows):
    ids = proposal["splits"]["train"]["ids"]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Invalid training manifest IDs")
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows) or any(image_id not in by_id for image_id in ids):
        raise ValueError("Missing or duplicate training records")
    image_id = sorted(ids)[0]
    questions = by_id[image_id].get("questions")
    if not isinstance(questions, list) or len(questions) != 1 or not isinstance(questions[0], str):
        raise ValueError("Expected one original question")
    return {"id": image_id, "question": questions[0]}


def smoke_generation(model, tokenizer, source, dataset, manifest):
    import torch
    from question_only import prepare_model_inputs
    from rgb_preprocessing import read_rgb, build_preprocessors, prepare_rgb_inputs
    from model.llava import conversation as conversation_lib
    from model.llava.mm_utils import tokenizer_image_token

    dataset = Path(dataset).resolve(strict=True)
    rows = json.loads((dataset / "labels/DRSeg_train.json").read_text())
    proposal = json.loads(Path(manifest).read_text())
    selected = select_smoke_input(proposal, rows)
    changed = [{"id": row["id"], "questions": row["questions"],
                "answers": ["REPLACED"], "ann_list": []} for row in rows]
    if selected != select_smoke_input(proposal, changed):
        raise RuntimeError("GT field mutation changed selected inference input")
    rgb = read_rgb(dataset, "train", selected["id"])
    detail, clip = build_preprocessors(source)
    rgb_inputs = prepare_rgb_inputs(rgb, detail_transform=detail, clip_processor=clip)
    device = next(model.parameters()).device
    if device.type != "cuda":
        raise ValueError("The fixed multimodal source requires CUDA")
    for key in ("images", "images_clip"):
        rgb_inputs[key] = rgb_inputs[key].to(device=device, dtype=torch.bfloat16)
    with torch.inference_mode():
        inputs = prepare_model_inputs(
            selected["question"], tokenizer, conversation_lib.conv_templates["llava_v1"],
            model, tokenize_image=tokenizer_image_token, max_new_tokens=8, **rgb_inputs)
        raw = model.base_model.model
        output = raw.generate(input_ids=inputs["input_ids"], images=inputs["images_clip"],
                              clip_resize_list=inputs["clip_resize_list"], txt_feat=inputs["txt_feat"],
                              max_new_tokens=8, do_sample=False, num_beams=1, use_cache=True,
                              output_hidden_states=True, return_dict_in_generate=True)
        hidden = torch.cat(list(output.hidden_states), dim=1)
        expected = output.sequences.shape[1] - 1 + raw._last_visual_token_num
        if hidden.shape[:2] != (1, expected) or not torch.isfinite(hidden).all():
            raise RuntimeError("Actual multimodal cached generation alignment/finite check failed")
    return {"sample_id": selected["id"], "input_fields": ["RGB", "original_question"],
            "raw_rgb_shape": list(rgb.shape), "txt_feat_shape": list(inputs["txt_feat"].shape),
            "generation_hidden_shape": list(hidden.shape),
            "visual_extra_tokens": raw._last_visual_token_num,
            "generated_new_tokens": output.sequences.shape[1] - inputs["input_ids"].shape[1],
            "max_new_tokens": 8, "gt_mutation_input_selection_unchanged": True,
            "decoder_mask_or_metric_acceptance": False,
            "untrained_engineering_smoke_only": True,
            "cuda_peak_allocated_bytes": torch.cuda.max_memory_allocated()}


def load_rebuilt_model(source, deployment, base, seed, device):
    import numpy as np
    import torch
    from safetensors import safe_open
    from transformers import AutoTokenizer

    source, deployment, base = (Path(p).resolve(strict=True) for p in (source, deployment, base))
    sys.path.insert(0, str(source))
    os.environ["PIXDLM_ROOT"] = str(deployment)
    from model.PixDLM import PixDLMForCausalLM
    from model.llava.language_model.llava_llama import LlavaConfig

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(str(base), use_fast=False,
                                              local_files_only=True, padding_side="right",
                                              model_max_length=512, legacy=True)
    tokenizer.pad_token = tokenizer.unk_token
    seg_tokens = [f"[SEG{i}]" for i in range(9)]
    tokenizer.add_tokens(seg_tokens)
    tokenizer.add_tokens(["<think>", "</think>", "<answer>", "</answer>"])
    tokenizer.add_tokens(["<im_start>", "<im_end>"], special_tokens=True)
    seg_ids = [tokenizer(t, add_special_tokens=False).input_ids[0] for t in seg_tokens]
    config_data = json.loads((base / "config.json").read_text())
    clip = str(deployment / "models/clip-vit-large-patch14")
    config_data.update(vision_tower=clip, mm_vision_tower=clip)
    config = LlavaConfig.from_dict(config_data)
    kwargs = dict(train_mask_decoder=True, out_dim=256, ce_loss_weight=1.,
                  dice_loss_weight=.5, bce_loss_weight=2., seg_token_idx=seg_ids,
                  seg_token_num=3, image_feature_scale_num=3, tokenizer=tokenizer,
                  vision_tower=clip, local_rank=0, pad_train_clip_images=False,
                  resize_vision_tower=True, resize_vision_tower_size=448,
                  vision_tower_for_mask=True, separate_mm_projector=False,
                  three_level_multi_scale_decoder=True, is_multipath_encoder=True,
                  freeze_vision=False, use_mm_start_end=True)
    previous_dtype = torch.get_default_dtype()
    try:
        # FP32 initialization avoids the slow CPU BF16 random kernel; cast before copying.
        torch.set_default_dtype(torch.float32)
        model = PixDLMForCausalLM(config, **kwargs)
        # Reload external towers after the outer model's post_init, as in train_ds.
        model.get_model().initialize_vision_modules(model.config)
        model.get_model().initialize_pixdlm_modules(model.config)
    finally:
        torch.set_default_dtype(previous_dtype)
    gc.collect()
    model = model.to(dtype=torch.bfloat16)
    index = json.loads((base / "model.safetensors.index.json").read_text())
    weight_map = index["weight_map"]
    shapes = {}
    for filename in sorted(set(weight_map.values())):
        if Path(filename).name != filename:
            raise ValueError("Unexpected shard path")
        with safe_open(str(base / filename), framework="pt", device="cpu") as shard:
            for name in shard.keys():
                if weight_map.get(name) != filename or name in shapes:
                    raise ValueError("Shard index/key disagreement")
                shapes[name] = list(shard.get_slice(name).get_shape())
    if set(shapes) != set(weight_map):
        raise ValueError("Shard coverage mismatch")
    target = model.state_dict()
    audit = audit_base_keys({k: list(v.shape) for k, v in target.items()}, shapes)
    with torch.no_grad():
        copied = set(audit["copied_keys"])
        for filename in sorted(set(weight_map.values())):
            with safe_open(str(base / filename), framework="pt", device="cpu") as shard:
                for name in shard.keys():
                    if name in copied:
                        value = shard.get_tensor(name).to(dtype=target[name].dtype)
                        target[name].copy_(value)
                        if not torch.equal(target[name], value):
                            raise RuntimeError(f"Foundation copy verification failed: {name}")
    del target
    model.resize_token_embeddings(len(tokenizer))
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.bos_token_id = tokenizer.bos_token_id
    model.config.pad_token_id = tokenizer.pad_token_id
    from peft import LoraConfig, get_peft_model

    excluded = ("visual_model", "vision_tower", "mm_projector", "text_hidden_fcs",
                "mask_decoder", "image_feature_neck", "prompt_encoder")
    targets = sorted(name for name, module in model.named_modules()
                     if isinstance(module, torch.nn.Linear)
                     and not any(part in name for part in excluded)
                     and any(part in name for part in ("q_proj", "v_proj")))
    if len(targets) != 64:
        raise ValueError("Expected 64 language LoRA targets")
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=.05,
                                            target_modules=targets, bias="none", task_type="CAUSAL_LM"))
    trainable = ("mask_decoder", "text_hidden_fcs", "sam_to_embed_conv",
                 "prompt_encoder", "image_feature_neck", "lm_head", "embed_tokens", "mm_projector")
    for name, parameter in model.named_parameters():
        if any(part in name for part in trainable):
            parameter.requires_grad_(True)
    audit["trainable_alignment_keys"] = configure_alignment_training(model)
    audit["parameter_inventory"] = [
        {"name": name, "shape": list(p.shape), "dtype": str(p.dtype),
         "requires_grad": p.requires_grad, "numel": p.numel()}
        for name, p in model.named_parameters()]
    audit.update(seed=seed, tokenizer_size=len(tokenizer), language_lora_targets=targets,
                 device=device, published_checkpoint_used=False, training_run=False,
                 external_tower_value_acceptance_pending=True,
                 initialization_dtype="float32_then_bfloat16",
                 external_clip_model=config_data.get("mm_vision_tower"),
                 original_base_clip_model=json.loads((base / "config.json").read_text()).get("mm_vision_tower"))
    model = model.to(device).eval()
    return model, tokenizer, audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke-dataset", type=Path)
    parser.add_argument("--smoke-manifest", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    model, tokenizer, audit = load_rebuilt_model(
        args.source, args.deployment, args.base, args.seed, args.device)
    if bool(args.smoke_dataset) != bool(args.smoke_manifest):
        raise ValueError("Both smoke dataset and manifest are required")
    if args.smoke_dataset:
        audit["smoke_generation"] = smoke_generation(
            model, tokenizer, args.source, args.smoke_dataset, args.smoke_manifest)
    args.output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"copied_keys": len(audit["copied_keys"]),
                      "initialized_keys": len(audit["initialized_keys"]),
                      "alignment_parameters": len(audit["trainable_alignment_keys"]),
                      "tokenizer_size": len(tokenizer), "training_run": False}))
