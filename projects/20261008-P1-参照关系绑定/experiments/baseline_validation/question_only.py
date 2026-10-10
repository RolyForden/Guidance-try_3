"""Question-only input adapter, not a training or evaluation launcher."""

import json
from pathlib import Path
import re


_RESERVED = re.compile(r"\[SEG\d*\]|</?(?:think|answer)>|<image>|<im_start>|<im_end>")


def build_question_prompt(question, conversation, *, use_mm_start_end=True):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("A nonempty original question is required")
    if _RESERVED.search(question):
        raise ValueError("The original question contains reserved conditioning tokens")
    conv = conversation.copy()
    conv.messages = []
    image = "<im_start><image><im_end>" if use_mm_start_end else "<image>"
    conv.append_message(conv.roles[0], image + "\n" + question)
    conv.append_message(conv.roles[1], None)
    return conv.get_prompt()


def local_model_config(deployment_root):
    """Pass this dict to LlavaConfig.from_dict before loading; do not save over upstream."""
    root = Path(deployment_root).resolve(strict=True)
    clip = root / "models/clip-vit-large-patch14"
    for name in ("config.json", "preprocessor_config.json", "model.safetensors"):
        if not (clip / name).is_file():
            raise FileNotFoundError(clip / name)
    config = json.loads((root / "pretrained/pixdlm-7b/config.json").read_text(encoding="utf-8"))
    if config.get("model_type") != "llava":
        raise ValueError("Expected the fixed PixDLM llava configuration")
    config["vision_tower"] = str(clip)
    config["mm_vision_tower"] = str(clip)
    return config


def prepare_question_inputs(question, tokenizer, conversation, language_backbone, *,
                            tokenize_image, device, use_mm_start_end=True):
    """Use model.get_model() and the fixed source's tokenizer_image_token.

    RGB tensors and geometry stay separate; this API cannot accept annotations.
    Set PIXDLM_ROOT to the deployment root before constructing the actual model.
    """
    import torch

    prompt = build_question_prompt(question, conversation, use_mm_start_end=use_mm_start_end)
    if language_backbone.training:
        raise ValueError("The language backbone must be in eval mode")
    tokens = tokenizer(question, return_tensors="pt")
    question_ids = tokens.input_ids.to(device)
    attention_mask = tokens.attention_mask.to(device)
    input_ids = tokenize_image(prompt, tokenizer, image_token_index=-200,
                               return_tensors="pt").unsqueeze(0).to(device)
    with torch.no_grad():
        output = language_backbone(input_ids=question_ids, attention_mask=attention_mask,
                                   output_hidden_states=True, return_dict=True, use_cache=False)
        features = output.hidden_states[-1][:, attention_mask[0].bool(), :]
    if features.ndim != 3 or features.shape[0] != 1 or not torch.isfinite(features).all():
        raise ValueError("Invalid question-only text features")
    return {"input_ids": input_ids, "txt_feat": features}


def prepare_model_inputs(question, tokenizer, conversation, model, *, images, images_clip,
                         resize_list, clip_resize_list, original_size_list, tokenize_image,
                         max_new_tokens=32):
    """Whitelist one prepared RGB sample for model.evaluate; never accept a collated GT dict."""
    if model.training:
        raise ValueError("The model must be in eval mode")
    for image in (images, images_clip):
        if image.ndim != 4 or image.shape[0] != 1 or image.shape[1] != 3:
            raise ValueError("Expected a single prepared RGB tensor [1, 3, H, W]")
    if images.device != images_clip.device:
        raise ValueError("RGB tensors must be on the same device")
    if any(len(sizes) != 1 for sizes in (resize_list, clip_resize_list, original_size_list)):
        raise ValueError("Expected geometry for exactly one RGB sample")
    inputs = prepare_question_inputs(
        question, tokenizer, conversation, model.get_model(), tokenize_image=tokenize_image,
        device=images_clip.device, use_mm_start_end=model.config.mm_use_im_start_end)
    inputs.update(images=images, images_clip=images_clip, resize_list=resize_list,
                  clip_resize_list=clip_resize_list, original_size_list=original_size_list,
                  max_new_tokens=max_new_tokens, tokenizer=tokenizer)
    return inputs
