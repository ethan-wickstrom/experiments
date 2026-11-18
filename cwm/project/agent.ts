import { Effect } from "effect";
import { permittedActions, decodeAction, wire, type Action, type Event } from "./protocol.ts";
import { maxFileBytes, maxFiles, sourcePath } from "./workspace.ts";
import { runTests, testObservation, type ToolRun } from "./sandbox.ts";

export type Completion = { text: string; finish: string; tokens: number; inputTokens: number };
export type Generate = (
  prompt: string,
  limit: number,
  signal?: AbortSignal,
  grammar?: ReturnType<typeof permittedActions>["grammar"],
  verbatim?: boolean,
) => Promise<Completion>;
export function endpoint(url: string, model: string): Generate {
  return async (prompt, limit, signal, grammar, verbatim = false) => {
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
      text: verbatim ? choice.message.content : choice.message.content.trim(),
      finish: choice.finish_reason,
      tokens: data.usage.completion_tokens,
      inputTokens: data.usage.prompt_tokens,
    };
  };
}
export type Workspace = {
  files: Map<string, string>;
  refresh?: () => Promise<void>;
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
  private needsTest = false;
  private readonly read = new Map<string, string>();
  readonly project: Workspace;
  readonly generate: Generate;
  readonly test: (files: ReadonlyMap<string, string>, signal?: AbortSignal) => Promise<ToolRun>;
  constructor(
    project: Workspace,
    generate: Generate,
    test = (files: ReadonlyMap<string, string>, signal?: AbortSignal) =>
      Effect.runPromise(runTests(files), { signal }),
  ) {
    this.project = project;
    this.generate = generate;
    this.test = test;
  }
  state() {
    return { files: [...this.project.files.keys()].sort(), history: this.history.slice() };
  }
  get untestedChanges() {
    return this.needsTest;
  }
  get observedFiles(): ReadonlyMap<string, string> {
    return this.read;
  }
  async begin(goal: string) {
    if (!goal.trim()) throw Error("Expected a project request");
    await this.project.refresh?.();
    this.read.clear();
    this.tested = false;
    this.history.push({ user: goal });
  }

  async act(
    action: Exclude<Action, { op: "done" }>,
    signal?: AbortSignal,
    observeTest = testObservation,
  ) {
    let run: ToolRun | undefined;
    let observed: string;
    if (action.op === "test") {
      run = await this.test(this.project.files, signal);
      observed = observeTest(run);
      this.tested = true;
      this.needsTest = false;
    } else if (!sourcePath(action.path)) observed = "rejected";
    else if (action.op === "read") {
      const text = this.project.files.get(action.path);
      if (text !== undefined) this.read.set(action.path, text);
      observed = text ?? "rejected";
    } else if (
      !/\.(?:[cm]?ts|tsx)$/i.test(action.path) ||
      (this.project.files.has(action.path)
        ? !this.read.has(action.path)
        : this.project.files.size >= maxFiles) ||
      Buffer.byteLength(action.text) > maxFileBytes
    )
      observed = "rejected";
    else {
      await this.project.persist?.(action.path, action.text);
      if (this.project.files.get(action.path) !== action.text) {
        this.tested = false;
        this.needsTest = true;
      }
      this.project.files.set(action.path, action.text);
      this.read.set(action.path, action.text);
      observed = "written";
    }
    this.history.push({ action, observed });
    return { observed, run };
  }
  // A write candidate asks about applying the replacement followed by the project's tests.
  async predict(candidate: Action, signal?: AbortSignal) {
    if (candidate.op !== "write" && candidate.op !== "test")
      throw Error("Forecast a write followed by tests, or the current tests");
    const { files, history } = this.state();
    const reply = await this.generate(wire(files, history, candidate), 8, signal);
    return {
      ...reply,
      prediction:
        reply.finish === "stop" && ["pass", "fail", "rejected"].includes(reply.text)
          ? reply.text
          : null,
    };
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
    await this.begin(goal);
    const events: TurnEvent[] = [];
    for (let i = 0; i < steps; i++) {
      const { files, history } = this.state();
      const prompt = wire(files, history);
      const allowed = permittedActions(
        files.filter((p) => !this.read.has(p)),
        this.tested,
        this.needsTest,
      );
      const start = performance.now();
      const reply = await this.generate(prompt, limit, signal, allowed.grammar);
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
        if (!allowed.accepts(action)) throw Error("Unavailable action");
      } catch {
        onEvent?.(event);
        return { stop: "invalid" as const, events };
      }
      event.action = action;
      if (action.op === "done") {
        onEvent?.(event);
        return { stop: this.needsTest ? ("invalid" as const) : ("done" as const), events };
      }
      Object.assign(event, await this.act(action, signal));
      onEvent?.(event);
    }
    return { stop: "budget" as const, events };
  }
}
