"""CPU-only pinned runtime acceptance; never load published weights or data."""

import argparse
import importlib
import importlib.metadata
import json
from pathlib import Path


def check(requirements):
    versions = {}
    for line in Path(requirements).read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, expected = line.split("==")
        actual = importlib.metadata.version(name)
        if actual != expected:
            raise RuntimeError(f"{name}: expected {expected}, found {actual}")
        versions[name] = actual
    for name in ("torch", "torchvision", "transformers", "accelerate", "peft",
                 "deepspeed", "cv2", "pycocotools.mask", "sam2.build_sam"):
        importlib.import_module(name)
    import torch
    from transformers import LlamaConfig, LlamaForCausalLM

    torch.set_num_threads(1)
    torch.manual_seed(20261008)
    model = LlamaForCausalLM(LlamaConfig(
        vocab_size=32, hidden_size=16, intermediate_size=32,
        num_hidden_layers=2, num_attention_heads=2, bos_token_id=1,
        eos_token_id=None, pad_token_id=0)).eval()
    with torch.no_grad():
        output = model.generate(torch.tensor([[1, 3, 4, 5]]),
                                max_new_tokens=3, do_sample=False,
                                use_cache=True, output_hidden_states=True,
                                return_dict_in_generate=True)
    lengths = [step[-1].shape[1] for step in output.hidden_states]
    hidden = torch.cat([step[-1] for step in output.hidden_states], dim=1)
    if lengths != [4, 1, 1] or hidden.shape[:2] != (1, output.sequences.shape[1] - 1):
        raise RuntimeError("Unexpected actual cached generation alignment")
    return {"direct_versions": versions, "cpu_imports_passed": True,
            "sam2_version": importlib.metadata.version("SAM-2"),
            "cuda_available": torch.cuda.is_available(),
            "random_tiny_llama_cached_step_lengths": lengths,
            "published_weights_or_dataset_read": False,
            "published_model_alignment_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = check(args.requirements)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
