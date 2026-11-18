/** Raw completion after MiniCPM5's stock single-message, no-thinking template. */
export type BodyQuery = {
  user: string;
  prefill: string;
  limit: number;
  stop?: string[];
  grammar?: string;
};
export type BodyReply = {
  text: string;
  finish: string;
  inputTokens: number;
  tokens: number;
  rendered: string;
  ids: number[];
  generatedIds: number[];
  stoppingWord: string;
  truncated: boolean;
  timings: object;
};
export type BodyGenerate = (query: BodyQuery, signal?: AbortSignal) => Promise<BodyReply>;

const noThink = "<|im_start|>assistant\n<think>\n\n</think>\n\n";
const reserved = (id: number) => id < 22 || id >= 130072;

export function bodyEndpoint(base: string, model: string): BodyGenerate {
  return async ({ user, prefill, limit, stop, grammar }, signal) => {
    const timeout = AbortSignal.timeout(180000);
    const abort = signal ? AbortSignal.any([signal, timeout]) : timeout;
    async function post<T>(path: string, body: object): Promise<T> {
      const r = await fetch(new URL(path, base), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: abort,
      });
      if (!r.ok) throw Error(path + " HTTP " + r.status + ": " + (await r.text()).slice(0, 600));
      return (await r.json()) as T;
    }
    const { prompt } = await post<{ prompt: string }>("/apply-template", {
      messages: [{ role: "user", content: user }],
      chat_template_kwargs: { enable_thinking: false },
    });
    if (prompt !== "<s><|im_start|>user\n" + user + "<|im_end|>\n" + noThink)
      throw Error("Expected the stock MiniCPM5 no-thinking template");
    // Split at the final reserved token boundary. The ordinary-token suffix
    // retains BPE merges across the two template newlines and the source prefill.
    const tokenize = async (content: string, special: boolean) =>
      (
        await post<{ tokens: number[] }>("/tokenize", {
          content,
          add_special: false,
          parse_special: special,
        })
      ).tokens;
    const templateIds = await tokenize(prompt.slice(0, -2), true);
    const suffixIds = await tokenize("\n\n" + prefill, false);
    if (
      templateIds.filter(reserved).join() !== "0,130072,130073,130072,8,9" ||
      suffixIds.some(reserved)
    )
      throw Error("Unreserved template delimiter in project data");
    const ids = [...templateIds, ...suffixIds];
    if (ids.length + limit > 4096) throw Error("Body edit exceeds 4096-token context budget");
    const result = await post<{
      model: string;
      content: string;
      stop_type: string;
      tokens: number[];
      tokens_evaluated: number;
      tokens_predicted: number;
      truncated: boolean;
      stopping_word: string;
      timings: object;
    }>("/completion", {
      prompt: ids,
      n_predict: limit,
      temperature: 0,
      seed: 17,
      return_tokens: true,
      cache_prompt: false,
      stop,
      grammar,
    });
    if (
      result.model !== model ||
      result.tokens_evaluated !== ids.length ||
      typeof result.content !== "string" ||
      !Array.isArray(result.tokens)
    )
      throw Error("Unexpected raw completion model, prompt count or response");
    const unsafe = result.tokens.some(
      (id, i) =>
        reserved(id) &&
        !(
          result.stop_type === "eos" &&
          i === result.tokens.length - 1 &&
          (id === 1 || id === 130073)
        ),
    );
    return {
      text: result.content,
      finish: unsafe ? "reserved" : result.stop_type,
      inputTokens: ids.length,
      tokens: result.tokens_predicted,
      rendered: prompt + prefill,
      ids,
      generatedIds: result.tokens,
      stoppingWord: result.stopping_word,
      truncated: result.truncated,
      timings: result.timings,
    };
  };
}
