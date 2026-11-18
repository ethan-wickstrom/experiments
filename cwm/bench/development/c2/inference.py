"""Stock chat greedy FP32 generation retaining raw whitespace, cap and both EOS IDs."""
import argparse
import json
import sys

import torch
from transformers import GenerationConfig

from package_model import ROOT, verify
from model import adapted, chat_ids, load


def load_arm(arm):
    if arm != "A":
        verify(arm)
    base, tok = load()
    model = base if arm == "A" else adapted(base,ROOT / arm / "peft")
    return model, base, tok


def decode(tok, continuation):
    stops={tok.eos_token_id,tok.convert_tokens_to_ids("<|im_end|>")}
    at=next((i for i,id_ in enumerate(continuation) if id_ in stops),len(continuation))
    return {"text":tok.decode(continuation[:at],skip_special_tokens=False),
            "stopped":at<len(continuation), "tokens":at}


@torch.inference_mode()
def generate(model,tok,users,limit,forecast=False):
    ids=[chat_ids(tok,u) for u in users]
    width=max(map(len,ids))
    inputs=torch.tensor([[tok.pad_token_id]*(width-len(x))+x for x in ids])
    mask=torch.tensor([[0]*(width-len(x))+[1]*len(x) for x in ids])
    cfg=GenerationConfig(do_sample=False,use_cache=True,max_new_tokens=limit,pad_token_id=tok.pad_token_id,
                         eos_token_id=[tok.eos_token_id,tok.convert_tokens_to_ids("<|im_end|>")])
    out=model.generate(input_ids=inputs,attention_mask=mask,generation_config=cfg,
                       return_dict_in_generate=True,output_scores=forecast)
    answers=[decode(tok,row[width:].tolist()) for row in out.sequences]
    if forecast:
        ids=[tok.encode(s,add_special_tokens=False) for s in ["pass","fail"]]
        assert all(len(x)==1 for x in ids)
        for answer,logits in zip(answers,out.scores[0],strict=True):
            answer["pass_minus_fail_logit"]=float(logits[ids[0][0]]-logits[ids[1][0]])
    return answers


if __name__ == "__main__":
    p=argparse.ArgumentParser(description="One user-message wire payload from stdin; emits raw text on a confirmed stop.")
    p.add_argument("arm",choices=["A","B2","C2"])
    p.add_argument("--budget",type=int,default=384)
    args=p.parse_args()
    model,_,tok=load_arm(args.arm)
    answer,=generate(model,tok,[sys.stdin.read()],args.budget)
    if not answer["stopped"]:
        sys.exit("Token cap reached before stop")
    sys.stdout.write(answer["text"])
