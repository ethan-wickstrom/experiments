"""Unconstrained log probabilities for complete alternative replies including the assistant stop."""
import torch
from backbone import chat_ids, target_ids


@torch.inference_mode()
def sequence_logprobs(editor, prompt, answers):
    prefix = chat_ids(editor.tok, prompt)
    tails = [target_ids(editor.tok, answer) for answer in answers]
    sequences = [prefix + tail[:-1] for tail in tails]
    width = max(map(len, sequences))
    assert width <= editor.max_input
    ids = torch.tensor([s + [editor.tok.pad_token_id] * (width - len(s)) for s in sequences])
    mask = torch.tensor([[1] * len(s) + [0] * (width - len(s)) for s in sequences])
    base = editor.model.get_base_model() if hasattr(editor.model, "get_base_model") else editor.model
    hidden = base.model(input_ids=ids, attention_mask=mask, use_cache=False).last_hidden_state
    scores = []
    for i, tail in enumerate(tails):
        logits = base.lm_head(hidden[i, len(prefix) - 1:len(prefix) - 1 + len(tail)])
        scores.append(-torch.nn.functional.cross_entropy(logits, torch.tensor(tail), reduction="sum").item())
    return scores
