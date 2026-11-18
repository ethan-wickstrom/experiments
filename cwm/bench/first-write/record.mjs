// Preloaded only in the duplicate oracle process. Observe existing protocol traffic;
// do not evaluate expressions, request extra properties, or alter breakpoint placement.
import { appendFileSync } from "node:fs";
import { Session } from "node:inspector/promises";
import { isMainThread } from "node:worker_threads";

if (!isMainThread) {
  const post = Session.prototype.post;
  const write = (event) =>
    appendFileSync(process.env.CWM_PROTOCOL_LOG, JSON.stringify(event) + "\n");
  const scripts = new Set();
  let recording = false;
  Session.prototype.post = async function (method, params) {
    if (method === "Debugger.enable") {
      this.prependListener("Debugger.scriptParsed", ({ params }) => {
        if (!params.url.startsWith("repo:")) return;
        scripts.add(params.scriptId);
        write({ method: "Debugger.scriptParsed", params });
      });
      this.prependListener("Debugger.paused", ({ params }) => {
        recording = scripts.has(params.callFrames[0].location.scriptId);
        if (recording) write({ method: "Debugger.paused", params });
      });
    }
    if (method === "Debugger.resume") recording = false;
    const response = await post.call(this, method, params);
    if (recording && method === "Runtime.getProperties") write({ method, params, response });
    return response;
  };
}
