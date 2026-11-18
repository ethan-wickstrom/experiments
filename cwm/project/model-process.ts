import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

/** One serial NDJSON connection. A cancelled request discards the process and its unread output. */
export function modelProcess(command: string, args: string[]) {
  function connect() {
    const child = spawn(command, args, { stdio: ["pipe", "pipe", "inherit"] });
    const lines = createInterface({ input: child.stdout, crlfDelay: Infinity });
    let failure: Error | undefined;
    child.once("error", (error) => {
      failure = error;
    });
    child.stdin.on("error", (error) => {
      failure = error;
    });
    const closed = new Promise<void>((resolve) => child.once("close", () => resolve()));
    const replies = lines[Symbol.asyncIterator]();
    return { child, replies, closed, error: () => failure };
  }
  let live: ReturnType<typeof connect> | undefined;
  let queue = Promise.resolve();
  let closed = false;
  async function disconnect() {
    const connection = live;
    live = undefined;
    if (connection) {
      connection.child.kill("SIGKILL");
      await connection.closed;
    }
  }
  async function exchange(value: unknown, signal?: AbortSignal) {
    signal?.throwIfAborted();
    if (closed) throw Error("Model process closed");
    const line = JSON.stringify(value) + "\n";
    const connection = (live ??= connect());
    const deadline = AbortSignal.timeout(600000);
    const cancel = signal ? AbortSignal.any([signal, deadline]) : deadline;
    const abort = () => connection.child.kill("SIGKILL");
    cancel.addEventListener("abort", abort, { once: true });
    try {
      await new Promise<void>((resolve, reject) => {
        connection.child.stdin.write(line, (error) => (error ? reject(error) : resolve()));
      });
      const reply = await connection.replies.next();
      cancel.throwIfAborted();
      if (reply.done) throw connection.error() ?? Error("Model process ended before replying");
      return JSON.parse(reply.value) as unknown;
    } catch (error) {
      await disconnect();
      cancel.throwIfAborted();
      throw error;
    } finally {
      cancel.removeEventListener("abort", abort);
    }
  }
  return {
    request(this: void, value: unknown, signal?: AbortSignal) {
      const next = queue.then(() => exchange(value, signal));
      queue = next.then(
        () => {},
        () => {},
      );
      return next;
    },
    async close(this: void) {
      closed = true;
      await disconnect();
      await queue;
    },
  };
}

export function pythonModel(script: URL, arm: string) {
  return modelProcess(process.env.CWM_PYTHON ?? "python", [
    fileURLToPath(script),
    "--serve",
    "--arm",
    arm,
  ]);
}
