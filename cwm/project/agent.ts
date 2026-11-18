import { Effect } from "effect";
import { actionGrammar, decodeAction, wire, type Action, type Event } from "./protocol.ts";
import { maxFileBytes, maxFiles, sourcePath } from "./workspace.ts";
import { runTests, testObservation, type ToolRun } from "./sandbox.ts";

export type Completion = { text: string; finish: string; tokens: number; inputTokens: number };
export type Generate = (
  prompt: string,
  limit: number,
  signal?: AbortSignal,
  grammar?: ReturnType<typeof actionGrammar>,
) => Promise<Completion>;
export function endpoint(url: string, model: string): Generate {
  return async (prompt, limit, signal, grammar) => {
    const timeout = AbortSignal.timeout(180000);
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: prompt }],
        chat_template_kwargs: { enable_thinking: false },
        temperature: 0,
        max_tokens: limit,
        stream: false,
        ...(grammar ? { response_format: { type: "json_object", schema: grammar } } : {}),
      }),
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
    if (!response.ok)
      throw Error("Model HTTP " + response.status + ": " + (await response.text()).slice(0, 400));
    const data = (await response.json()) as {
      choices?: { message?: { content?: string }; finish_reason?: string }[];
      usage?: { completion_tokens: number; prompt_tokens: number };
    };
    const choice = data.choices?.[0];
    if (
      typeof choice?.message?.content !== "string" ||
      typeof choice.finish_reason !== "string" ||
      !data.usage
    )
      throw Error("Malformed model response");
    return {
      text: choice.message.content.trim(),
      finish: choice.finish_reason,
      tokens: data.usage.completion_tokens,
      inputTokens: data.usage.prompt_tokens,
    };
  };
}
export type Workspace = {
  files: Map<string, string>;
  persist?: (path: string, text: string) => Promise<void>;
};
export type TurnEvent = {
  request: string;
  reply: Completion;
  elapsedMs: number;
  action?: Action;
  observed?: string;
  run?: ToolRun;
};
export class ProjectSession {
  readonly history: Event[] = [];
  private tested = false;
  private readonly read = new Set<string>();
  readonly project: Workspace;
  readonly generate: Generate;
  constructor(project: Workspace, generate: Generate) {
    this.project = project;
    this.generate = generate;
  }
  state() {
    return { files: [...this.project.files.keys()].sort(), history: this.history.slice() };
  }

  // A write candidate asks about applying the replacement followed by the project's tests.
  predict(candidate: Action, signal?: AbortSignal) {
    const { files, history } = this.state();
    return this.generate(wire(files, history, candidate), 8, signal);
  }
  async turn(
    goal: string,
    {
      steps = 8,
      limit = 768,
      signal,
      onEvent,
    }: {
      steps?: number;
      limit?: number;
      signal?: AbortSignal;
      onEvent?: (event: TurnEvent) => void;
    } = {},
  ) {
    if (!goal.trim()) throw Error("Expected a project request");
    this.history.push({ user: goal });
    const events: TurnEvent[] = [];
    for (let i = 0; i < steps; i++) {
      const { files, history } = this.state();
      const prompt = wire(files, history);
      const grammar = actionGrammar(
        files.filter((p) => !this.read.has(p)),
        this.tested,
      );
      const start = performance.now();
      const reply = await this.generate(prompt, limit, signal, grammar);
      const event: TurnEvent = {
        request: prompt,
        reply,
        elapsedMs: Math.round(performance.now() - start),
      };
      events.push(event);
      if (reply.finish !== "stop") {
        onEvent?.(event);
        return { stop: "incomplete" as const, events };
      }
      let action: Action;
      try {
        action = decodeAction(reply.text);
      } catch {
        onEvent?.(event);
        return { stop: "invalid" as const, events };
      }
      event.action = action;
      if (action.op === "done") {
        onEvent?.(event);
        return { stop: "done" as const, events };
      }
      if (action.op === "test") {
        event.run = await Effect.runPromise(runTests(this.project.files), { signal });
        event.observed = testObservation(event.run);
        this.tested = true;
      } else if (!sourcePath(action.path)) event.observed = "rejected";
      else if (action.op === "read") {
        const text = this.project.files.get(action.path);
        if (text !== undefined) this.read.add(action.path);
        event.observed = text ?? "rejected";
      } else if (
        !/\.(?:[cm]?ts|tsx)$/i.test(action.path) ||
        (this.project.files.has(action.path)
          ? !this.read.has(action.path)
          : this.project.files.size >= maxFiles) ||
        Buffer.byteLength(action.text) > maxFileBytes
      )
        event.observed = "rejected";
      else {
        await this.project.persist?.(action.path, action.text);
        if (this.project.files.get(action.path) !== action.text) this.tested = false;
        this.project.files.set(action.path, action.text);
        this.read.add(action.path);
        event.observed = "written";
      }
      this.history.push({ action, observed: event.observed });
      onEvent?.(event);
    }
    return { stop: "budget" as const, events };
  }
}
