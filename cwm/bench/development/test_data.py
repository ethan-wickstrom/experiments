"""Reconstruct every learner-visible prefix from the independent raw collector tape."""
import gzip
import json
import unittest

from corpus import DATA, PROJECT_SHA, ORACLE_SHA, canonical, corpus, verified

POLICY = "Choose one TypeScript project action as compact JSON. Actions: read(path), write(path,text), test(), done(). Use the key op for the action name. Read before replacing a file. Run tests after changes."
FORECAST = "Predict the result of the candidate project action. Reply with one word: pass, fail or rejected."


class CorpusAudit(unittest.TestCase):
    def test_no_future_or_counterfactual_observation_in_prompts(self):
        records = list(map(json.loads, verified(DATA / "oracle.jsonl.gz", ORACLE_SHA).splitlines()))
        derived = []
        for event in records:
            kind = event["type"]
            if kind == "initial":
                files = event["files"].copy()
                history = []
            elif kind == "request":
                files.update(event["supplied"])
                history.append({"user":event["user"]})
            else:
                assert kind in ("action","candidate")
                prediction = kind == "candidate"
                action = event["candidate" if prediction else "action"]
                state = dict(files=sorted(files),history=history)
                if prediction:
                    state["candidate"] = action
                compact = lambda value: json.dumps(value,ensure_ascii=False,separators=(",",":"))
                target = event["label"] if prediction else compact(action)
                derived.append(dict(family=event["family"], task="forecast" if prediction else "policy",
                                    prompt=(FORECAST if prediction else POLICY)+"\n"+compact(state), target=target))
                if prediction:
                    if "oracle" in event:
                        self.assertEqual(target, "pass" if event["oracle"]["exit"] == 0 else "fail")
                    else:
                        self.assertEqual(target, "rejected")
                        self.assertIn(action["path"],files)
                        self.assertFalse(any(e.get("action") == {"op":"read","path":action["path"]} for e in history))
                elif action["op"] != "done":
                    result = event["observed"]
                    if action["op"] == "read":
                        self.assertEqual(files[action["path"]],result)
                    elif action["op"] == "write":
                        self.assertEqual(result,"written")
                        files[action["path"]] = action["text"]
                    else:
                        self.assertEqual(action["op"],"test")
                        self.assertEqual(result.split("\n")[0], "pass" if event["oracle"]["exit"] == 0 else "fail")
                    history.append({"action":action,"observed":result})
                else:
                    self.assertEqual(history[-1],{"action":{"op":"test"},"observed":"pass"})
        self.assertEqual(canonical(derived), verified(DATA / "projects.jsonl.gz",PROJECT_SHA))

    def test_combined_tape(self):
        self.assertEqual(canonical(corpus()), gzip.decompress((DATA / "training.jsonl.gz").read_bytes()))


if __name__ == "__main__":
    unittest.main()
