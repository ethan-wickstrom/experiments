"""Against a running llama-server on loopback, check the actual prompt and raw edit response."""
import argparse
import gzip
import hashlib
import json
import os
from urllib.request import Request, urlopen

from transformers import AutoTokenizer

from package_model import ROOT, verify
from model import chat_ids
from provenance import verified_base


def check(port,arm):
    verify(arm)
    base="http://127.0.0.1:"+str(port)
    def request(path,obj=None):
        data=None if obj is None else json.dumps(obj).encode()
        with urlopen(Request(base+path,data=data,headers={"Content-Type":"application/json"}),timeout=120) as r:
            return json.load(r)
    adapters=request("/lora-adapters")
    assert len(adapters)==1 and adapters[0]["scale"]==1 and adapters[0]["path"].endswith(arm+"/adapter-f32.gguf")
    first=json.loads(gzip.open(ROOT/"data/projects.jsonl.gz","rt").readline())
    user=first["prompt"]
    messages=[{"role":"user","content":user}]
    config={"messages":messages,"chat_template_kwargs":{"enable_thinking":False}}
    formatted=request("/apply-template",config)["prompt"]
    ids=request("/tokenize",{"content":formatted,"add_special":False,"parse_special":True})["tokens"]
    with verified_base(os.environ["CWM_MODEL_PATH"]) as snapshot:
        tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True)
        expected=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
        if expected!=formatted or ids!=chat_ids(tok,user):
            raise ValueError("Server differs from training template: "+repr((expected[-90:],formatted[-90:],len(ids),len(chat_ids(tok,user)))))
    reply=request("/v1/chat/completions",dict(**config,max_tokens=128,temperature=0,seed=17))
    choice,=reply["choices"]
    assert reply["usage"]["prompt_tokens"]==len(ids)
    return dict(arm=arm,adapter=adapters[0]["path"],scale=adapters[0]["scale"],tokens=len(ids),
                template_sha256=hashlib.sha256(formatted.encode()).hexdigest(),
                output=choice["message"]["content"],finish_reason=choice["finish_reason"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("arm",choices=["B2","C2"])
    p.add_argument("port",type=int)
    args=p.parse_args()
    print(json.dumps(check(args.port,args.arm),ensure_ascii=False))
