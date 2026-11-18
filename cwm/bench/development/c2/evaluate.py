"""Score local predeclared projects and debugger probes after weight freeze."""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

import torch

from data import ROOT, corpus, verified
from inference import generate, load_arm
from model import examples, frame_row, prompt, valid_row
from score import grade, token_loss


def rows(name):
    pins=json.loads((ROOT/"probe-pins.json").read_text())
    data=verified(ROOT/"probes"/(name+".jsonl.gz"),pins[name])
    return [json.loads(line) for line in data.splitlines()]


def run_tests(state, text, extra=None):
    # Only the ephemeral probe files enter the isolated interpreter. Mount read-only,
    # drop all capabilities, disable network and impose time, PID, CPU and memory limits.
    container="cwm-edit-"+uuid.uuid4().hex
    with tempfile.TemporaryDirectory() as root:
        os.chmod(root,0o755)
        for f in state["files"]:
            path=Path(f["path"])
            assert path == Path(path.name)
            (Path(root)/path).write_text(text if f["path"]==state["path"] else f["text"])
        if extra is not None:
            (Path(root)/"accept.test.ts").write_text(extra)
        cmd=["docker","run","--rm","--name",container,"--network","none","--read-only","--cap-drop","ALL",
             "--security-opt","no-new-privileges","--pids-limit","48","--memory","256m","--cpus","1",
             "--user","65534:65534","--log-driver","none","-w","/work","-v",root+":/work:ro",
             "cwm-c2-bun:1.4.4","/bin/bun","test","accept.test.ts" if extra else "checks.test.ts"]
        try:
            with tempfile.TemporaryFile() as log:
                result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=8)
                log.seek(0)
                output=log.read(4096).decode(errors="replace")
            if result.returncode not in (0,1):
                raise RuntimeError("Container execution error: "+output)
            # Require Bun's passing test count as well as the successful exit.
            return dict(passed=result.returncode==0 and "1 pass" in output and "0 fail" in output,
                        exit=result.returncode,log=output)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker","rm","-f",container],capture_output=True)
            return dict(passed=False,timeout=True)


def project_score(model,tok):
    projects=rows("projects")
    oracle=rows("oracle")
    checks=json.loads((ROOT/"extra-checks.json").read_text())
    key_to_test={}
    for ep in oracle:
        spec=checks[ep["family"]]
        fn={"catalog":"titles","ticket":"ticket"}[ep["family"]]
        expected=spec["expected"][ep["turn"]*2+ep["fork"]]
        extra=('import {test,expect} from "bun:test";\n'+f'import {{{fn}}} from "./{ep["family"]}";\n'
               +f'test("additional input",()=>expect({fn}({spec["call"]})).toEqual({json.dumps(expected)}));')
        assert run_tests(ep,ep["after"]["text"],extra)["passed"]
        key_to_test[ep["goal"]]=extra
    train_families={r["family"] for r in corpus()}
    assert all(r["family"] not in train_families for r in projects)
    predictions=[]
    for task,budget in [("source",128),("decision",8),("forecast",8)]:
        part=[r for r in projects if r["task"]==task]
        for start in range(0,len(part),4):
            batch=part[start:start+4]
            answers=generate(model,tok,[r["prompt"] for r in batch],budget,task=="forecast")
            for row,answer in zip(batch,answers,strict=True):
                state=json.loads(row["prompt"].split("\n",1)[1])
                item={**row,**answer,"exact":answer["stopped"] and answer["text"]==row["target"]}
                if task=="source" and answer["stopped"]:
                    item["tests"]=run_tests(state,answer["text"])
                    item["acceptance"]=run_tests(state,answer["text"],key_to_test[state["goal"]])
                predictions.append(item)
    totals={}
    for task in ("source","decision","forecast"):
        items=[p for p in predictions if p["task"]==task]
        totals[task]={"rows":len(items),"stops":sum(p["stopped"] for p in items),"exact":sum(p["exact"] for p in items)}
    totals["source"]["bun_pass"]=sum(p.get("tests",{}).get("passed",False) for p in predictions)
    totals["source"]["both_pass"]=sum(p.get("tests",{}).get("passed",False) and
                                      p.get("acceptance",{}).get("passed",False) for p in predictions)
    groups={}
    for p in predictions:
        if p["task"]=="forecast" and p["target"] in ("pass","fail"):
            s=json.loads(p["prompt"].split("\n",1)[1])
            key=json.dumps(s["history"],sort_keys=True)
            group=groups.setdefault(key,{})
            assert p["target"] not in group
            group[p["target"]]=p["pass_minus_fail_logit"]
    assert all(set(g)=={"pass","fail"} for g in groups.values())
    totals["pairs"]={"rows":len(groups),"correct":sum(g["pass"]>g["fail"] for g in groups.values()),
                     "ties":sum(g["pass"]==g["fail"] for g in groups.values())}
    return {"metrics":totals,"predictions":predictions}


def pause_score(model,base,tok):
    pins=json.loads((ROOT/"probe-pins.json").read_text())
    path=ROOT/"probes/pauses.jsonl.gz"
    data=examples(path,expected_sha=pins["pauses"])
    train={r["prompt"].split("\nCurrent:")[0] for r in corpus() if r["task"]=="execution"}
    assert all(prompt(s,c).split("\nCurrent:")[0] not in train for s,c,_ in data)
    totals=Counter()
    outputs=[]
    nll=tokens=0
    for start in range(0,len(data),6):
        batch=data[start:start+6]
        loss,n=token_loss(base,tok,batch)
        nll+=loss
        tokens+=n
        answers=generate(model,tok,[prompt(s,c) for s,c,_ in batch],32)
        for (s,c,g),a in zip(batch,answers,strict=True):
            t=a["text"] if a["stopped"] else ""
            totals.update(grade(c,g,t))
            outputs.append({"current":c,"gold":g,**a})
    runs=[]
    for t in rows("pauses"):
        obs=[frame_row(f,t["entry"],t["fn"]) for f in t["frames"][1:]]
        runs.append(dict(source=t["files"][t["entry"]],entry=obs[0],gold=obs[1:],predicted=[],stop=""))
    for _ in range(16):
        live=[r for r in runs if not r["stop"]]
        if not live:
            break
        users=[prompt(r["source"],(r["predicted"] or [r["entry"]])[-1]) for r in live]
        for r,a in zip(live,generate(model,tok,users,32),strict=True):
            out=a["text"]
            if not a["stopped"] or not valid_row(out):
                r["stop"]="invalid or capped"
            elif out.startswith("R,"):
                r["stop"]="predicted return"
            elif out==r["entry"] or out in r["predicted"]:
                r["stop"]="repetition"
            r["predicted"].append(out)
    return dict(metrics=dict(totals),target_tokens=tokens,nll=nll/tokens,outputs=outputs,
                exact_rollouts=sum(r["gold"]==r["predicted"] and r["stop"]=="predicted return" for r in runs),rollouts=runs)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("arm",choices=["A","B2","C2"])
    args=p.parse_args()
    assert run_tests({"path":"m.ts","files":[{"path":"m.ts","text":""},{"path":"checks.test.ts","text":
        'import {test,expect} from "bun:test";import {v} from "./m";test("value",()=>expect(v).toBe(2));'}]},
        "export const v = 2;")["passed"]
    model,base,tok=load_arm(args.arm)
    with torch.inference_mode():
        score={"arm":args.arm,"project":project_score(model,tok),"execution":pause_score(model,base,tok)}
    print(json.dumps(score,separators=(",",":"),ensure_ascii=False))
