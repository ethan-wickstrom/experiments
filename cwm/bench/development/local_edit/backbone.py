"""Replay the trainable top decoder blocks from exact frozen prefix activations."""
import sys
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model

HERE = Path(__file__).resolve().parent
C2 = HERE.parent / "c2"
sys.path.insert(0, str(C2))
from data import corpus
from model import REVISION, MODEL_ID, chat_ids, load, target_ids


def adapt(base, count):
    start = len(base.model.layers) - count
    modules = [f"model.layers.{i}.{module}" for i in range(start, start + count) for module in
               ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj", "mlp.down_proj")]
    config = LoraConfig(task_type="CAUSAL_LM", r=32, lora_alpha=32, lora_dropout=0.0,
                        target_modules=modules, bias="none")
    return get_peft_model(base, config)


def top_logits(base, hidden, positions, count):
    n = hidden.shape[0]
    x = hidden[None]
    ids = torch.arange(n)[None]
    rotary = base.model.rotary_emb(x, ids)
    mask = torch.full((n, n), torch.finfo(x.dtype).min).triu(1)[None, None]
    for block in base.model.layers[-count:]:
        x = block(x, attention_mask=mask, position_ids=ids, position_embeddings=rotary, use_cache=False)
    return base.lm_head(base.model.norm(x[0, positions]))
